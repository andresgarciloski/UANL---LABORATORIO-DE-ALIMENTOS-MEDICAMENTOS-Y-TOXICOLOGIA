import bcrypt
from config.db_config import get_connection

def verificar_login(username, password):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT PasswordHash FROM Usuarios WHERE Username = ?", (username,))
    row = cursor.fetchone()
    conn.close()
    if row:
        password_hash = row[0]
        # Comparación directa (solo si las contraseñas están en texto plano)
        if password == password_hash:
            return True
    return False