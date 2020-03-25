from sqlalchemy import create_engine, Column, Table, ForeignKey, MetaData
from sqlalchemy.orm import relation
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import (
    Integer, String, Date, DateTime, Float, Boolean, Text)
from scrapy.utils.project import get_project_settings

Base = declarative_base()


def db_connect():
    """
    Performs database connection using database settings from settings.py.
    Returns sqlalchemy engine instance
    """
    return create_engine(get_project_settings().get("CONNECTION_STRING"))


def create_table(engine):
    Base.metadata.create_all(engine)


class Class(Base):
    __tablename__ = "classes"

    id = Column(Integer, primary_key=True)
    name = Column('name', Text())
    description = Column('description', Text())
    page = Column('page', Text())

    def __init__(self, name, description, page):
        self.name = name
        self.description = description
        self.page = page
    
    def __repr__(self):
        return "Class(%r, %r, %r)" % (self.name, self.description, self.page)

class Method(Base):
    __tablename__ = "methods"

    id = Column(Integer, primary_key=True)
    name = Column('name', Text())
    description = Column('description', Text())
    page = Column('page', Text())
    contained_by = Column(Integer, ForeignKey('classes.id'))
    contained_class = relation("Class", backref='methods', lazy=False)

    def __init__(self, name, description, page):
        self.name = name
        self.description = description
        self.page = page
    
    def __repr__(self):
        return "Method(%r, %r, %r, %r)" % (self.name, self.description, self.page, self.contained_class)