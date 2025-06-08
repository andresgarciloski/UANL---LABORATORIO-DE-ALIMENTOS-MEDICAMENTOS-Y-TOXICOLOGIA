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
        # Si el hash parece bcrypt, intenta verificarlo
        if password_hash.startswith("$2b$") or password_hash.startswith("$2a$"):
            try:
                if bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8')):
                    return True
            except Exception:
                pass
        # Si no, compara en texto plano
        if password == password_hash:
            return True
    return False

def crear_usuario(username, password, email=None):
    conn = get_connection()
    cursor = conn.cursor()
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    cursor.execute(
        "INSERT INTO Usuarios (Username, PasswordHash, Email) VALUES (?, ?, ?)",
        (username, hashed.decode('utf-8'), email)
    )
    conn.commit()
    conn.close()