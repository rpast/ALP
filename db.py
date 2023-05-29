import sqlite3
import pandas as pd

# connect with database
conn = sqlite3.connect('./static/data/dbs/app.db')

#pointer
c = conn.cursor()

# read list of tables
c.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = c.fetchall()

# read session table with pandas
session_df = pd.read_sql_query("SELECT * FROM session", conn)

# read context table with pandas
collections_df = pd.read_sql_query("SELECT * FROM collections", conn)
