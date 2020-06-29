import os
import re

SMALI_METHOD_START = '.method'
SMALI_METHOD_END = '.end method'
SMALI_CLASS = '.class'
PATH = "/home/huseyinalecakir"

def inspect_methods(fcontent):
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

def pscout_perm_api_map(path):
    mapping = {}
    with open(path) as target:
        for line in target:
            intent = line.split(" ")[0].strip()

            perm = line.split(" ")[1].strip()
            mapping[intent] = perm
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

class ContentProvider:
    def find_in_class(methods):
        """Find methods that invoke content providers."""
        def is_exist(keyword, lst):
            for line in lst:
                if keyword.lower() in line.lower():
                    return True
            return False
        permission_methods = []
        for method in methods:
            exist_cr = is_exist("ContentResolver", method)
            exist_q = is_exist("query", method)
            exist_c = is_exist("contact", method)
            #if exist_cr:
            #    print(exist_cr , exist_q , exist_c)
            if exist_cr and exist_q and exist_c:
                permission_methods.append(method[0])
        return permission_methods

    def find_in_path(path):
        """Traverse all smali files"""
        for root, dirs, files in os.walk(path):
            for file in files:
                fname = os.path.join(root, file)
                if not fname.endswith('.smali'):
                    continue
                f = open(fname, 'r')
                fcontent = f.readlines()
                #print(fname, end=" ")
                class_methods = inspect_methods(fcontent)
                permission_methods = ContentProvider.find_in_class(class_methods)
                f.close()
                if permission_methods:
                    print(fname, permission_methods)

class APICall:
    def find_in_class(methods, mapping):
        """Find methods that invoke content providers."""
        perm_methods = {}
        def match_api_call(line):
            for api in mapping:
                if api in line:
                    return mapping[api]
            return None
        for method in methods:
            for line in method[1:-1]:
                requested_perm= match_api_call(line)
                if requested_perm:
                    if method[0] not in perm_methods:
                        perm_methods[method[0]] = []
                    perm_methods[method[0]].append(requested_perm)
        return perm_methods

    def find_in_path(path, mapping):
        """Traverse all smali files"""
        for root, dirs, files in os.walk(path):
            for file in files:
                fname = os.path.join(root, file)
                if not fname.endswith('.smali'):
                    continue
                f = open(fname, 'r')
                fcontent = f.readlines()
                #print(fname, end=" ")
                class_methods = inspect_methods(fcontent)
                permission_methods = APICall.find_in_class(class_methods, mapping)
                f.close()
                if permission_methods:
                    print(fname)
                    for m in permission_methods:
                        print(m, permission_methods[m])
                    print()

class Intent:
    def find_in_class(methods, mapping):
        """Find methods that invoke content providers."""
        perm_methods = {}
        def match_api_call(line):
            for api in mapping:
                if api in line:
                    print(api)
                    return mapping[api]
            return None
        for method in methods:
            for line in method[1:-1]:
                requested_perm= match_api_call(line)
                if requested_perm:
                    if method[0] not in perm_methods:
                        perm_methods[method[0]] = []
                    perm_methods[method[0]].append(requested_perm)
        return perm_methods

    def find_in_path(path, mapping):
        """Traverse all smali files"""
        for root, dirs, files in os.walk(path):
            for file in files:
                fname = os.path.join(root, file)
                if not fname.endswith('.smali'):
                    continue
                f = open(fname, 'r')
                fcontent = f.readlines()
                #print(fname, end=" ")
                class_methods = inspect_methods(fcontent)
                permission_methods = Intent.find_in_class(class_methods, mapping)
                f.close()
                if permission_methods:
                    print(fname)
                    for m in permission_methods:
                        print(m, permission_methods[m])
                    print()

