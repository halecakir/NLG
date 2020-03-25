# -*- coding: utf-8 -*-
from sqlalchemy.orm import sessionmaker
from scrapy.exceptions import DropItem
from google_apis_crawler.models import Class, Method, db_connect, create_table
from google_apis_crawler.logger import logger


class GoogleApisCrawlerPipeline(object):
    def __init__(self):
        engine = db_connect()
        create_table(engine)
        self.Session = sessionmaker(bind=engine)
        logger.info("****GoogleApisCrawlerPipeline: database connected****")

    def process_item(self, item, spider):
        session = self.Session()
        class_ = Class(item["name"], item["description"], item["page"])
        for method in item["methods"].keys():
            m = Method(method, item["methods"][method]["description"], item["methods"][method]["page"])
            class_.methods.append(m)
        try:
            session.add(class_)
            session.commit()

        except:
            logger.error(class_)
            session.rollback()
            raise

        finally:
            session.close()
        return item
