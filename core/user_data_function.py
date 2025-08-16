import pyodbc
import hashlib
import sys
from config.db_config import get_connection  # Usamos get_connection

def get_user_data(username):
    """
    Obtiene los datos del usuario por su nombre de usuario.
    Retorna: diccionario con datos del usuario o None si no se encuentra.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        query = """
        SELECT Id, Username, Email, Rol, CreatedAt
        FROM Usuarios
        WHERE Username = ?
        """
        cursor.execute(query, (username,))
        row = cursor.fetchone()
        
        if row:
            user_data = {
                'id': row[0],
                'username': row[1],
                'email': row[2] if row[2] else '',
                'rol': row[3],
                'createdAt': row[4] if len(row) > 4 else None,
                # Valores vacíos para los campos que no existen pero son usados en la UI
                'nombre': '',
                'apellido': '',
                'telefono': ''
            }
            return user_data
        return None
    except Exception as e:
        print(f"Error al obtener datos de usuario: {e}")
        return None
    finally:
        try:
            cursor.close()
            conn.close()
        except:
            pass

def update_user_profile(user_id, nombre, apellido, email, telefono, current_password=None, new_password=None):
    """
    Actualiza los datos del perfil de usuario.
    Si se proporciona contraseña actual y nueva, también actualiza la contraseña.
    Retorna: (éxito, mensaje)
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Si hay cambio de contraseña, verificar la actual
        if current_password and new_password:
            # Verificar contraseña actual
            verify_query = "SELECT PasswordHash FROM Usuarios WHERE Id = ?"  # Cambiado a PasswordHash
            cursor.execute(verify_query, (user_id,))
            stored_password = cursor.fetchone()
            
            if not stored_password:
                return False, "Usuario no encontrado."
            
            # Hashear la contraseña proporcionada y comparar
            hashed_current = hashlib.sha256(current_password.encode()).hexdigest()
            if hashed_current != stored_password[0]:
                return False, "La contraseña actual no es correcta."
            
            # Hashear la nueva contraseña
            hashed_new = hashlib.sha256(new_password.encode()).hexdigest()
            
            # Actualizar solo email y password (las únicas columnas existentes)
            update_query = """
            UPDATE Usuarios 
            SET Email = ?, PasswordHash = ?
            WHERE Id = ?
            """
            cursor.execute(update_query, (email, hashed_new, user_id))
        else:
            # Actualizar solo el email (la única columna que existe de las que intentamos actualizar)
            update_query = """
            UPDATE Usuarios 
            SET Email = ?
            WHERE Id = ?
            """
            cursor.execute(update_query, (email, user_id))
        
        conn.commit()
        return True, "Perfil actualizado correctamente."
        
    except Exception as e:
        print(f"Error al actualizar perfil: {e}")
        return False, f"Error al actualizar perfil: {e}"
    finally:
        try:
            cursor.close()
            conn.close()
        except:
            pass

def validate_current_password(user_id, current_password):
    """
    Valida si la contraseña proporcionada coincide con la almacenada.
    Retorna: True si coincide, False en caso contrario.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        query = "SELECT PasswordHash FROM Usuarios WHERE Id = ?"  # Cambiado a PasswordHash
        cursor.execute(query, (user_id,))
        stored_password = cursor.fetchone()
        
        if not stored_password:
            return False
        
        hashed_current = hashlib.sha256(current_password.encode()).hexdigest()
        return hashed_current == stored_password[0]
        
    except Exception as e:
        print(f"Error al validar contraseña: {e}")
        return False
    finally:
        try:
            cursor.close()
            conn.close()
        except:
            pass