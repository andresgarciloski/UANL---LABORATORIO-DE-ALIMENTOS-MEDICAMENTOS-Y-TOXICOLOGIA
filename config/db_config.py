import pyodbc

def get_connection():
    server = 'LATITUDE-3540\\SQLEXPRESS'      # Cambia por el nombre o IP de tu servidor SQL
    database = 'FCQ'  # Cambia por el nombre de tu base de datos
    username = 'root'     # Cambia por tu usuario
    password = 'Fime2025'  # Cambia por tu contraseña
    driver = 'ODBC Driver 17 for SQL Server'  # Asegúrate de tener este driver instalado

    conn_str = (
        f'DRIVER={{{driver}}};'
        f'SERVER={server};'
        f'DATABASE={database};'
        f'UID={username};'
        f'PWD={password}'
    )
    return pyodbc.connect(conn_str)