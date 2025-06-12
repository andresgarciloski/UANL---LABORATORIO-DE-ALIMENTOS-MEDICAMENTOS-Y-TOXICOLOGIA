import pyodbc

def get_connection():
    server = 'LATITUDE-3540\\SQLEXPRESS'      
    database = 'FCQ'  
    username = 'root'    
    password = 'Fime2025'  
    driver = 'ODBC Driver 17 for SQL Server'  

    conn_str = (
        f'DRIVER={{{driver}}};'
        f'SERVER={server};'
        f'DATABASE={database};'
        f'UID={username};'
        f'PWD={password}'
    )
    return pyodbc.connect(conn_str)