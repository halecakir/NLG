import argparse
import os
import shutil
import subprocess

import pandas as pd
from tqdm import tqdm


def get_apps_desre(file_type, file_dir):
    if file_type == "DesRe":
        df = pd.read_csv(file_dir)
        sentences = df["sentence"]
        bool_series = sentences.str.startswith("##")
        apps = [app.replace("##", "") for app in sentences[bool_series]]
        return [app.replace(".apk", "") for app in apps if app.endswith(".apk")]
    else:
        df = pd.read_csv(file_dir)
        return df["app_id"]

    
    
if __name__=="__main__":
    parser = argparse.ArgumentParser(description='APK Downloader')
    parser.add_argument('--file-type', dest='file_type', type=str, required=True, help='File Type')
    parser.add_argument('--file-dir', dest='file_dir', type=str, required=True, help='Path to DesRe file')
    parser.add_argument('--downloader', dest='downloader', type=str, required=True, help='Path to PlayStore downloader')

    args = parser.parse_args()

    assert args.file_type == "DesRe" or args.file_type == "Crawled", "File type must be 'DesRe' or 'Crawled'"
    #Get package names
    apps = get_apps_desre(args.file_type, args.file_dir)
    
    #Dowload apps
    for a in tqdm(apps):
        subprocess.run(["python", args.downloader, a], cwd=os.path.dirname(args.downloader)) 
  
