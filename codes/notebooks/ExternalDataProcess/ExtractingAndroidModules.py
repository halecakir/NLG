#!/usr/bin/env python
# coding: utf-8

# In[1]:


import pickle
import os
    
PATH = "/data/huseyinalecakir_data/CallGraphOutputs"
##List files
call_graph_files = []
for file in os.listdir(PATH):
    call_graph_files.append(os.path.join(PATH, file))


# In[2]:


## Read files
"""app_permissions = {}
app_chains = {}
app_nodes = {}
app_analyzers = {}
items = {}"""
def call_script(graph_files, app_permissions, app_chains, app_nodes, app_analyzers, items):
    for idx, file_dir in enumerate(graph_files):
        with open(file_dir, "rb") as target:
            item, app_chain, app_node, app_permission, app_analyzer = pickle.load(target)
            smali = item[b"smali"].decode("utf-8")
            items[smali] = item
            app_chains[smali] = app_chain[smali]
            app_nodes[smali] = app_node[smali]
            app_permissions[smali] = app_permission[smali]
            app_analyzers[smali] = app_analyzer[smali]


# In[ ]:


from multiprocessing import Process, Manager

manager = Manager()
app_permissions = manager.dict()
app_chains = manager.dict()
app_nodes = manager.dict()
app_analyzers = manager.dict()
items = manager.dict()

processes = []
chunk = 100
for i in range(0, len(call_graph_files), chunk):
    processes.append(Process(target=call_script, args=(call_graph_files[i:i+chunk], app_permissions, app_chains, app_nodes, app_analyzers, items)))

for p in processes:
    p.start()

for p in processes:
    p.join()


# In[ ]:


## Report requested permissions
requested_permissions = {}
for app_name in app_permissions:
    for permission in app_permissions[app_name]:
        if permission not in requested_permissions:
            requested_permissions[permission] = 0
        requested_permissions[permission] += 1

sorted_requested_permissions = {k: v for k, v in sorted(requested_permissions.items(), key=lambda item: item[1], reverse=True)}

for permission in sorted_requested_permissions:
    print(permission, sorted_requested_permissions[permission])


# In[ ]:


## Third party permission calls and third party libs listing
def dfs_third_party(node, permission_nodes):
    if node.api_permissions or node.cp_permissions:
        if node.is_third_party:
            if not node.detected_lib:
                node.detected_lib = {"package" : "NOT_FOUND"}
            permission_nodes.append(node)
    for child in node.childs:
        dfs_third_party(child, permission_nodes)

def call_hier(node, call_nodes):
    if node:
        call_nodes.append(node)
        call_hier(node.parent, call_nodes)
        
thirdparties = {}
with open("permission_nodes_custom.txt", "w") as target:
    for key in app_chains:
        target.write("{},\n".format(key.split("/")[-1]))
        permission_nodes = []
        for node in app_nodes[key]:
            dfs_third_party(node, permission_nodes)
        for node in permission_nodes:
            if node.detected_lib["package"] not in thirdparties:
                thirdparties[node.detected_lib["package"]] = 0
            thirdparties[node.detected_lib["package"]] += 1  
            target.write(",CALL:{}::{}::{}::{}\n".format(node.detected_lib["package"].strip(), node.class_name.strip(), node.method_name.strip(), ",".join(list(node.api_permissions)+list(node.cp_permissions))))
            
sorted_thirdparties = {k: v for k, v in sorted(thirdparties.items(), key=lambda item: item[1], reverse=True)}

for permission in sorted_thirdparties:
    print(permission, sorted_thirdparties[permission])    


# In[ ]:


## Permission requested from custom code and third party codes
def dfs_all(node, permission_nodes):
    if node.api_permissions or node.cp_permissions:
        if not node.detected_lib:
            node.detected_lib = {"package" : "NOT FOUND"}
        permission_nodes.append(node)
    for child in node.childs:
        dfs_all(child, permission_nodes)

def call_hier_all(node, call_nodes):
    if node:
        call_nodes.append(node)
        call_hier_all(node.parent, call_nodes)
customcodes_permissions = {}
thirdparty_permissions = {}

with open("permission_nodes_all.txt", "w") as target:
    for key in app_chains:
        target.write("{},\n".format(key.split("/")[-1]))
        permission_nodes = []
        for node in app_nodes[key]:
            dfs_all(node, permission_nodes)
        for node in permission_nodes:
            permissions = list(node.api_permissions)+list(node.cp_permissions)
            
            for p in permissions:
                if node.is_third_party:
                    if p not in thirdparty_permissions:
                        thirdparty_permissions[p] = 0
                    thirdparty_permissions[p] += 1
                else:
                    if p not in customcodes_permissions:
                        customcodes_permissions[p] = 0
                    customcodes_permissions[p] += 1
            target.write(",CALL:{}::{}::{}::{}\n".format(node.detected_lib["package"].strip(), node.class_name.strip(), node.method_name.strip(), ",".join(list(node.api_permissions)+list(node.cp_permissions))))
            
sorted_customcodes_permissions = {k: v for k, v in sorted(customcodes_permissions.items(), key=lambda item: item[1], reverse=True)}
print("Custom Code")
for permission in sorted_customcodes_permissions:
    print(permission, sorted_customcodes_permissions[permission])      
 
sorted_thirdparty_permissions = {k: v for k, v in sorted(thirdparty_permissions.items(), key=lambda item: item[1], reverse=True)}
print("Third Party Code")
for permission in sorted_thirdparty_permissions:
    print(permission, sorted_thirdparty_permissions[permission])     


# In[ ]:


## Saving third party modules 
third_party_calls = {}
third_party_total_call = {}
detected_libs_infos = []
for key in app_chains:
    permission_nodes = []
    for node in app_nodes[key]:
        dfs_third_party(node, permission_nodes)
    for node in permission_nodes:
        detected_libs_infos.append([node.detected_lib["package"].strip(), node.class_name.strip(),  node.method_name.strip(), list(node.api_permissions)+list(node.cp_permissions)])
        if node.detected_lib["package"].strip() not in third_party_calls:
            third_party_calls[node.detected_lib["package"].strip()] = {}
        if node.class_name.strip() not in third_party_calls[node.detected_lib["package"].strip()]:
            third_party_calls[node.detected_lib["package"].strip()][node.class_name.strip()] = {}
        if node.method_name.strip() not in third_party_calls[node.detected_lib["package"].strip()][node.class_name.strip()]:
            third_party_calls[node.detected_lib["package"].strip()][node.class_name.strip()][node.method_name.strip()] = {"count": 0, "permissions":set()}
        third_party_calls[node.detected_lib["package"].strip()][node.class_name.strip()][node.method_name.strip()]["count"] += 1
        third_party_calls[node.detected_lib["package"].strip()][node.class_name.strip()][node.method_name.strip()]["permissions"].update(list(node.api_permissions)+list(node.cp_permissions))
        
        if node.detected_lib["package"].strip() not in third_party_total_call:
            third_party_total_call[node.detected_lib["package"].strip()] = 0
        third_party_total_call[node.detected_lib["package"].strip()] += 1
with open("AndroidModules.pkl", "wb") as f:
    pickle.dump([third_party_calls, third_party_total_call, detected_libs_infos], f)  


# In[ ]:


sorted_third_party_total_call = {k: v for k, v in sorted(third_party_total_call.items(), key=lambda item: item[1], reverse=True)}
print("Lib use counts:\n")
for permission in sorted_third_party_total_call:
    print(permission, sorted_third_party_total_call[permission])

