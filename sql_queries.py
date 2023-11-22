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
	r.name as region,
    case when f.fund = 0 then 'FAM1' when f.fund =1 then 'FAM2' when f.fund =2 then 'FAM3' when f.fund =3 then 'FAM4'
    when f.fund =4 then 'Inland' when f.fund =5 then 'RDH II' when f.fund =6 then 'RDH III' when f.fund =7 then 'RDH IV'
    when f.fund =8 then 'SPH' 
    when f.fund =9 then 'FAM5' end as fund 
from facilities f 
		left join regions r on r.id = f.region_id ;
'''
