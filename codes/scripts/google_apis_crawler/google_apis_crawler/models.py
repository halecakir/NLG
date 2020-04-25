from sqlalchemy import create_engine, Column, Table, ForeignKey, MetaData
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import (
    Integer, String, Date, DateTime, Float, Boolean, Text)
from scrapy.utils.project import get_project_settings

Base = declarative_base()

CONNECTION_STRING = 'sqlite:////home/huseyinalecakir/NLG/datasets/databases/google_apis.db'

def db_connect():
    """
    Performs database connection using database settings from settings.py.
    Returns sqlalchemy engine instance
    """
    #return create_engine(get_project_settings().get("CONNECTION_STRING"))
    return create_engine(CONNECTION_STRING)

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
    contained_class = relationship("Class", backref='methods', lazy=False)

    def __init__(self, name, description, page):
        self.name = name
        self.description = description
        self.page = page
    
    def __repr__(self):
        return "Method(%r, %r, %r, %r)" % (self.name, self.description, self.page, self.contained_class)


class Description(Base):
    __tablename__ = "descriptions"
    id = Column(Integer, primary_key=True)
    description = Column('description', Text())
    vp = Column('vp', Text())
    description_predict = Column('description_predict', Float())
    vp_predict = Column('vp_predict', Float())

    contained_by = Column(Integer, ForeignKey('methods.id'))
    contained_method = relationship("Method", backref='descriptions', lazy=False)

    def __init__(self, data):
        self.description = data["description"]["str"]
        self.description_predict = data["description"]["prediction"]
        self.vp = data["vp"]["str"]
        self.vp_predict = data["vp"]["prediction"]
    
    def __repr__(self):
        return "Description(%r, %r, %r, %r, %r)" % (self.description, self.description_predict, self.vp, self.vp_predict, self.contained_method)





