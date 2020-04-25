import requests
import os
import re
import json

from bs4 import BeautifulSoup
from lxml import html
import urllib
import zipfile

BASE_URL = "https://javadoc.io"

LIBRARIES_DIR = os.path.join(os.environ["NLG_ROOT"], "datasets/libraries/library-descriptions")
JAVADOC_DIR = os.path.join(os.environ["NLG_ROOT"], "datasets/libraries/library-javadocs")
ANALYZED_LIBS = os.path.join(LIBRARIES_DIR, "analyzed-libraries.json")


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class NoJavaDocError(Exception):
    """No JavaDoc is released for given artifact"""
    pass


class JavaDocRefreshError(Exception):
    """Javadoc is being downloaded. Normally this will be completed within 10 minutes."""
    pass


class ArtifactNotExistError(Exception):
    """Artifact does not exist."""
    pass


def get_download_url(url):
    print("Download url is scraping {}".format(url))
    page = requests.get(url, timeout=20)
    soup = BeautifulSoup(page.content, "html.parser")

    # check javadoc is exist
    if soup.find(text=re.compile('No JavaDoc is released for artifact')):
        raise NoJavaDocError()
    if soup.find(text=re.compile('Normally this will be completed within 10 minutes.')):
        raise JavaDocRefreshError()
    if soup.find("div", {"role": "alert"}) and soup.find("div", {"role": "alert"}).find(text=re.compile("does not exist.")):
        raise ArtifactNotExistError()

    tree = html.fromstring(page.content)
    elements = tree.xpath('//*[@id="navbar-collapse"]/ul[1]/li[4]/a')
    path = elements[0].attrib['href']
    print("Url scraping is completed")
    return urllib.parse.urljoin(BASE_URL, path)


def download_jar(url, save_dir):
    print("Jar is downloading {}".format(url))
    link_components = urllib.parse.urlsplit(url).path.split('/')
    groupid = link_components[2]
    artefactid = link_components[3]
    version = link_components[4]

    outfile = os.path.join(save_dir, "{}__{}__{}.zip".format(
        groupid, artefactid, version))
    if not os.path.exists(outfile):
        request = requests.get(url, timeout=20, stream=True)
        with open(outfile, 'wb') as fh:
            for chunk in request.iter_content(1024 * 1024):
                # Write the chunk to the file
                fh.write(chunk)
        #urllib.request.urlretrieve(url, outfile)
    else:
        print(bcolors.WARNING +
              "File has already downloaded {}".format(url) + bcolors.ENDC)
    print("Downloading is completed")
    return outfile


def parse_class_list(dir, groupid, artefactid):
    classes, methods = [], []
    all_classes_html = os.path.join(dir, "allclasses-frame.html")
    soup = BeautifulSoup(open(all_classes_html, 'r').read(), 'html.parser')
    filtered = soup.find_all('a')
    for element in filtered:
        class_dir = os.path.join(dir, element['href'])
        c, ms = single_class(class_dir, groupid, artefactid)
        classes.append(c)
        methods.extend(ms)
    return classes, methods

def single_class(dir, groupid, artefactid):
    print(dir)
    class_ = {}
    class_["groupid"] = groupid
    class_["artefactid"] = artefactid
    soup = BeautifulSoup(open(dir, 'r').read(), 'html.parser')

    # API name
    api = soup.find("div", {"class": "subTitle"}).get_text()
    class_["api"] = api 

    # Class name
    class_name = soup.find("h2", {"class": "title"}).get_text()
    #print(class_name)
    class_["class"] = class_name 

    # Class description
    class_description_block = soup.find(
        "div", {"class": "description"}).find("div", {"class": "block"})
    if class_description_block:
        if class_description_block.find("h1"):
            class_description_block.find("h1").clear()
        class_description = re.sub(
            ' +', ' ', class_description_block.get_text().strip().replace('\n', ''))
        #print(class_description)
        class_["description"] = class_description 

    #print("-Methods-")
    # Method details
    methods = []
    details = soup.find("div", {"class": "details"})
    if details:
        details = details.find("li", {"class": "blockList"}).find_all("ul", {"class": "blockList"})
        for d in details:
            if d.find("a", {"name": "method.detail"}):
                for ul_block in d.find_all("ul", {"class": "blockList"}):
                    method_signature = re.sub(
                        ' +', ' ', ul_block.find("pre").get_text().strip().replace('\n', ''))
                    method_description_block = ul_block.find(
                        "div", {"class": "block"})
                    method = {}
                    method["groupid"] = groupid
                    method["artefactid"] = artefactid
                    method["api"] = api 
                    method["class"] = class_name
                    method["method"] = method_signature


                    #print(method_signature)
                    if method_description_block:
                        method_description = re.sub(
                            ' +', ' ', method_description_block.get_text().replace('\n', ''))
                        method["description"] = method_description.replace('"', '')
                        #print(method_description)
                    methods.append(method)
                    #print("---")
    #print("-----END OF CLASS------\n")
    return class_, methods

