import os
import re
import time
import sys
import json
import pickle
import ast

SMALI_METHOD_START = '.method'
SMALI_METHOD_END = '.end method'
SMALI_CLASS = '.class'
ROOT_PATH = "/home/huseyinalecakir"
MAX_DEPTH_LIMIT = 50
MAX_VISITED_LIMIT = 10
CALL_GRAP_OUT_PATH = "/data/huseyinalecakir_data/CallGraphOutputs"

class Node:
    def __init__(self, parent, path, method_name, class_name):
        self.path = path
        self.class_name = class_name
        self.method_name = method_name
        self.childs = []
        self.cp_permissions = set()
        self.api_permissions = set()
        self.intent_permissions = set()
        self.depth = 0
        self.visited = {}
        self.parent = parent
        self.detected_lib = None
        self.is_third_party = False

    def add_child(self, node):
        self.childs.append(node)
    
    def add_cp_permission(self, perm):
        self.cp_permissions.add(perm)
    
    def add_api_permission(self, perm):
        self.api_permissions.add(perm)

    def add_intent_permission(self, perm):
        self.intent_permissions.add(perm)

    def set_depth(self, depth):
        self.depth = depth

    def get_depth(self):
        return self.depth

class ManifestNotExistError(Exception):
    pass

class ThirdPartyAnalyzer:
    def __init__(self, path, module, api_mapping, intent_mapping, detected_libs):
        self.path = path
        self.module = module
        self.custom_path = os.path.join(path, "smali", module)
        self.api_mapping = api_mapping
        self.intent_mapping = intent_mapping
        self.signature_cache = {}
        self.detected_3party_libs = detected_libs
        
    def extract_permission_by_contentp(self, method):
        """Extract permissions which are requested by Content Providers"""
        def is_exist(keyword, lst):
            for line in lst:
                if keyword.lower() in line.lower():
                    return True
            return False
        permission_methods = []
        exist_cr = is_exist("ContentResolver", method)
        exist_q = is_exist("query", method)
        exist_c = is_exist("contact", method)
        if exist_cr and exist_q and exist_c:
            permission_methods.append("READ_CONTACTS")
        return permission_methods

    def extract_permission_by_apicall(self, method):
        """Extract permissions which are requested by API Calls"""
        perm_methods = []
        def match_api_call(line):
            for api in self.api_mapping:
                if api.lower()  in line.lower():
                    return self.api_mapping[api]
            return None
        for line in method[1:-1]:
            requested_perm= match_api_call(line) 
            if requested_perm:
                perm_methods.extend(requested_perm)
        return perm_methods

    def extract_permission_by_intent(self, method):
        """Extract permissions which are requested by Intents"""
        perm_methods = []
        def match_intent(line):
            for action in self.intent_mapping:
                for token in line.split():
                    if action.lower()  == token:
                        return self.intent_mapping[action]
            return None
        for line in method[1:-1]:
            requested_perm= match_intent(line) 
            if requested_perm:
                perm_methods.append(requested_perm)
        return perm_methods

    def inspect_class(self, fcontent):
        for line in fcontent:
            if line.startswith(SMALI_CLASS):
                parts = line.strip().split()
                return line

    def inspect_methods(self, fcontent):
        """Get all class methods"""
        methods = []
        method = []
        inside_method = False

        for i in range(len(fcontent)):
            if inside_method:
                if fcontent[i].strip():
                    method.append(fcontent[i].strip())
                    if fcontent[i].startswith(SMALI_METHOD_END):
                        methods.append(method)
                        method = []
                        inside_method = False
            else:
                if fcontent[i].startswith(SMALI_METHOD_START):
                    if fcontent[i].strip():
                        method.append(fcontent[i].strip())
                        inside_method = True
        return methods

    def get_called_method(self, fcontent, called_method):
        class_methods = self.inspect_methods(fcontent)
        for method in class_methods:
            method_name = method[0].split(" ")[-1].strip()
            if method_name == called_method:
                return method

    def check_requested_permissions(self, node, method):
        perm_cp = self.extract_permission_by_contentp(method)
        perm_api = self.extract_permission_by_apicall(method)
        perm_intent = self.extract_permission_by_intent(method)
        for p in perm_api:
            node.add_api_permission(p)
        for p in perm_cp:
            node.add_cp_permission(p)
        for p in perm_intent:
            node.add_intent_permissions(p)
    
    def match_with_detected_libs(self, node):
        class_name = node.class_name.strip().split()[-1]
        for lib in self.detected_3party_libs:
            if lib["package"] and lib["package"] in class_name: 
                node.detected_lib = lib
                return
    
    def check_is_thirdparty(self, node):
        class_name = node.class_name.strip().split()[-1]
        if self.module not in class_name:
            node.is_third_party = True
        
    def visit_method(self, node, method):
        #print("Visit method", node.path, node.depth)
        signature = node.class_name + "_" + node.method_name
        if signature not in node.visited:
            node.visited[signature] = 0
        node.visited[signature] += 1
        
        #Add requested permissions
        self.check_requested_permissions(node, method)

        if node.visited[signature] < MAX_VISITED_LIMIT and node.depth < MAX_DEPTH_LIMIT:
            if signature in self.signature_cache: #if method had already traversed.
                node = self.signature_cache[signature]
            else:
                #Check invoke statements
                for line in method[1:-1]:
                    code = line.split()
                    op = code[0].strip()
                    rest = code[-1].strip()
                    if op.startswith("invoke"):
                        if ";->" in rest:
                            _class = rest.split(";->")[0].split("/")[-1]
                            module = "/".join(rest.split(";->")[0].split("/")[:-1])
                            called_method = rest.split(";->")[1].strip()
                            smali_path =  os.path.join(self.path, "smali" , module[1:],  "{}.smali".format(_class))
                            if os.path.exists(smali_path):
                                f = open(smali_path, 'r')
                                fcontent = f.readlines()
                                f.close()
                                called_method_content = self.get_called_method(fcontent, called_method)
                                class_name = self.inspect_class(fcontent)
                                if called_method_content:
                                    child_node = Node(node, smali_path, called_method_content[0], class_name)
                                    self.match_with_detected_libs(child_node)
                                    self.check_is_thirdparty(child_node)
                                    node.add_child(child_node)
                                    child_node.set_depth(node.get_depth() + 1)
                                    child_node.visited = {key: node.visited[key] for key in node.visited}
                                    self.visit_method(child_node, called_method_content)
                self.signature_cache[signature] = node

    def get_calls(self, path, methods, class_name):
        nodes = []
        for method in methods:
            #print("Custom method", method[0])
            node = Node(None, path, method[0], class_name)
            node.set_depth(0)
            self.visit_method(node, method)
            nodes.append(node)
        return nodes

    def traverse_all_files(self):
        """Traverse all smali files"""
        all_nodes = []
        for root, dirs, files in os.walk(self.custom_path):
            for file in files:
                fname = os.path.join(root, file)
                if not fname.endswith('.smali'):
                    continue
                #print(fname)
                f = open(fname, 'r')
                fcontent = f.readlines()
                f.close()
                class_methods = self.inspect_methods(fcontent)
                class_name = self.inspect_class(fcontent)
                nodes = self.get_calls(fname, class_methods, class_name)
                all_nodes.extend(nodes)
        return all_nodes

