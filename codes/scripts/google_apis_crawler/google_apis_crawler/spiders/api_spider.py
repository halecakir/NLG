import scrapy
from scrapy.loader import ItemLoader

import urllib.parse
from bs4 import BeautifulSoup

from google_apis_crawler.items import GoogleApisCrawlerItem
from google_apis_crawler.logger import logger

def get_paragraphs(tag):
    hr_seen = False
    paragraphs = []
    for i in tag.contents:
        if i.name == "hr":
            hr_seen = True
        if hr_seen:
            if i.name == "p":
                if 'class' in i.attrs and 'caution' in i.attrs['class']:
                    #check whether class is was deprecated
                    pass
                else:
                    p = i.get_text().strip().replace('\n', '')
                    if p:
                        paragraphs.append(p)
    return paragraphs

class ApiSpider(scrapy.Spider):
    BASE_URL = "https://developer.android.com/"

    name = "apis"
    start_urls = [
        'https://developer.android.com/reference',
    ]

    def parse(self, response):
        """
            Parses the left nagivation panel. Creates the list of components.
        """
        navigation_parser = BeautifulSoup(response.body, "lxml") 
        for tag in navigation_parser.find_all(class_='devsite-nav-title'):
            if "gc-analytics-event" not in tag["class"]:
                href = tag.get("href")
                if href is not None and "kotlin" not in href:
                    absolute_href = urllib.parse.urljoin(ApiSpider.BASE_URL, href)
                    yield scrapy.Request(absolute_href, self.parse_component)
                

    def parse_component(self, response):
        """
            Parses the each component. Creates the list of apis related to that component.
        """
        component_page_parser = BeautifulSoup(response.body, "lxml")
        for tag in component_page_parser.find_all("tr"):
            href = tag.a["href"]
            absolute_href = urllib.parse.urljoin(ApiSpider.BASE_URL, href)
            yield scrapy.Request(absolute_href, self.parse_api)
            

    def parse_api(self, response):
        """
            Parses the each api. Creates the list of classes related to that api.
        """
        api_page_parser = BeautifulSoup(response.body, "lxml")
        for tag in api_page_parser.find_all("tr"):
            href = tag.a["href"]
            absolute_href = urllib.parse.urljoin(ApiSpider.BASE_URL, href)
            yield scrapy.Request(absolute_href, self.parse_classes)
            
    #def parse(self, response):
    def parse_classes(self, response):
        """
            Parses the each classs. 
            Creates the list of method related to that classes. (Will be implemented later.)
            Also, gathers classes information--their name and description.
        """
        loader = ItemLoader(item=GoogleApisCrawlerItem())
        class_page_parser = BeautifulSoup(response.body, "lxml")
        class_page = response.request.url
        class_name = class_page_parser.find_all(class_="jd-inheritance-class-cell")[-1].get_text().strip()
        all_paragraphs = get_paragraphs(class_page_parser.find(id="jd-content"))

        #check whether class is was deprecated
        #if all_paragraphs[2].get_text().find("class was deprecated") != -1:
        #    class_description = all_paragraphs[3].get_text().strip().replace('\n', '')
        #else:
        #    class_description = all_paragraphs[1].get_text().strip().replace('\n', '')
        class_description = " ".join(all_paragraphs)

        #if class descriptions is empty save them also.
        if not class_description: 
            class_description = " "
            
        loader.add_value("name", class_name)
        loader.add_value("description", class_description)
        loader.add_value("page", class_page)
        logger.warning("Class name : {}\n-----\nClass description : {}\n-----\nClass page {}\n\n\n\n". \
                format(class_name, class_description, class_page))
        yield loader.load_item()