def is_file_exist(path, groupid, artefactid):
    for line in os.listdir(path):
        if os.path.isdir(os.path.join(path, line)) and line.startswith("{}__{}".format(groupid, artefactid)):
            return True
    return False

def download_java_docs():
    refresh_pages = []
    not_exist_artifacts = []
    timeouts = []
    with open(ANALYZED_LIBS, "r") as target:
        data = json.load(target)
        for row in data:
            try:
                groupid, artefactid = row["groupid"], row["artefactid"]
                java_doc_url = "{}/doc/{}/{}".format(BASE_URL, groupid, artefactid)
                if not is_file_exist(JAVADOC_DIR, groupid, artefactid):
                    # Get Downloadeble url
                    url = get_download_url(java_doc_url)
                    # Download JavaDoc as zip
                    saved_zip = download_jar(url, JAVADOC_DIR)
                    # Extract file
                    with zipfile.ZipFile(saved_zip, 'r') as zip:
                        dir = saved_zip.replace(".zip", "")
                        if not os.path.exists(dir):
                            os.mkdir(dir)
                        zip.extractall(dir)
                    print(bcolors.OKGREEN + "SUCCESS: File downloaded {}".format(java_doc_url) + bcolors.ENDC)
                else:
                    print(bcolors.WARNING + "File has already downloaded {}".format(java_doc_url) + bcolors.ENDC)
            except NoJavaDocError:
                print(bcolors.FAIL +
                    "NoJavaDoc Error {}".format(java_doc_url) + bcolors.ENDC)
            except JavaDocRefreshError:
                refresh_pages.append(java_doc_url)
                print(bcolors.FAIL +
                    "JavaDocRefresh Error {}".format(java_doc_url) + bcolors.ENDC)
            except ArtifactNotExistError:
                not_exist_artifacts.append(java_doc_url)
                print(bcolors.FAIL +
                    "ArtifactNotExist Error {}".format(java_doc_url) + bcolors.ENDC)
            except requests.exceptions.ReadTimeout:
                timeouts.append(java_doc_url)
                print(bcolors.FAIL +
                    "Timeout Error {}".format(java_doc_url) + bcolors.ENDC)
            except requests.exceptions.ConnectionError:
                print(bcolors.FAIL +
                    "Connection Error {}".format(java_doc_url) + bcolors.ENDC)
            except zipfile.BadZipFile:
                print(bcolors.FAIL + bcolors.UNDERLINE +
                    "File is not a zip file {}".format(java_doc_url) + bcolors.ENDC)

def parse_java_docs():
    class_descriptions = []
    method_descriptions = []
    for folder in os.listdir(JAVADOC_DIR):
        dir = os.path.join(JAVADOC_DIR, folder)
        components = folder.split("__")
        groupid = components[0]
        artefactid = components[1]
        if os.path.isdir(dir):
            #Parse JavaDoc Content
            try:
                cls_descs, mtd_descs = parse_class_list(dir, groupid, artefactid)
                class_descriptions.extend(cls_descs)
                method_descriptions.extend(mtd_descs)
            except FileNotFoundError:
                print(bcolors.FAIL + "File not found {}".format(dir) + bcolors.ENDC)
            except AttributeError as error:
                print(error)

    import pandas as pd
    class_ = pd.DataFrame(class_descriptions)
    method_ = pd.DataFrame(method_descriptions)
    class_.to_csv(os.path.join(JAVADOC_DIR, "classes.csv"))
    method_.to_csv(os.path.join(JAVADOC_DIR, "methods.csv"))


