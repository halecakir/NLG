import scrapy
from scrapy.loader import ItemLoader

import urllib.parse
from bs4 import BeautifulSoup

from google_apis_crawler.items import GoogleApisCrawlerItem

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
        class_description = class_page_parser.find_all("p")[2].get_text().strip().replace('\n', '')

        loader.add_value("class_name", class_name)
        loader.add_value("class_description", class_description)
        loader.add_value("class_page", class_page)
        yield loader.load_item()