class Invoke:
    def get_method(smali, called_method, called_chain):
        f = open(smali, 'r')
        fcontent = f.readlines()
        class_methods = inspect_methods(fcontent)
        f.close()
        last_item = called_chain.pop()
        for method in class_methods:
            method_name = method[0].split(" ")[-1].split('(')[0].strip()
            if method_name == called_method and len(method_name)>1:
                called_chain.append(last_item)
                Invoke.method_calls(method, called_chain)
                return

    def method_calls(method, called):
        for line in method[1:-1]:
            requested_perm= Invoke.match_invoke(line, called)

    def match_invoke(line, called):
        code = line.split()
        op = code[0].strip()
        rest = code[-1].strip()
        if op.startswith("invoke"):
            _class = rest.split(";->")[0].split("/")[-1]
            module = "/".join(rest.split(";->")[0].split("/")[:-1])
            method = rest.split(";->")[1].split("(")[0]
            if (not module.startswith("Lcom/momobills")) and module.startswith("Lcom/"):
                smali =  os.path.join(PATH, "NLG/datasets/apks/invoice_market/smali" , module[1:],  "{}.smali".format(_class))
                if os.path.exists(smali):
                    path = rest.split('(')[0]
                    if path not in called:
                        called.append(path)
                        Invoke.get_method(smali, method, called)
                
    def find_in_class(path, methods):
        """Find methods that invoke content providers."""
        perm_methods = {}  
        for method in methods:
            called = [(path, method[0])]
            Invoke.method_calls(method, called)
            if len(called) > 3:
                print(called)
        return perm_methods

    def find_in_path(path):
        """Traverse all smali files"""
        for root, dirs, files in os.walk(path):
            for file in files:
                fname = os.path.join(root, file)
                if not fname.endswith('.smali'):
                    continue
                f = open(fname, 'r')
                fcontent = f.readlines()
                #print(fname, end=" ")
                class_methods = inspect_methods(fcontent)
                permission_methods = Invoke.find_in_class(fname, class_methods)
                f.close()
                if permission_methods:
                    for m in permission_methods:
                        print(m, permission_methods[m])
                    print()

class CustomCodeAnalyzer:
    def __init__(self, path, module, mapping):
        self.path = path
        self.custom_path = os.path.join(self.path, "smali", module)
        self.api_mapping = mapping

    def extract_permission_by_contentp(self, methods):
        """Find methods that invoke content providers."""
        def is_exist(keyword, lst):
            for line in lst:
                if keyword.lower() in line.lower():
                    return True
            return False
        permission_methods = []
        for method in methods:
            exist_cr = is_exist("ContentResolver", method)
            exist_q = is_exist("query", method)
            exist_c = is_exist("contact", method)
            #if exist_cr:
            #    print(exist_cr , exist_q , exist_c)
            if exist_cr and exist_q and exist_c:
                permission_methods.append((method[0], "READ_CONTACTS"))
        return permission_methods

    def extract_permission_by_apicall(self, methods):
        """Find methods that invoke content providers."""
        perm_methods = []
        def match_api_call(line):
            for api in self.api_mapping:
                if api in line:
                    return self.api_mapping[api]
            return None
        for method in methods:
            for line in method[1:-1]:
                requested_perm= match_api_call(line) 
                if requested_perm:
                    perm_methods.append((method[0], requested_perm))
        return perm_methods

    def traverse_all_files(self):
        """Traverse all smali files"""
        cp_permission_statements = []
        api_permission_statements = []
        for root, dirs, files in os.walk(self.custom_path):
            for file in files:
                fname = os.path.join(root, file)
                if not fname.endswith('.smali'):
                    continue
                f = open(fname, 'r')
                fcontent = f.readlines()
                f.close()

                class_methods = self.inspect_methods(fcontent)
                class_name = self.inspect_class(fcontent)
                permission_methods = self.extract_permission_by_contentp(class_methods)
                if permission_methods:
                    cp_permission_statements.append((class_name, permission_methods))
                permission_methods = self.extract_permission_by_apicall(class_methods)
                if permission_methods:
                    api_permission_statements.append((class_name, permission_methods))
        return cp_permission_statements, api_permission_statements

    def inspect_class(self, fcontent):
        for line in fcontent:
            if line.startswith(SMALI_CLASS):
                parts = line.strip().split()
                if len(parts) == 2:
                    return parts[1]
                else:
                    return parts[2]

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

