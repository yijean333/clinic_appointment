import pyodbc

def get_connection():
    conn = pyodbc.connect(
        'DRIVER={ODBC Driver 18 for SQL Server};'
        'SERVER=LAPTOP-41R5E87J\\SQLEXPRESS;'
        'DATABASE=appointment_db;' 
        'UID=Jane;PWD=0927;'
        'TrustServerCertificate=yes;'
    )
    return conn
