import bcrypt
from config.db_config import get_connection

def verificar_login(username, password):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT PasswordHash, rol FROM Usuarios WHERE Username = ?", (username,))
    row = cursor.fetchone()
    conn.close()
    if row:
        password_hash, rol = row
        # Si el hash parece bcrypt, intenta verificarlo
        if password_hash.startswith("$2b$") or password_hash.startswith("$2a$"):
            try:
                if bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8')):
                    return True, rol
            except Exception:
                pass
        # Si no, compara en texto plano
        if password == password_hash:
            return True, rol
    return False, None

def crear_usuario(username, password, email):
    conn = get_connection()
    cursor = conn.cursor()
    # Aquí deberías hashear la contraseña antes de guardar
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())  # Usa tu función de hash real
    cursor.execute(
        "INSERT INTO Usuarios (Username, PasswordHash, Email, Rol) VALUES (?, ?, ?, ?)",
        (username, hashed_password.decode('utf-8'), email, "usuario")
    )
    conn.commit()
    conn.close()

def obtener_usuarios():
    conn = get_connection()  # Usa tu función de conexión
    cursor = conn.cursor()
    cursor.execute("SELECT Id, Username, Email, Rol FROM Usuarios")
    usuarios = cursor.fetchall()
    conn.close()
    return [(row.Id, row.Username, row.Email, row.Rol) for row in usuarios]

def actualizar_usuario(user_id, username, email, rol, password=None):
    conn = get_connection()  # Usa tu función de conexión
    cursor = conn.cursor()
    if password:  # Si hay nueva contraseña, actualízala
        # Aquí deberías hashear la contraseña antes de guardar
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())  # Usa tu función de hash real
        cursor.execute(
            "UPDATE Usuarios SET Username=?, Email=?, Rol=?, PasswordHash=? WHERE Id=?",
            (username, email, rol, hashed.decode('utf-8'), user_id)
        )
    else:  # Si no, solo actualiza los otros campos
        cursor.execute(
            "UPDATE Usuarios SET Username=?, Email=?, Rol=? WHERE Id=?",
            (username, email, rol, user_id)
        )
    conn.commit()
    conn.close()

def eliminar_usuario(user_id):
    conn = get_connection()  # Usa tu función de conexión
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Usuarios WHERE Id=?", (user_id,))
    conn.commit()
    conn.close()

def obtener_historial():
    conn = get_connection()  # Usa tu función de conexión
    cursor = conn.cursor()
    cursor.execute("SELECT Id, Nombre, Descripcion, Fecha, Hora, UsuarioId, Archivo FROM Historial")
    rows = cursor.fetchall()
    conn.close()
    return [(row.Id, row.Nombre, row.Descripcion, row.Fecha, row.Hora, row.UsuarioId, row.Archivo) for row in rows]

def obtener_historial_usuario(usuario_id):
    conn = get_connection()  # Usa tu función de conexión
    cursor = conn.cursor()
    cursor.execute("SELECT Id, Nombre, Descripcion, Fecha, Hora, UsuarioId, Archivo FROM Historial WHERE UsuarioId=?", (usuario_id,))
    rows = cursor.fetchall()
    conn.close()
    return [(row.Id, row.Nombre, row.Descripcion, row.Fecha, row.Hora, row.UsuarioId, row.Archivo) for row in rows]

def obtener_id_por_username(username):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT Id FROM Usuarios WHERE Username=?", (username,))
    row = cursor.fetchone()
    conn.close()
    return row.Id if row else None

def agregar_historial(nombre, descripcion, fecha, hora, usuario_id, archivo_bin):
    conn = get_connection()  # Usa tu función de conexión
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO Historial (Nombre, Descripcion, Fecha, Hora, UsuarioId, Archivo) VALUES (?, ?, ?, ?, ?, ?)",
        (nombre, descripcion, fecha, hora, usuario_id, archivo_bin)
    )
    conn.commit()
    conn.close()