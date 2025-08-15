import datetime
import zipfile
import io
import os
import pandas as pd
from core.auth import obtener_historial, importar_registro

def _historial_to_dataframe(historial):
    """Convierte el listado de tuplas de obtener_historial() a DataFrame con columnas conocidas."""
    cols = ["Id", "Nombre", "Descripcion", "Fecha", "Hora", "UsuarioId", "Archivo"]
    df = pd.DataFrame(historial, columns=cols)
    # normalizar columnas y parsear Fecha a datetime (intentar varios formatos)
    df["Fecha_parsed"] = pd.to_datetime(df["Fecha"], errors="coerce")
    return df

def filter_historial_dataframe(df, start_date=None, end_date=None, name_contains=None, user_id=None, ids=None):
    """Aplica filtros al DataFrame y devuelve el filtrado."""
    res = df.copy()
    if start_date is not None:
        sd = pd.to_datetime(start_date, errors="coerce")
        if not pd.isna(sd):
            res = res[res["Fecha_parsed"] >= sd]
    if end_date is not None:
        ed = pd.to_datetime(end_date, errors="coerce")
        if not pd.isna(ed):
            # incluir todo el día si se pasa una fecha sin tiempo
            if ed.time() == datetime.time(0, 0):
                ed = ed + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
            res = res[res["Fecha_parsed"] <= ed]
    if name_contains:
        name_lower = str(name_contains).strip().lower()
        res = res[res["Nombre"].astype(str).str.lower().str.contains(name_lower, na=False)]
    if user_id is not None and user_id != "":
        try:
            uid = int(user_id)
            res = res[res["UsuarioId"] == uid]
        except Exception:
            # si no es int, comparar como string
            res = res[res["UsuarioId"].astype(str) == str(user_id)]
    if ids:
        try:
            ids_list = [int(x) for x in ids]
            res = res[res["Id"].isin(ids_list)]
        except Exception:
            # fallback si vienen como strings compararlos como texto
            res = res[res["Id"].astype(str).isin([str(x) for x in ids])]
    return res

def get_export_preview(start_date=None, end_date=None, name_contains=None, user_id=None, ids=None, sample_rows=10):
    """
    Retorna un dict con resumen de lo que sería exportado siguiendo los filtros:
    { 'count': n, 'sample': [rows as dicts] }
    """
    historial = obtener_historial()
    if not historial:
        return {"count": 0, "sample": []}
    df = _historial_to_dataframe(historial)
    df_filtered = filter_historial_dataframe(df, start_date, end_date, name_contains, user_id, ids)
    sample = df_filtered.head(sample_rows).to_dict(orient="records")
    return {"count": len(df_filtered), "sample": sample}

def export_database_to_zip(output_path: str, start_date=None, end_date=None, name_contains=None, user_id=None, ids=None):
    """
    Exporta el historial (y archivos binarios) a un ZIP en output_path aplicando filtros opcionales:
    - start_date, end_date: aceptan str/fecha; se parsean con pandas.to_datetime
    - name_contains: substring para Nombre (case-insensitive)
    - user_id: filtra UsuarioId
    - ids: lista de ids a exportar (acepta lista de int o strings)
    Retorna dict con resumen: {'registros': n, 'archivos': m, 'path': output_path}
    Lanza excepciones en caso de error.
    """
    if not output_path:
        raise ValueError("output_path es requerido")

    historial = obtener_historial()
    if not historial:
        raise ValueError("No hay registros para exportar")

    df = _historial_to_dataframe(historial)
    df_filtered = filter_historial_dataframe(df, start_date, end_date, name_contains, user_id, ids)

    if df_filtered.empty:
        raise ValueError("No se encontraron registros con los filtros especificados.")

    # Preparar datos y archivos
    data = []
    archivos = []
    for _, row in df_filtered.iterrows():
        Id = row["Id"]
        Nombre = row["Nombre"]
        Descripcion = row["Descripcion"]
        Fecha = row["Fecha"]
        Hora = row["Hora"]
        UsuarioId = row["UsuarioId"]
        Archivo = row["Archivo"]
        archivo_nombre = f"{Id}_{Nombre}.bin" if Archivo else ""
        if Archivo:
            archivos.append((archivo_nombre, Archivo))
        data.append([Id, Nombre, Descripcion, Fecha, Hora, UsuarioId, archivo_nombre])

    df_out = pd.DataFrame(data, columns=["Id", "Nombre", "Descripcion", "Fecha", "Hora", "UsuarioId", "ArchivoNombre"])

    # Escribir ZIP
    with zipfile.ZipFile(output_path, "w") as zf:
        excel_buffer = io.BytesIO()
        df_out.to_excel(excel_buffer, index=False)
        zf.writestr("historial.xlsx", excel_buffer.getvalue())
        for archivo_nombre, archivo_bin in archivos:
            # si archivo_bin es bytes o bytearray
            if archivo_bin:
                if isinstance(archivo_bin, (bytes, bytearray)):
                    zf.writestr(archivo_nombre, archivo_bin)
                elif hasattr(archivo_bin, "read"):
                    # file-like
                    zf.writestr(archivo_nombre, archivo_bin.read())
                else:
                    # intentar str() fallback
                    zf.writestr(archivo_nombre, str(archivo_bin).encode("utf-8"))

    return {"registros": len(df_filtered), "archivos": len(archivos), "path": output_path}

def import_database_from_zip(zip_path: str, import_all=True, overwrite=True):
    """
    Importa registros desde un ZIP exportado por export_database_to_zip.
    - zip_path: ruta del ZIP.
    - import_all: si False podría implementarse filtrado por filas (por ahora importa todo en el Excel)
    - overwrite: si True permite que importar_registro gestione duplicados (depende de implementación)
    Retorna dict con resumen: {'registros_importados': n, 'archivos_importados': m}
    """
    if not zip_path:
        raise ValueError("zip_path es requerido")

    registros_importados = 0
    archivos_importados = 0

    with zipfile.ZipFile(zip_path, "r") as zf:
        # Leer el Excel
        if "historial.xlsx" not in zf.namelist():
            raise ValueError("El ZIP no contiene 'historial.xlsx'")
        excel_data = zf.read("historial.xlsx")
        df = pd.read_excel(io.BytesIO(excel_data))

        for _, row in df.iterrows():
            archivo_bin = None
            if pd.notna(row.get("ArchivoNombre")) and row.get("ArchivoNombre") != "":
                try:
                    archivo_bin = zf.read(row["ArchivoNombre"])
                    archivos_importados += 1
                except KeyError:
                    archivo_bin = None
            # importar registro (puede lanzar)
            importar_registro(
                row["Nombre"],
                row["Descripcion"],
                row["Fecha"],
                row["Hora"],
                row["UsuarioId"],
                archivo_bin
            )
            registros_importados += 1

    return {"registros_importados": registros_importados, "archivos_importados": archivos_importados}