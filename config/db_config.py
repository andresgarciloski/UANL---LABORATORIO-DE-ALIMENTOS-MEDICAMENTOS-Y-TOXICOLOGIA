import pyodbc

# Configuración del servidor
server = 'LATITUDE-3540\\SQLEXPRESS'      
database = 'FCQ'  
username = 'root'    
password = 'Fime2025'  
driver = 'ODBC Driver 17 for SQL Server'  

# Cadena de conexión para autenticación SQL
conn_str = (
    f'DRIVER={{{driver}}};'
    f'SERVER={server};'
    f'DATABASE={database};'
    f'UID={username};'
    f'PWD={password}'
)

# Función auxiliar para obtener la cadena de conexión
def get_connection_string():
    return conn_str

# Función para obtener la conexión directamente
def get_connection():
    return pyodbc.connect(conn_str)