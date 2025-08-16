import re
from typing import List, Tuple, Callable, Optional, Any

# Funciones de acceso a BD / autenticación que ya existen en core.auth
from core.auth import (
    obtener_historial,
    obtener_historial_usuario,
    obtener_historial_completo_admin,
    obtener_username_por_id,
    eliminar_historial,
    importar_registro,
)

def fetch_historial(role: str = "usuario", get_usuario_id: Optional[Callable[[], Any]] = None) -> List[Tuple]:
    """
    Obtiene el historial según el rol:
    - role == "admin": intenta obtener obtener_historial_completo_admin() o fallback a obtener_historial()
    - role != "admin": requiere get_usuario_id callable y usa obtener_historial_usuario(usuario_id)
    Retorna lista de tuplas (Id, Nombre, Descripcion, Fecha, Hora, UsuarioId, Archivo)
    """
    try:
        if role == "admin":
            try:
                return obtener_historial_completo_admin()
            except Exception:
                return obtener_historial()
        else:
            if get_usuario_id is None:
                raise ValueError("Se requiere get_usuario_id para usuarios no-admin")
            usuario_id = get_usuario_id()
            if usuario_id is None:
                return []
            return obtener_historial_usuario(usuario_id)
    except Exception:
        # En caso de error con la BD, devolver lista vacía para que la UI lo maneje
        return []

def filter_historial(historial: List[Tuple], nombre: Optional[str] = None, fecha: Optional[str] = None, usuario_filter: Optional[str] = None) -> List[Tuple]:
    """
    Filtra la lista de tuplas del historial por nombre, fecha exacta (string) y/o usuario.
    - nombre: substring case-insensitive en campo Nombre
    - fecha: compara str(Fecha) == fecha (mantengo la lógica existente)
    - usuario_filter: substring en UsuarioId convertido a str
    """
    if not historial:
        return []
    filtrado = []
    for item in historial:
        try:
            if len(item) < 6:
                continue
            Id, Nombre, Descripcion, Fecha, Hora, UsuarioId, *rest = item
            if nombre and nombre.strip():
                if nombre.strip().lower() not in str(Nombre).lower():
                    continue
            if fecha and fecha.strip():
                if str(Fecha) != fecha.strip():
                    continue
            if usuario_filter and usuario_filter.strip():
                if usuario_filter.strip().lower() not in str(UsuarioId).lower():
                    continue
            filtrado.append(item)
        except Exception:
            continue
    return filtrado

def get_suggested_filename(nombre: Optional[str], archivo_bin: Optional[bytes]) -> str:
    """
    Provee un nombre de archivo sugerido (limpio) basado en 'nombre' y el contenido binario.
    Determina extensión por encabezado (PDF, XLSX/ZIP) y limpia caracteres inválidos.
    """
    safe_name = "archivo"
    try:
        if nombre and str(nombre).strip():
            safe_name = "".join(c for c in str(nombre).strip() if c.isalnum() or c in (' ', '-', '_', '.')).rstrip()
            if not safe_name:
                safe_name = "archivo"
    except Exception:
        safe_name = "archivo"

    ext = ".bin"
    try:
        if archivo_bin and isinstance(archivo_bin, (bytes, bytearray)) and len(archivo_bin) >= 4:
            head = archivo_bin[:4]
            if head.startswith(b'%PDF'):
                ext = ".pdf"
            elif head.startswith(b'PK'):
                ext = ".xlsx"
            else:
                # Try simple heuristics for common formats
                if archivo_bin[:2] == b'\x1f\x8b':
                    ext = ".gz"
                else:
                    ext = ".bin"
    except Exception:
        ext = ".bin"

    # Asegurar que el nombre termine con la extensión correcta
    if not safe_name.lower().endswith(ext):
        safe_name = safe_name + ext
    return safe_name

def save_binary_to_path(archivo_bin: bytes, path: str) -> None:
    """Guarda bytes en la ruta indicada; lanza excepciones si falla."""
    with open(path, "wb") as f:
        f.write(archivo_bin)

def delete_historial_record(id_hist: Any) -> None:
    """Wrapper para eliminar registro del historial en la capa de datos."""
    try:
        eliminar_historial(id_hist)
    except Exception as e:
        raise

def get_username_by_id(usuario_id: Any) -> str:
    """Obtiene el username por id o devuelve texto por defecto si falla."""
    try:
        name = obtener_username_por_id(usuario_id)
        return name if name else f"Usuario {usuario_id}"
    except Exception:
        return f"Usuario {usuario_id}"