# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy
from scrapy.loader.processors import TakeFirst, Join



class GoogleApisCrawlerItem(scrapy.Item):
    page = scrapy.Field(output_processor=TakeFirst(),)
    name = scrapy.Field(output_processor=TakeFirst(),)
    description = scrapy.Field(output_processor=TakeFirst(),)
