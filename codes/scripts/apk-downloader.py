import os
import argparse
import subprocess

from tqdm import tqdm
import pandas as pd

def get_apps(file_dir):
    df = pd.read_csv(file_dir)
    sentences = df["sentence"]
    bool_series = sentences.str.startswith("##")
    apps = [app.replace("##", "") for app in sentences[bool_series]]
    apps = [app.replace(".apk", "") for app in apps if app.endswith(".apk")]
    return apps

if __name__=="__main__":
    parser = argparse.ArgumentParser(description='APK Downloader')
    parser.add_argument('--file-dir', dest='file_dir', type=str, required=True, help='Path to DesRe file')
    parser.add_argument('--downloader', dest='downloader', type=str, required=True, help='Path to PlayStore downloader')

    args = parser.parse_args()


    #Get package names
    apps = get_apps(args.file_dir)

    #Dowload apps
    for a in tqdm(apps):
        subprocess.run(["python", args.downloader, a], cwd=os.path.dirname(args.downloader))
