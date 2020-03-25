# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html

from sqlalchemy.orm import sessionmaker
from scrapy.exceptions import DropItem
from google_apis_crawler.models import ClassInfo, db_connect, create_table
from google_apis_crawler.logger import logger


class GoogleApisCrawlerPipeline(object):
    def __init__(self):
        engine = db_connect()
        create_table(engine)
        self.Session = sessionmaker(bind=engine)
        logger.info("****GoogleApisCrawlerPipeline: database connected****")

    def process_item(self, item, spider):
        session = self.Session()
        class_info = ClassInfo()
        class_info.name = item["name"]
        class_info.description = item["description"]
        class_info.page = item["page"]
        try:
            session.add(class_info)
            session.commit()

        except:
            logger.error("Class name : {}\n-----\nClass description : {}\n-----\nClass page {}\n\n\n\n". \
                format(item["name"], item["description"], item["page"]))
            session.rollback()
            raise

        finally:
            session.close()
        return item
