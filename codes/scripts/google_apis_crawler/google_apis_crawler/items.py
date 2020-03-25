# -*- coding: utf-8 -*-
import scrapy
from scrapy.loader.processors import TakeFirst, Join

class GoogleApisCrawlerItem(scrapy.Item):
    page = scrapy.Field(output_processor=TakeFirst(),)
    name = scrapy.Field(output_processor=TakeFirst(),)
    description = scrapy.Field(output_processor=TakeFirst(),)
    methods = scrapy.Field(output_processor=TakeFirst(),)