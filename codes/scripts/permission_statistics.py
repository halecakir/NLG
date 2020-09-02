
import os
import argparse
import subprocess

def get_permission_stats(root_path):
    permission_stats = {}
    for path in os.listdir(root_path):
        if path.endswith(".apk"):
            full_path = os.path.join(root_path, path)
            result = subprocess.run(["aapt", "d", "permissions", full_path], capture_output=True)
            s = str(result.stdout).strip()
            for line in s.split("'\\n"):
                if "permission" in line:
                    if "name='" in line:
                        perm = line.split("name='")[1].strip()
                    else:
                        perm = line.split(" ")[1].strip()
                    if perm not in permission_stats:
                        permission_stats[perm] =  0
                    permission_stats[perm] += 1
    return permission_stats

if __name__=="__main__":
    parser = argparse.ArgumentParser(description='Permission Tool')
    parser.add_argument('--file-dir', dest='file_dir', type=str, required=True, help='APK dir')
    parser.add_argument('--output', dest='output', type=str, required=True, help='Output file.')
    args = parser.parse_args()

    
    
    permission_stats = get_permission_stats(args.file_dir)    
            
    sorted_requested_permissions = {k: v for k, v in sorted(permission_stats.items(), key=lambda item: item[1], reverse=True)}
    with open(args.output, "w") as target:
        for permission in sorted_requested_permissions:
            target.write(permission + " , " + str(sorted_requested_permissions[permission]) + " , " + "\n")