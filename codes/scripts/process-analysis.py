import os
import operator
import pandas as pd

ANALYSIS_DIR = os.path.join(os.environ["NLG_ROOT"], "datasets/analysis")


APK_DIR = os.path.join(ANALYSIS_DIR, "apk-analysis/")
DEX_DIR = os.path.join(ANALYSIS_DIR, "dex-analysis/")


def list_files(folder_name):
    files = [os.path.join(folder_name, f) \
            for f in os.listdir(folder_name) if os.path.isfile(os.path.join(folder_name, f))]
    return files

def convert_jsons_to_df(files):
    df_all = None
    for f in files:
        df = pd.read_json(f) 
        df_all = pd.concat([df_all, df], axis=1, sort=False) if df_all is not None else df
    return df_all

def calculate_df_statistics(df):
    apicall2perm = {}
    method2api = {}
    apicall_usage = {}
    method_usage = {}
    permission_usage = {}
    for row in df.iterrows():
        index  = row[0]
        rest = row[1]
        perm = rest.loc[rest.first_valid_index()]
        splitted = index.strip().split("---")
        api_call = splitted[-1]
        method = "{}.{}".format(splitted[0], splitted[1])
        apicall2perm[api_call] = perm
        if method not in method2api:
            method2api[method] = set()
        method2api[method].add(api_call)
        apicall_usage[api_call] = apicall_usage.get(api_call, 0) + 1
        method_usage[method] = method_usage.get(method, 0) + 1
        for p in perm:
            permission_usage[p] = permission_usage.get(p, 0) + 1
    return apicall2perm, method2api, apicall_usage, method_usage, permission_usage



apk_files = list_files(APK_DIR)
dex_files = list_files(DEX_DIR)

df_apk = convert_jsons_to_df(apk_files)
df_dex = convert_jsons_to_df(dex_files)
df = pd.concat([df_apk, df_dex], axis=1, sort=False)

apicall2perm, method2api, apicall_usage, method_usage, permission_usage = calculate_df_statistics(df)

def top_n(data, n=10):
    sorted_x = sorted(data.items(), key=operator.itemgetter(1), reverse=True)
    with open("output.txt", "w") as target:
        for item in sorted_x[:n]:
            if isinstance(item[1], list):
                print("{}".format(item[0]), end="")
                target.write("{}".format(item[0]))
                for i in item[1]:
                    print(",{}".format(i), end="")
                    target.write(",{}".format(i))
                print()
                target.write("\n")
            else:
                print("{},{}".format(item[0], item[1]))
                target.write("{},{}\n".format(item[0], item[1]))
    print("-----\n")

perm2apicall = {}
for a in apicall2perm:
    for p in apicall2perm[a]:
        if p not in perm2apicall:
            perm2apicall[p] = []
        perm2apicall[p].append(a)

location_api_calls = perm2apicall["android.permission.ACCESS_FINE_LOCATION"]

apicall2method = {}
for a in method2api:
    for p in method2api[a]:
        if p not in apicall2method:
            apicall2method[p] = set()
        apicall2method[p].add(a)

location_methods = []
for api in location_api_calls:
    location_methods.extend(list(apicall2method[api]))

    