class ThirdPartyAnalyzer:
    def __init__(self, path, module, mapping):
        self.path = path
        self.module = module
        self.custom_path = os.path.join(path, "smali", module)
        self.api_mapping = mapping
    
    def extract_permission_by_contentp(self, method):
        """Find methods that invoke content providers."""
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
            permission_methods.append((method[0], "READ_CONTACTS"))
        return permission_methods

    def extract_permission_by_apicall(self, method):
        """Find methods that invoke content providers."""
        perm_methods = []
        def match_api_call(line):
            for api in self.api_mapping:
                if api in line:
                    return self.api_mapping[api]
            return None
        for line in method[1:-1]:
            requested_perm= match_api_call(line) 
            if requested_perm:
                perm_methods.append((method[0], requested_perm))
        return perm_methods

    def get_method(self, smali, called_method, called_chain):
        f = open(smali, 'r')
        fcontent = f.readlines()
        f.close()

        class_methods = self.inspect_methods(fcontent)
        class_name = self.inspect_class(fcontent)

        last_item = called_chain.pop()
        for method in class_methods:
            method_name = method[0].split(" ")[-1].split('(')[0].strip()
            if method_name == called_method:
                perm_cp = self.extract_permission_by_contentp(method)
                perm_api = self.extract_permission_by_apicall(method)
                

                called_chain.append((last_item, perm_cp, perm_api))
                self.method_calls(method, called_chain)
                return

    def match_invoke(self, line, called):
        code = line.split()
        op = code[0].strip()
        rest = code[-1].strip()
        if op.startswith("invoke"):
            _class = rest.split(";->")[0].split("/")[-1]
            module = "/".join(rest.split(";->")[0].split("/")[:-1])
            method = rest.split(";->")[1].split("(")[0]
            if (not module.startswith("L{}".format(self.module))):
                smali =  os.path.join(self.path, "smali" , module[1:],  "{}.smali".format(_class))
                if os.path.exists(smali):
                    path = rest.split('(')[0]
                    exist = True if len([path for m in called if m[0] == path]) else False
                    if not exist:
                        called.append(path)
                        self.get_method(smali, method, called)

    def method_calls(self, method, called):
        for line in method[1:-1]:
            requested_perm = self.match_invoke(line, called)

    def find_in_class(self, path, methods):
        """Find methods that invoke content providers."""
        call_chains = []
        for method in methods:
            #perm_cp = self.extract_permission_by_contentp(method)
            #perm_api = self.extract_permission_by_apicall(method)
            #if perm_cp:
            #    print(perm_cp)
            #if perm_api:
            #    print(perm_api)
            called = [(path, method[0])]
            self.method_calls(method, called)
            if len(called) > 1:
                call_chains.append(called)
        perm_chains = []
        
        for chain in call_chains:
            perms_cp = [p for m, p, c in chain[1:] if len(p) > 0]
            perms_api = [c for m, p, c in chain[1:] if len(c) > 0]
            if perms_cp:
                print(perms_cp)
            if perms_api:
                print(perms_api)
            
    def traverse_all_files(self):
        """Traverse all smali files"""
        for root, dirs, files in os.walk(self.custom_path):
            for file in files:
                fname = os.path.join(root, file)
                if not fname.endswith('.smali'):
                    continue
                f = open(fname, 'r')
                fcontent = f.readlines()
                f.close()
                class_methods = self.inspect_methods(fcontent)
                permission_methods = self.find_in_class(fname, class_methods)

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

    def inspect_class(self, fcontent):
        for line in fcontent:
            if line.startswith(SMALI_CLASS):
                parts = line.strip().split()
                if len(parts) == 2:
                    return parts[1]
                else:
                    return parts[2]

