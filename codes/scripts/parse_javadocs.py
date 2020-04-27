import os
import re
from bs4 import BeautifulSoup
import pandas as pd

from log_utils import ColoredLogger

logger = ColoredLogger("parser")

JAVADOC_DIR = os.path.join(
    os.environ["NLG_ROOT"], "datasets/libraries/library-javadocs")
OUTPUT_DIR = os.path.join(
    os.environ["NLG_ROOT"], "output/other")

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
    logger.debug(dir)
    class_ = {}
    class_["groupid"] = groupid
    class_["artefactid"] = artefactid
    soup = BeautifulSoup(open(dir, 'r').read(), 'html.parser')

    # API name
    api = soup.find("div", {"class": "subTitle"}).get_text()
    class_["api"] = api

    # Class name
    class_name = soup.find("h2", {"class": "title"}).get_text()
    logger.debug(class_name)
    class_["class"] = class_name

    # Class description
    class_description_block = soup.find(
        "div", {"class": "description"}).find("div", {"class": "block"})
    if class_description_block:
        if class_description_block.find("h1"):
            class_description_block.find("h1").clear()
        class_description = re.sub(
            ' +', ' ', class_description_block.get_text().strip().replace('\n', ''))
        logger.debug(class_description)
        class_["description"] = class_description

    logger.debug("-Methods-")
    # Method details
    methods = []
    details = soup.find("div", {"class": "details"})
    if details:
        details = details.find("li", {"class": "blockList"}).find_all(
            "ul", {"class": "blockList"})
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
                    logger.debug(method_signature)
                    if method_description_block:
                        method_description = re.sub(
                            ' +', ' ', method_description_block.get_text().replace('\n', ''))
                        method["description"] = method_description.replace(
                            '"', '')
                        logger.debug(method_description)
                    methods.append(method)
                    logger.debug("---")
    logger.debug("-----END OF CLASS------\n")
    return class_, methods


def parse_java_docs():
    class_descriptions = []
    method_descriptions = []
    for folder in os.listdir(JAVADOC_DIR):
        dir = os.path.join(JAVADOC_DIR, folder)
        logger.debug("Directory {}".format(dir))
        components = folder.split("__")
        groupid = components[0]
        artefactid = components[1]
        if os.path.isdir(dir):
            # Parse JavaDoc Content
            try:
                cls_descs, mtd_descs = parse_class_list(
                    dir, groupid, artefactid)
                class_descriptions.extend(cls_descs)
                method_descriptions.extend(mtd_descs)
            except FileNotFoundError:
                logger.error("File not found {}".format(dir))
            except AttributeError as error:
                logger.error(error)

    class_ = pd.DataFrame(class_descriptions)
    method_ = pd.DataFrame(method_descriptions)
    class_.to_csv(os.path.join(OUTPUT_DIR, "classes.csv"))
    method_.to_csv(os.path.join(OUTPUT_DIR, "methods.csv"))


if __name__ == "__main__":
    parse_java_docs()
