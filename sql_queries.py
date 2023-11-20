import psycopg2 
import pandas as pd
import streamlit as st

HOST = st.secrets["POSTGRES_HOST"]
DB = st.secrets["POSTGRES_DB"]
PORT = st.secrets["POSTGRES_PORT"]
USER = st.secrets["POSTGRES_USER"]
PASSWORD = st.secrets["POSTGRES_PASSWORD"]


def get_sql_connection():
    conn = psycopg2.connect(
        host=HOST,
        database=DB,
        port=PORT,
        user=USER,
        password=PASSWORD
    )

    return conn 

st.cache(ttl=60*60*24)
def run_sql_query(sql_query):
    conn = get_sql_connection()
    df = pd.read_sql_query(sql_query, conn)
    conn.close()
    
    return df 

facilities_sql = '''
select 
	f.site_code,
	r.name as region
from facilities f 
		left join regions r on r.id = f.region_id ;
'''
