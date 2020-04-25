import sys
sys.path.insert(0, "/home/huseyinalecakir/NLG/codes/scripts/google_apis_crawler")

from google_apis_crawler.models import Class, Method, db_connect, create_table, Description
from sqlalchemy.orm import sessionmaker

import pandas as pd

engine = db_connect()
create_table(engine)
Session = sessionmaker(bind=engine)
session = Session()

ResultProxy = session.execute("SELECT * FROM descriptions")
ResultSet = ResultProxy.fetchall()

df_descriptions = pd.DataFrame(ResultSet)
df_descriptions.columns = ResultSet[0].keys()


ResultProxy = session.execute("SELECT * FROM methods")
ResultSet = ResultProxy.fetchall()

df_methods = pd.DataFrame(ResultSet)
df_methods.columns = ResultSet[0].keys()


df_concat = pd.concat([df_descriptions.set_index('contained_by'), df_methods.set_index('id')], axis=1, join='inner').reset_index()

df_concat.sort_values(by=['vp_predict'], ascending=False).to_excel("descriptions_sorted_by_vp.xlsx")
df_concat.sort_values(by=['description_predict'], ascending=False).to_excel("descriptions_sorted_by_description.xlsx")
