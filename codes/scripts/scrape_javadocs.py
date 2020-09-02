import requests
import os
import re
import json
import sys

from bs4 import BeautifulSoup
from lxml import html
import urllib
import zipfile

from log_utils import ColoredLogger

logger = ColoredLogger("downloader")

BASE_URL = "https://javadoc.io"

"""LIBRARIES_DIR = os.path.join(
    os.environ["NLG_ROOT"], "datasets/libraries/library-descriptions")
JAVADOC_DIR = os.path.join(
    os.environ["NLG_ROOT"], "datasets/libraries/library-javadocs")
ANALYZED_LIBS = os.path.join(LIBRARIES_DIR, "analyzed-libraries.json")
"""

JAVADOC_DIR = sys.argv[1]
ANALYZED_LIBS = sys.argv[2]

class NoJavaDocError(Exception):
    """No JavaDoc is released for given artifact"""
    pass


class JavaDocRefreshError(Exception):
    """Javadoc is being downloaded. Normally this will be completed within 10 minutes."""
    pass

class JavaDocAlreadyDownloadedError(Exception):
    """Javadoc has already downloaded."""
    pass

class ArtifactNotExistError(Exception):
    """Artifact does not exist."""
    pass


def get_download_url(url):
    #logger.debug("Download url is scraping {}".format(url))
    page = requests.get(url, timeout=30)
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
    #logger.debug("Url scraping is completed")
    return urllib.parse.urljoin(BASE_URL, path)


def download_jar(url, save_dir):
    #logger.debug("Jar is downloading {}".format(url))
    link_components = urllib.parse.urlsplit(url).path.split('/')
    groupid = link_components[2]
    artefactid = link_components[3]
    version = link_components[4]

    outfile = os.path.join(save_dir, "{}__{}__{}.zip".format(
        groupid, artefactid, version))
    if not os.path.exists(outfile):
        request = requests.get(url, timeout=30, stream=True)
        with open(outfile, 'wb') as fh:
            for chunk in request.iter_content(1024 * 1024):
                # Write the chunk to the file
                fh.write(chunk)
    else:
        raise JavaDocAlreadyDownloadedError()
    #logger.debug("Downloading is completed")
    return outfile


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
        data = data["libraries"] if "libraries" in data else data
        for row in data:
            try:
                groupid, artefactid = row["groupid"], row["artefactid"]
                java_doc_url = "{}/doc/{}/{}".format(
                    BASE_URL, groupid, artefactid)
                if not is_file_exist(JAVADOC_DIR, groupid, artefactid):
                    # Get Downloadeble url
                    url = get_download_url(java_doc_url)
                    # Download JavaDoc as zip
                    saved_zip = download_jar(url, JAVADOC_DIR)
                    # Extract file
                    try:
                        with zipfile.ZipFile(saved_zip, 'r') as zip:
                            dir = saved_zip.replace(".zip", "")
                            if not os.path.exists(dir):
                                os.mkdir(dir)
                            zip.extractall(dir)
                        logger.info(
                            "SUCCESS: File downloaded {}".format(java_doc_url))
                    except zipfile.BadZipFile:
                        logger.error(
                            "File is not a zip file {}".format(java_doc_url))
                        logger.error(
                            "File is removing {}".format(saved_zip))
                        os.remove(saved_zip)
            except JavaDocAlreadyDownloadedError:
                logger.warning(
                    "File has already downloaded {}".format(java_doc_url))
            except NoJavaDocError:
                logger.error(
                    "NoJavaDoc Error {}".format(java_doc_url))
            except JavaDocRefreshError:
                logger.error(
                    "JavaDocRefresh Error {}".format(java_doc_url))
            except ArtifactNotExistError:
                logger.error(
                    "ArtifactNotExist Error {}".format(java_doc_url))
            except requests.exceptions.ReadTimeout:
                logger.error("Timeout Error {}".format(java_doc_url))
            except requests.exceptions.ConnectionError:
                logger.error(
                    "Connection Error {}".format(java_doc_url))
            except TypeError:
                logger.error("TypeError {}".format(row))

if __name__ == "__main__":
    download_java_docs()