def pscout_perm_api_map(path):
    mapping = {}
    with open(path) as target:
        for line in target:
            intent = line.split(" ")[0].strip()

            perm = line.split(" ")[1].strip()
            mapping[intent] = perm
    return mapping

def get_all_pscout_intent_mappings():
    path = os.path.join(ROOT_PATH, "NLG/datasets/PScout/jellybean_intentpermissions.txt")
    mapping = pscout_perm_api_map(path)
    return mapping

def axplorer_perm_api_map(path):
    mapping = {}

    with open(path) as target:
        for line in target:
            api_call = line.split("::")[0].strip()
            matchObj = re.match( r"^([a-zA-Z].*)\.(.*)\((.*)\)(.*)$", api_call, re.M|re.I)
            module = matchObj.group(1)
            fname = matchObj.group(2)
            args = matchObj.group(3)
            retval = matchObj.group(4)
            api_call = "L{};->{}".format(module.replace(".", "/"), fname)
            """
            for arg in args.split(","):
                arg = arg.strip()
                if arg.replace(".", "/"):
                    api_call += arg.replace(".", "/") + ";"
            api_call += "){}".format(retval.replace(".", "/"))
            """
            perms = line.split("::")[1].strip().split(",")
            mapping[api_call] = []
            for p in perms: 
                mapping[api_call].append(p.strip())
    return mapping