"""
1. Custom code
    1.1. API CALL
    1.2. Content Provider
    1.3. Intent
2. 3rd Party
    1.1. API CALL
    1.2. Content Provider
    1.3. Intent
3. All permissions
4. Manifest Permissions

TODO: 
Axplorer api-25 seti yerine hepsini al. : TAMAMLANDI
momobills e ozel yazdigin kisimlari cikar.
3. parti kutuphaneleri cikaracagin bir yontem bul.
"""

"""axplorer_map = axplorer_perm_api_map(os.path.join(PATH, "NLG/datasets/axplorer/permissions/api-25/sdk-map-25.txt"))
custom_path = os.path.join(PATH, "NLG/datasets/apks/invoice_market/smali/com/momobills")
custom_analyzer = CustomCodeAnalyzer(custom_path, axplorer_map)
out = custom_analyzer.traverse_all_files()
"""

def get_custom_code(path):
    custom_path = os.path.join(path, "AndroidManifest.xml")
    com = ""
    module = ""
    with open(custom_path) as target:
        for line in target:
            if "<?xml" in line:
                matchObj = re.match(r'.*package="([a-zA-Z\.0-9]*)"', line, re.M|re.I)
                custom_code = matchObj.group(1)
                parts = custom_code.split(".")
                com = parts[0]
                module = parts[1]
    return os.path.join(com, module)


axplorer_map = {}
for i in range(16, 26):
    path = os.path.join(PATH, "NLG/datasets/axplorer/permissions/api-{}/sdk-map-{}.txt".format(i,i))
    if os.path.exists(path):
        mapping = axplorer_perm_api_map(path)
        for k in mapping:
            if k not in axplorer_map:
                axplorer_map[k] = []
            for e in mapping[k]:
                if e not in axplorer_map[k]:
                    axplorer_map[k].append(e)

err = 0
ok = 0
analyzed_apks_dir = os.path.join(PATH, "Final")
for f in os.listdir(analyzed_apks_dir):
    full_path = os.path.join(analyzed_apks_dir, f)
    if os.path.isdir(full_path):
        try:
            module = get_custom_code(full_path)
            print("Analyzed APK ", f, "Module", module)

            
            thirdparty_analyzer = ThirdPartyAnalyzer(full_path, module, axplorer_map)
            thirdparty_analyzer.traverse_all_files()
            
            """
            custom_analyzer = CustomCodeAnalyzer(full_path, module, axplorer_map)
            cp, api = custom_analyzer.traverse_all_files()
            print(",","Custom Code API CALL Permissions:")
            for c, p in api:
                print(",",",",c)
                for m, perms in p:
                    print(",",",",",", m.split()[-1], ",", perms)
            print(",","Custom Code Content Provider Permissions:")
            for c, p in cp:
                print(",",",", c)
                for m, perms in p:
                    print(",",",",",", m.split()[-1], ",", perms)
            """
        except:
            pass

"""
custom_path = os.path.join(PATH, "NLG/datasets/apks/invoice_market/smali/com/momobills")
thirdparty_analyzer = ThirdPartyAnalyzer(custom_path, axplorer_map)
thirdparty_analyzer.traverse_all_files()
"""

#axplorer_map = axplorer_perm_api_map(os.path.join(PATH, "NLG/datasets/axplorer/permissions/api-25/sdk-map-25.txt"))
#APICall.find_in_path(custom_path, axplorer_map)
#pscout_intent_map = pscout_perm_api_map("/home/huseyinalecakir/NLG/datasets/PScout/results/API_22/intentpermission")
#Intent.find_in_path("/home/huseyinalecakir/NLG/datasets/apks/invoice_market/smali/com/momobills", pscout_intent_map)
#Invoke.find_in_path(os.path.join(PATH, "NLG/datasets/apks/invoice_market/smali/com/momobills"))