def get_all_axplorer_api_mappings():
    axplorer_map = {}
    for i in range(16, 26):
        path = os.path.join(ROOT_PATH, "NLG/datasets/axplorer/permissions/api-{}/sdk-map-{}.txt".format(i,i))
        if os.path.exists(path):
            mapping = axplorer_perm_api_map(path)
            for k in mapping:
                if k not in axplorer_map:
                    axplorer_map[k] = []
                for e in mapping[k]:
                    if e not in axplorer_map[k]:
                        axplorer_map[k].append(e)
    return axplorer_map

def get_custom_code(path):
    print(path)
    custom_path = os.path.join(path, "AndroidManifest.xml")
    com = ""
    module = ""
    if not os.path.exists(custom_path):
        raise ManifestNotExistError()

    with open(custom_path) as target:
        for line in target:
            #if "<?xml" in line:
            matchObj = re.match(r'.*package="([_a-zA-Z\.0-9]*)"', line, re.M|re.I)
            if matchObj:
                custom_code = matchObj.group(1)
                parts = custom_code.split(".")
                com = parts[0]
                module = parts[1]
                break 
    return os.path.join(com, module)

def get_call_chain(node):
    if node.parent:
        return get_call_chain(node.parent) + [node]
    else:
        return []

def dfs(node, chains):
    #if node.cp_permissions:
    chain = get_call_chain(node)
    if chain:
        chains["cp"].append(chain)
    #if node.api_permissions:
    chain = get_call_chain(node)
    if chain:
        chains["api"].append(chain)
    #if node.intent_permissions:
    chain = get_call_chain(node)
    if chain:
        chains["intent"].append(chain)
    for child in node.childs:
        dfs(child, chains)

def permission_statistics(chains):
    permissions = {}
    for key in chains:
        for list_of_chain in chains[key]:
            for node in list_of_chain:
                for p in node.cp_permissions:
                    if p not in permissions:
                        permissions[p] = 0
                    permissions[p] += 1
                for p in node.api_permissions:
                    if p not in permissions:
                        permissions[p] = 0
                    permissions[p] += 1
    return permissions
            
def write_to_file(err, permission):
    with open("ERRORS_{}.log".format(permission), "a") as target:
        target.write(err + "\n")
    
def read_detection_libraries_libID(file_name):
    with open(file_name) as json_file:
        data = json.load(json_file)
        k = full_path.split("/")[-1].replace(".json", "")
        return data["libraries"]

def read_detection_libraries_libRadar(file_name):
    with open(file_name) as json_file:
        data = json.load(json_file)
        libraries = []
        for lib in data:
            l = {}
            l["name"] = lib["Library"]
            l["package"] = lib["Package"]
            libraries.append(l)
        return libraries


## Load API and Intent Mapping
pscout_intent_map = get_all_pscout_intent_mappings()
axplorer_map = get_all_axplorer_api_mappings()

app_permissions = {}
app_chains = {}
app_nodes = {}
app_analyzers = {}

"""app_name = item[b"app_name"].decode("utf-8") 
dev_sha = item[b"dev_sha"].decode("utf-8") 
app_sha = item[b"app_sha"].decode("utf-8") 
literadar = item[b"literadar"].decode("utf-8") 
smali = item[b"smali"].decode("utf-8") 
apk_path = item[b"apk_path"].decode("utf-8")""" 

apk_path = "/home/huseyinalecakir/app-debug.apk"
smali = "/home/huseyinalecakir/app-debug"
literadar = "/home/huseyinalecakir/app-debug.libradar"
try:
    print("Analyzed APK ", apk_path) 
    module = get_custom_code(smali)
    detection_file = read_detection_libraries_libRadar(literadar)
    thirdparty_analyzer = ThirdPartyAnalyzer(smali, module, axplorer_map, pscout_intent_map, detection_file)
    head_nodes = thirdparty_analyzer.traverse_all_files()
    chains = {"api":[], "cp":[], "intent":[]}
    for n in head_nodes:
        dfs(n, chains)
    app_chains[smali] = chains
    app_nodes[smali] = head_nodes
    app_permissions[smali] = permission_statistics(chains)
    app_analyzers[smali] = thirdparty_analyzer
except ManifestNotExistError: 
    write_to_file("ManifestNotExistError:  {}".format(apk_path))

"""with open(os.path.join(CALL_GRAP_OUT_PATH, "{}.pkl".format(smali.replace("/", "##"))), "wb") as f:
    pickle.dump([item, app_chains, app_nodes, app_permissions, app_analyzers], f)  
"""
