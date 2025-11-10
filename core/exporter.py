import os
import tempfile
import datetime
from tkinter import messagebox, filedialog
from openpyxl import load_workbook
from openpyxl.drawing.image import Image as XLImage
from openpyxl.utils.units import pixels_to_EMU
from openpyxl.utils.cell import coordinate_from_string, column_index_from_string
from core.auth import agregar_historial
import pandas as pd
from openpyxl.styles import Alignment, Font

def escribir_celda_segura(ws, coord, valor):
    """Escribe en una celda asegurando que, si está dentro de un rango merged, se escriba en la celda superior izquierda."""
    if not isinstance(coord, str):
        try:
            coord = coord.coordinate
        except Exception:
            coord = str(coord)
    for rango in ws.merged_cells.ranges:
        if coord in rango:
            ws.cell(row=rango.min_row, column=rango.min_col).value = valor
            return
    ws[coord] = valor

def _alinear_derecha_seguro(ws, coord):
    """Aplica alineación derecha (y vertical centrada) respetando celdas combinadas."""
    if not isinstance(coord, str):
        try:
            coord = coord.coordinate
        except Exception:
            coord = str(coord)
    for rango in ws.merged_cells.ranges:
        if coord in rango:
            c = ws.cell(row=rango.min_row, column=rango.min_col)
            c.alignment = Alignment(horizontal="right", vertical="center", indent=0, wrap_text=False, shrinkToFit=False)
            return
    ws[coord].alignment = Alignment(horizontal="right", vertical="center", indent=0, wrap_text=False, shrinkToFit=False)

def _alinear_izquierda_seguro(ws, coord):
    """Aplica alineación izquierda (y vertical centrada) respetando celdas combinadas."""
    if not isinstance(coord, str):
        try:
            coord = coord.coordinate
        except Exception:
            coord = str(coord)
    for rango in ws.merged_cells.ranges:
        if coord in rango:
            c = ws.cell(row=rango.min_row, column=rango.min_col)
            c.alignment = Alignment(horizontal="left", vertical="center", indent=0, wrap_text=False, shrinkToFit=False)
            return
    ws[coord].alignment = Alignment(horizontal="left", vertical="center", indent=0, wrap_text=False, shrinkToFit=False)

def _sanitize_filename(name: str) -> str:
    """Quitar caracteres inválidos y espacios duplicados para filenames."""
    keep = "-_.() abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    cleaned = "".join(c for c in name if c in keep)
    cleaned = "_".join(part for part in cleaned.split() if part)
    return cleaned.strip("_") or "archivo"

def _add_stamp(ws, img_path: str, cell: str, w_px: int = 48, h_px: int = 48):
    """Inserta una imagen anclada a una celda (compatible con todas las versiones)."""
    try:
        img = XLImage(img_path)
        img.width = w_px
        img.height = h_px
        img.anchor = cell   # anclaje simple sin OneCellAnchor
        ws.add_image(img)
    except Exception as e:
        print(f"[exporter] fallo al insertar imagen {img_path}: {e}")

def _excel_width_from_px(px: int) -> float:
    """Convierte píxeles a unidades de ancho de columna de Excel (~ px = width*7 + 5)."""
    return max(0.0, (float(px) - 5.0) / 7.0)

def _set_equal_column_widths(ws, columns, target_px: int):
    """Fija el mismo ancho en píxeles para un conjunto de columnas."""
    try:
        width_units = _excel_width_from_px(target_px)
        for c in columns:
            ws.column_dimensions[c].width = width_units
    except Exception:
        pass

def _apply_energy_style(ws, coord, size=11):
    """Fuente un poco más grande para energía y shrinkToFit, manteniendo derecha/centro."""
    if not isinstance(coord, str):
        try:
            coord = coord.coordinate
        except Exception:
            coord = str(coord)
    for rango in ws.merged_cells.ranges:
        if coord in rango:
            cell = ws.cell(row=rango.min_row, column=rango.min_col)
            break
    else:
        cell = ws[coord]
    f = cell.font or Font()
    cell.font = Font(
        name=f.name, size=size, bold=f.bold, italic=f.italic, vertAlign=f.vertAlign,
        underline=f.underline, strike=f.strike, color=f.color
    )
    # Igual alineación que los demás: derecha y centrado vertical
    cell.alignment = Alignment(horizontal="right", vertical="center", indent=0, shrinkToFit=True, wrap_text=False)

class NutrimentalExporter:
    def __init__(self, parent_window):
        self.parent = parent_window

    def agregar_sellos_advertencia(self, ws, resultados):
        """Inserta imágenes de sellos en celdas específicas del template siguiendo info2.txt.
        Las imágenes se colocan con tamaño mayor al de las celdas pero no modifican
        el alto/ancho de filas/columnas del libro (se superponen)."""
        # Obtener flags desde la UI si están disponibles
        es_liquida = False
        es_bebida_sin_calorias = False
        try:
            tipo_var = getattr(self.parent, "tipo_muestra", None)
            if tipo_var is not None and tipo_var.get() == "liquida":
                es_liquida = True
        except Exception:
            es_liquida = False
        try:
            beb_var = getattr(self.parent, "bebida_sin_calorias", None)
            if beb_var is not None and beb_var.get():
                es_bebida_sin_calorias = True
        except Exception:
            es_bebida_sin_calorias = False

        por100 = resultados.get("por_100g", {})

        # Valores esperados
        calorias = float(por100.get("energia_kcal", 0) or 0)
        azucares_g = float(por100.get("azucares", 0) or 0)
        grasa_sat_g = float(por100.get("grasa_saturada", 0) or 0)
        grasa_trans_mg = float(por100.get("grasa_trans", 0) or 0)
        sodio_mg = float(por100.get("sodio", 0) or 0)

        # Calcular sellos según info2.txt
        sellos = {
            "exceso_calorias": False,
            "exceso_azucares": False,
            "exceso_grasas_saturadas": False,
            "exceso_grasas_trans": False,
            "exceso_sodio": False
        }

        # EXCESO CALORÍAS
        if es_liquida:
            if calorias >= 70:
                sellos["exceso_calorias"] = True
        else:
            if calorias >= 275:
                sellos["exceso_calorias"] = True
        if (azucares_g * 4) >= 8:
            sellos["exceso_calorias"] = True

        # EXCESO AZÚCARES (azucares_g * 4 >= 10% de kcal)
        if calorias > 0 and (azucares_g * 4) >= (0.10 * calorias):
            sellos["exceso_azucares"] = True

        # EXCESO GRASAS SATURADAS (grasa_sat_g * 9 >= 10% de kcal)
        if calorias > 0 and (grasa_sat_g * 9) >= (0.10 * calorias):
            sellos["exceso_grasas_saturadas"] = True

        # EXCESO GRASAS TRANS (grasa_trans_mg /1000 *9 >= 1% de kcal)
        if calorias > 0:
            energia_trans_kcal = (grasa_trans_mg / 1000.0) * 9.0
            if energia_trans_kcal >= (0.01 * calorias):
                sellos["exceso_grasas_trans"] = True

        # EXCESO SODIO (>=300 mg OR mg sodio >= kcal OR bebida sin calorías >=45 mg)
        if sodio_mg >= 300:
            sellos["exceso_sodio"] = True
        elif calorias >= 0 and sodio_mg >= calorias:
            sellos["exceso_sodio"] = True
        elif es_bebida_sin_calorias and sodio_mg >= 45:
            sellos["exceso_sodio"] = True

        # Mapeo de sello -> imagen y celda (todas contiguas)
        project_root = os.path.dirname(os.path.dirname(__file__))
        ruta_base = os.path.abspath(os.path.join(project_root, "img", "Sellos"))

        # Calcular un tamaño uniforme que quepa en las columnas M–Q (sin tocar la plantilla)
        def _col_px(letter: str) -> int:
            # ancho en unidades Excel -> píxeles aprox (width*7 + 5)
            try:
                width = ws.column_dimensions[letter].width
            except Exception:
                width = None
            if width in (None, 0):
                width = ws.sheet_format.defaultColWidth or 8.43
            return int(round(width * 7 + 5))

        try:
            # columnas donde se colocan los 5 sellos: M, O, Q, S, U
            col_letters = ["M", "O", "Q", "S", "U"]
            min_col_px = min(_col_px(c) for c in col_letters)
            GAP_INNER = 4  # margen interno más pequeño
            base_side = max(64, min(140, min_col_px - GAP_INNER * 2))
            # hacerlos un poco más grandes sin tocar celdas
            side = min(180, int(round(base_side * 1.20)))
            STAMP_SIZE = (side, side)
        except Exception:
            STAMP_SIZE = (144, 144)  # fallback un poco mayor

        # Orden requerido: calorías, azúcares, grasas saturadas, grasa trans, sodio
        # Celdas en orden izquierda→derecha: M18, O18, Q18, S18, U18
        sellos_config = [
            ("exceso_calorias",         {"imagen": "calorias.jpg",  "celda": "L18", "size": STAMP_SIZE}),
            ("exceso_azucares",         {"imagen": "azucares.jpg",  "celda": "N18", "size": STAMP_SIZE}),
            ("exceso_grasas_saturadas", {"imagen": "saturadas.jpg", "celda": "P18", "size": STAMP_SIZE}),
            ("exceso_grasas_trans",     {"imagen": "trans.jpg",     "celda": "R18", "size": STAMP_SIZE}),
            ("exceso_sodio",            {"imagen": "sodio.jpg",     "celda": "T18", "size": STAMP_SIZE}),
        ]

        # No modificar anchos/altos de filas/columnas; solo superponer imágenes más grandes
        # (Se deja el ancho original de las columnas M–Q)

        # Inserción de imágenes
        ruta_base = os.path.join(os.path.dirname(__file__), "..", "img", "Sellos")
        for key, cfg in sellos_config:
            try:
                if not sellos.get(key):
                    continue
                ruta = os.path.join(ruta_base, cfg["imagen"])
                if not os.path.exists(ruta):
                    print(f"[exporter] imagen no encontrada: {ruta}")
                    continue
                cell = cfg["celda"]
                w, h = cfg.get("size", (48, 48))
                _add_stamp(ws, ruta, cell, w_px=w, h_px=h)
            except Exception as e:
                print(f"[exporter] fallo al insertar imagen {cfg.get('imagen','?')}: {e}")

    def llenar_plantilla_excel(self, wb, resultados, entrada, datos_basicos, formato_100: bool = False):
        ws = wb.active
        # Determinar unidad automática: "mL" si es líquida, "g" si es sólida (fallback a "g")
        unidad = "g"
        tipo_var = getattr(self.parent, "tipo_muestra", None)
        try:
            if tipo_var is not None and tipo_var.get() == "liquida":
                unidad = "mL"
        except Exception:
            unidad = "g"

        # Añadir unidad a G20 (alineado a la izquierda)
        escribir_celda_segura(ws, "G20", unidad)
        _alinear_izquierda_seguro(ws, "G20")
        
        # El resto del código existente...
        # Tamaño de porción con unidad en F17 (escribe sólo la celda destino)
        porcion_val = entrada.get("porcion", "")
        escribir_celda_segura(ws, "F17", f"{porcion_val}" if porcion_val != "" else "")
        _alinear_derecha_seguro(ws, "F17")
        escribir_celda_segura(ws, "G17", unidad if porcion_val != "" else "")
        _alinear_izquierda_seguro(ws, "G17")

        # Porciones por envase en F18 (sin unidad para coincidir con vista previa)
        porciones_envase = resultados.get("porciones_envase", None)
        if porciones_envase is not None and porciones_envase != "":
            try:
                pv = float(porciones_envase)
                porciones_display = int(pv) if pv.is_integer() else round(pv, 1)
            except Exception:
                porciones_display = porciones_envase
            escribir_celda_segura(ws, "F18", f"{porciones_display}")
            _alinear_derecha_seguro(ws, "F18")  # <-- NUEVO
            _alinear_izquierda_seguro(ws, "G18")  # Mantener consistente con las otras filas
        else:
            escribir_celda_segura(ws, "F18", "")
            _alinear_derecha_seguro(ws, "F18")
            _alinear_izquierda_seguro(ws, "G18")

        # Contenido energético por envase en F19 (mismo tamaño que el resto; solo derecha)
        env = resultados.get('por_envase', {}) or {}
        energia_envase_fmt = ""
        try:
            kcal_env = env.get('energia_kcal', '')
            kj_env = env.get('energia_kj', '')
            if str(kcal_env) != "":
                energia_envase_fmt = self._fmt_kcal_kj(kcal_env, kj_env)
        except Exception:
            energia_envase_fmt = ""
        escribir_celda_segura(ws, "F19", energia_envase_fmt)
        _alinear_derecha_seguro(ws, "F19")  # misma alineación que los demás
        escribir_celda_segura(ws, "G19", "")
        _alinear_izquierda_seguro(ws, "G19")

        contenido_neto = entrada.get("contenido_neto", "")
        escribir_celda_segura(ws, "F12", f"{contenido_neto} {unidad}" if contenido_neto != "" else "")

        # Nombre y descripción
        escribir_celda_segura(ws, "C8", f"{datos_basicos.get('nombre','')} - {datos_basicos.get('descripcion','')}")
        # También en N8
        escribir_celda_segura(ws, "N8", f"{datos_basicos.get('nombre','')} - {datos_basicos.get('descripcion','')}")

        # Mapeo valores por 100g (siempre) y por porción (solo si formato_100 == False)
        m = resultados.get("por_100g", {})
        p = resultados.get("por_porcion", {})

        # Escribir energía combinada en una sola celda y vaciar la celda de unidad
        mappings_100 = [
            ("F21", self._fmt_kcal_kj(m.get("energia_kcal",""), m.get("energia_kj","")), "G21", ""),
            ("F22", m.get("proteina", ""), "G22", "g"),
            ("F23", m.get("grasa_total", ""), "G23", "g"),
            ("F24", m.get("grasa_saturada", ""), "G24", "g"),
            ("F25", m.get("grasa_trans", ""), "G25", "mg"),
            ("F26", m.get("carbohidratos_disponibles", ""), "G26", "g"),
            ("F27", m.get("azucares", ""), "G27", "g"),
            ("F28", m.get("azucares_anadidos", ""), "G28", "g"),
            ("F29", m.get("fibra_dietetica", ""), "G29", "g"),
            ("F30", m.get("sodio", ""), "G30", "mg"),
        ]
        mappings_porcion = [
            ("H21", self._fmt_kcal_kj(p.get("energia_kcal",""), p.get("energia_kj","")), "I21", ""),
            ("H22", p.get("proteina", ""), "I22", "g"),
            ("H23", p.get("grasa_total", ""), "I23", "g"),
            ("H24", p.get("grasa_saturada", ""), "I24", "g"),
            ("H25", p.get("grasa_trans", ""), "I25", "mg"),
            ("H26", p.get("carbohidratos_disponibles", ""), "I26", "g"),
            ("H27", p.get("azucares", ""), "I27", "g"),
            ("H28", p.get("azucares_anadidos", ""), "I28", "g"),
            ("H29", p.get("fibra_dietetica", ""), "I29", "g"),
            ("H30", p.get("sodio", ""), "I30", "mg"),
        ]

        def _as_int_str(v):
            try:
                return str(int(float(v)))
            except Exception:
                return v if v is not None else ""

        # Escribir siempre los valores por 100g
        for cel_val_100, val100, cel_unit, unit in mappings_100:
            val_fmt = _as_int_str(val100)
            escribir_celda_segura(ws, cel_val_100, val_fmt)
            try:
                ws[cel_val_100].number_format = '@' if isinstance(val100, str) else '0'
            except Exception:
                pass
            _alinear_derecha_seguro(ws, cel_val_100)
            if cel_val_100 == "F21":
                _apply_energy_style(ws, "F21", size=11)  # más grande y ajusta para que no se corte
            try:
                ws[cel_unit] = unit
            except Exception:
                pass

        # Porción (si aplica)
        if not formato_100:
            for cel_val_p, valp, cel_unit_p, unitp in mappings_porcion:
                valp_fmt = _as_int_str(valp)
                escribir_celda_segura(ws, cel_val_p, valp_fmt)
                try:
                    ws[cel_val_p].number_format = '@' if isinstance(valp, str) else '0'
                except Exception:
                    pass
                _alinear_derecha_seguro(ws, cel_val_p)
                if cel_val_p == "H21":
                    _apply_energy_style(ws, "H21", size=11)  # más grande y ajusta para que no se corte
                try:
                    ws[cel_unit_p] = unitp
                except Exception:
                    pass
        else:
            for cel_val_p, _, cel_unit_p, _ in mappings_porcion:
                escribir_celda_segura(ws, cel_val_p, "")
                try: ws[cel_val_p].number_format = '@'
                except Exception: pass
                try: ws[cel_unit_p] = ""
                except Exception: pass

        # Agregar sellos de advertencia (usa cálculo en nutrimental.py)
        self.agregar_sellos_advertencia(ws, resultados)
        return wb

    def generar_pdf_desde_excel(self, wb, nombre_archivo, guardar_dialogo=True):
        """Genera PDF usando Excel COM; incluye initialfile en el diálogo de guardado."""
        tmp_excel_path = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
                wb.save(tmp.name)
                tmp_excel_path = tmp.name

            try:
                import win32com.client
            except ImportError:
                raise ImportError("win32com no disponible. Instale pywin32 para exportar a PDF desde Excel en Windows.")

            excel = win32com.client.Dispatch("Excel.Application")
            excel.Visible = False
            wb_x = excel.Workbooks.Open(tmp_excel_path)

            if guardar_dialogo:
                # incluir nombre sugerido en initialfile
                ruta_guardado_pdf = filedialog.asksaveasfilename(
                    defaultextension=".pdf",
                    initialfile=nombre_archivo,
                    filetypes=[("PDF","*.pdf")]
                )
                if not ruta_guardado_pdf:
                    wb_x.Close(False)
                    excel.Quit()
                    return None, "Cancelado"
            else:
                ruta_guardado_pdf = os.path.join(tempfile.gettempdir(), nombre_archivo)

            wb_x.ExportAsFixedFormat(0, ruta_guardado_pdf)
            wb_x.Close(False)
            excel.Quit()

            with open(ruta_guardado_pdf, "rb") as f:
                contenido = f.read()
            return contenido, ruta_guardado_pdf

        finally:
            if tmp_excel_path and os.path.exists(tmp_excel_path):
                try:
                    os.remove(tmp_excel_path)
                except Exception:
                    pass

    def exportar_a_formato_predefinido(self):
        """Exporta usando plantilla y sugiere un nombre estandarizado según datos ingresadas."""
        if not hasattr(self.parent, "ultimo_calculo"):
            messagebox.showwarning("Advertencia", "Primero debe calcular la tabla nutrimental")
            return
        try:
            # elegir plantilla: si porción == 100 usar formato100.xlsx
            entrada = self.parent.ultimo_calculo["datos_entrada"]
            porcion_val = entrada.get("porcion", "")
            formato_100_flag = False
            try:
                pv = float(porcion_val)
                if pv == 100.0:
                    formato_100_flag = True
            except Exception:
                formato_100_flag = False
            plantilla_name = "formato100.xlsx" if formato_100_flag else "formato.xlsx"
            plantilla = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "templates", plantilla_name))
            if not os.path.exists(plantilla):
                raise FileNotFoundError(f"Plantilla no encontrada: {plantilla}")
            wb = load_workbook(plantilla)
            resultados = self.parent.ultimo_calculo["resultados"]
            entrada = self.parent.ultimo_calculo["datos_entrada"]
            datos_basicos = self.parent.ultimo_calculo["datos_basicos"]

            # Generar nombre recomendado estandarizado
            nombre_raw = datos_basicos.get("nombre", "muestra")
            nombre_limpio = _sanitize_filename(str(nombre_raw))
            tipo = "liquida" if getattr(self.parent, "tipo_muestra", None) and self.parent.tipo_muestra.get() == "liquida" else "solida"
            # unidad y porcion (sin decimales si es entero)
            unidad = "mL" if tipo == "liquida" else "g"
            porcion_val = entrada.get("porcion", "")
            try:
                pv = float(porcion_val)
                porcion_str = str(int(pv)) if pv.is_integer() else str(pv).replace(".", "_")
            except Exception:
                porcion_str = _sanitize_filename(str(porcion_val))
            fecha = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            recommended = f"{nombre_limpio}_{tipo}_{porcion_str}{unidad}_{fecha}.pdf"
            recommended = _sanitize_filename(recommended)

            wb = self.llenar_plantilla_excel(wb, resultados, entrada, datos_basicos, formato_100=formato_100_flag)

            # pasar el nombre recomendado a la función que muestra el diálogo
            _, ruta = self.generar_pdf_desde_excel(wb, recommended, True)
            if ruta != "Cancelado":
                messagebox.showinfo("Éxito", f"Archivo PDF exportado correctamente:\n\n{ruta}")
        except FileNotFoundError:
            messagebox.showerror("Error", "No se encontró la plantilla formato.xlsx.")
        except ImportError as ie:
            messagebox.showwarning("PDF no generado", str(ie))
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo completar la exportación:\n{e}")

    def guardar_solo_bd(self):
        if not hasattr(self.parent, "ultimo_calculo"):
            messagebox.showwarning("Advertencia", "Primero debe calcular la tabla nutrimental")
            return
        try:
            nombre_actual = self.parent.nombre_entry.get().strip()
            descripcion_actual = self.parent.descripcion_entry.get("1.0", "end-1c").strip()
            if not nombre_actual:
                messagebox.showerror("Error", "El campo '# de muestra' es obligatorio para guardar")
                self.parent.nombre_entry.focus()
                return
            usuario_id = self.parent.get_usuario_id()
            if usuario_id is None:
                messagebox.showwarning("Advertencia", "No se pudo guardar en la base de datos: Usuario no válido")
                return
            # elegir plantilla: si porción == 100 usar formato100.xlsx
            entrada = self.parent.ultimo_calculo["datos_entrada"]
            porcion_val = entrada.get("porcion", "")
            formato_100_flag = False
            try:
                pv = float(porcion_val)
                if pv == 100.0:
                    formato_100_flag = True
            except Exception:
                formato_100_flag = False
            plantilla_name = "formato100.xlsx" if formato_100_flag else "formato.xlsx"
            plantilla = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "templates", plantilla_name))
            if not os.path.exists(plantilla):
                raise FileNotFoundError(f"Plantilla no encontrada: {plantilla}")
            wb = load_workbook(plantilla)
            resultados = self.parent.ultimo_calculo["resultados"]
            entrada = self.parent.ultimo_calculo["datos_entrada"]
            datos_basicos = self.parent.ultimo_calculo["datos_basicos"]
            wb = self.llenar_plantilla_excel(wb, resultados, entrada, datos_basicos, formato_100=formato_100_flag)
            fecha = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            nombre_pdf = f"nutrimental_{nombre_actual}_{fecha}.pdf"
            archivo_binario, _ = self.generar_pdf_desde_excel(wb, nombre_pdf, False)
            if not archivo_binario:
                messagebox.showwarning("Advertencia", "No se pudo generar el PDF para la base de datos.")
                return
            fecha_actual = datetime.datetime.now()
            descripcion_completa = f"{descripcion_actual}\n\nTABLA NUTRIMENTAL OFICIAL (PDF):\n"
            descripcion_completa += f"- Proteína: {resultados['por_100g'].get('proteina','')}g/100g\n"
            descripcion_completa += f"- Grasa total: {resultados['por_100g'].get('grasa_total','')}g/100g\n"
            descripcion_completa += f"- Carbohidratos disponibles: {resultados['por_100g'].get('carbohidratos_disponibles','')}g/100g\n"
            descripcion_completa += f"- Energía: {resultados['por_100g'].get('energia_kcal','')} kcal/100g\n"
            descripcion_completa += f"- Tamaño de porción: {entrada.get('porcion','')}g\n"
            descripcion_completa += f"- Contenido neto: {entrada.get('contenido_neto','No especificado')}\n"
            descripcion_completa += f"Archivo PDF formato oficial generado el {fecha_actual.strftime('%d/%m/%Y %H:%M:%S')}"
            agregar_historial(
                nombre_actual,
                descripcion_completa,
                fecha_actual.strftime("%Y-%m-%d"),
                fecha_actual.strftime("%H:%M:%S"),
                usuario_id,
                archivo_binario
            )
            messagebox.showinfo("Guardado en Base de Datos", "PDF nutrimental guardado correctamente en la base de datos.")
        except FileNotFoundError:
            messagebox.showerror("Error", "No se encontró la plantilla formato.xlsx.")
        except ImportError as ie:
            messagebox.showwarning("PDF no generado", str(ie))
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo completar la exportación:\n{e}")

    def exportar_nutrimental_excel(self):
        if not hasattr(self.parent, "ultimo_calculo"):
            messagebox.showwarning("Advertencia", "Primero debe calcular la tabla nutrimental")
            return
        try:
            nombre_actual = self.parent.nombre_entry.get().strip()
            descripcion_actual = self.parent.descripcion_entry.get("1.0", "end-1c").strip()
            if not nombre_actual:
                messagebox.showerror("Error", "El campo '# de muestra' es obligatorio para exportar")
                self.parent.nombre_entry.focus()
                return
            fecha_actual = datetime.datetime.now()
            nombre_limpio = "".join(c for c in nombre_actual if c.isalnum() or c in (' ', '-', '_')).rstrip().replace(' ','_') or "Tabla_Nutrimental"
            timestamp = fecha_actual.strftime("%Y-%m-%d_%H%M%S")
            nombre_predeterminado = f"{nombre_limpio}_{timestamp}.xlsx"

            # Determinar encabezado según tipo de muestra
            tipo_var = getattr(self.parent, "tipo_muestra", None)
            try:
                es_liquida = (tipo_var is not None and tipo_var.get() == "liquida")
            except Exception:
                es_liquida = False
            header_por100 = "Por 100 mL" if es_liquida else "Por 100 g"

            datos_excel = []
            datos_excel.append(["INFORMACIÓN BÁSICA","",""])
            datos_excel.append(["# de muestra", nombre_actual, ""])
            datos_excel.append(["Descripción", descripcion_actual, ""])
            datos_excel.append(["Fecha de análisis", fecha_actual.strftime("%Y-%m-%d"), ""])
            datos_excel.append(["Hora de análisis", fecha_actual.strftime("%H:%M:%S"), ""])
            datos_excel.append(["Usuario", getattr(self.parent, "username", ""), ""])
            datos_excel.append(["Fecha de exportación", fecha_actual.strftime("%Y-%m-%d %H:%M:%S"), ""])
            datos_excel.append(["","",""])
            datos_excel.append(["DATOS DE ENTRADA","",""])
            for key, value in self.parent.ultimo_calculo["datos_entrada"].items():
                nombre_campo = key.replace('_',' ').title()
                if key in ("sodio","grasa_trans"):
                    unidad_entrada = f"mg/{'100 mL' if es_liquida else '100 g'}"
                    datos_excel.append([f"{nombre_campo} ({unidad_entrada})", value, ""])
                elif key == "porcion":
                    unidad_porcion = "mL" if es_liquida else "g"
                    datos_excel.append([f"{nombre_campo} ({unidad_porcion})", value, ""])
                elif key == "contenido_neto":
                    unidad_cn = "mL" if es_liquida else "g"
                    datos_excel.append([f"{nombre_campo} ({unidad_cn})", value, ""])
                else:
                    unidad_pct = f"%/{'100 mL' if es_liquida else '100 g'}"
                    datos_excel.append([f"{nombre_campo} ({unidad_pct})", value, ""])
            datos_excel.append(["","",""])
            datos_excel.append(["TABLA NUTRIMENTAL MEXICANA", header_por100, "Por Porción"])
            resultados = self.parent.ultimo_calculo["resultados"]
            if "porciones_envase" in resultados and resultados["porciones_envase"] is not None:
                # Formato igual que en la vista: entero si es entero, 1 decimal si no
                try:
                    pv = float(resultados["porciones_envase"])
                    pv_display = int(pv) if pv.is_integer() else round(pv, 1)
                except Exception:
                    pv_display = resultados["porciones_envase"]
                datos_excel.append(["Porciones por envase", pv_display, ""])

            # Fila combinada de energía
            energia_100 = self._fmt_kcal_kj(
                resultados["por_100g"].get("energia_kcal", 0),
                resultados["por_100g"].get("energia_kj", 0)
            )
            energia_por = self._fmt_kcal_kj(
                resultados["por_porcion"].get("energia_kcal", 0),
                resultados["por_porcion"].get("energia_kj", 0)
            )
            datos_excel.append(["Contenido energético", energia_100, energia_por])

            # Resto de nutrimentos (sin energía)
            def _cast_int(v):
                try: return int(float(v))
                except Exception: return v

            orden = [
                ("Proteínas", "proteina", "g"),
                ("Grasas totales", "grasa_total", "g"),
                ("Grasas saturadas", "grasa_saturada", "g"),
                ("Grasas trans", "grasa_trans", "mg"),
                ("Hidratos de carbono disponibles", "carbohidratos_disponibles", "g"),
                ("Azúcares", "azucares", "g"),
                ("Azúcares añadidos", "azucares_anadidos", "g"),
                ("Fibra dietética", "fibra_dietetica", "g"),
                ("Sodio", "sodio", "mg"),
            ]
            for nombre, key, unidad in orden:
                v100 = _cast_int(resultados["por_100g"].get(key, ""))
                vpor = _cast_int(resultados["por_porcion"].get(key, ""))
                datos_excel.append([f"{nombre} ({unidad})", v100, vpor])

            if "por_envase" in resultados:
                datos_excel.append(["","",""]); datos_excel.append(["POR ENVASE COMPLETO","",""])
                env = resultados["por_envase"] or {}
                energia_env = self._fmt_kcal_kj(env.get("energia_kcal", 0), env.get("energia_kj", 0))
                datos_excel.append(["Contenido energético total", energia_env, ""])
            datos_excel.append(["","",""]); datos_excel.append(["SELLOS DE ADVERTENCIA","",""])
            sellos = {}
            calc = getattr(self.parent, "_calcular_sellos_advertencia", None)
            if callable(calc):
                sellos = calc(resultados)
            # Forzar el orden: calorías, azúcares, grasas saturadas, grasa trans, sodio
            orden_sellos = [
                "exceso_calorias",
                "exceso_azucares",
                "exceso_grasas_saturadas",
                "exceso_grasas_trans",
                "exceso_sodio",
            ]
            for sello in orden_sellos:
                if sello in sellos:
                    aplica = sellos[sello]
                    nombre_sello = sello.replace("exceso_", "EXCESO DE ").upper()
                    datos_excel.append([nombre_sello, "SÍ" if aplica else "NO", ""])
            # Cualquier sello extra no contemplado
            for sello, aplica in sellos.items():
                if sello not in orden_sellos:
                    nombre_sello = sello.replace("exceso_", "EXCESO DE ").upper()
                    datos_excel.append([nombre_sello, "SÍ" if aplica else "NO", ""])
            df = pd.DataFrame(datos_excel, columns=["Componente","Valor 100g/mL","Valor Porción"])
            try:
                desktop = os.path.join(os.path.expanduser("~"), "Desktop")
                if not os.path.exists(desktop):
                    desktop = os.path.expanduser("~")
            except:
                desktop = ""
            filename = filedialog.asksaveasfilename(initialfile=nombre_predeterminado, initialdir=desktop, defaultextension=".xlsx", filetypes=[("Excel files","*.xlsx"),("All files","*.*")], title="Guardar tabla nutrimental")
            if filename:
                with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False, sheet_name="Tabla Nutrimental")
                    workbook = writer.book
                    worksheet = writer.sheets["Tabla Nutrimental"]
                    worksheet.column_dimensions['A'].width = 30
                    worksheet.column_dimensions['B'].width = 15
                    worksheet.column_dimensions['C'].width = 15
                # YA NO se guarda el archivo Excel en la base de datos para evitar
                # almacenar formatos que no son el oficial (PDF). El guardado en BD
                # debe hacerse únicamente mediante 'guardar_solo_bd' que genera PDF.
                messagebox.showinfo(
                    "Exportación Exitosa",
                    f"Tabla nutrimental exportada en Excel (solo archivo local).\n\n📁 Archivo: {os.path.basename(filename)}\n📂 Ubicación: {filename}\n\nPara guardar en la base de datos en formato PDF use 'Guardar en base de datos'."
                )
            else:
                messagebox.showinfo("Cancelado", "Exportación cancelada por el usuario.")
        except ImportError:
            messagebox.showerror("Error", "No se pudo importar pandas. Asegúrate de que esté instalado:\npip install pandas openpyxl")
        except Exception as e:
            messagebox.showerror("Error", f"Error al exportar: {e}")

    def _fmt_kcal_kj(self, kcal, kj):
        try:
            ikcal = int(float(kcal))
        except Exception:
            ikcal = 0
        try:
            ikj = int(float(kj))
        except Exception:
            ikj = 0
        return f"{ikcal} kcal ({ikj} kJ)"

    # Ejemplo: cuando construyes las filas para el PDF
    def _build_rows(self, resultados):
        por100 = resultados.get('por_100g', {}) or {}
        porcion = resultados.get('por_porcion', {}) if not resultados.get('es_porcion_100g', False) else None

        rows = []
        # --- Contenido energético combinado en una sola fila ---
        energia_100 = self._fmt_kcal_kj(por100.get('energia_kcal', 0), por100.get('energia_kj', 0))
        if porcion:
            energia_por = self._fmt_kcal_kj(porcion.get('energia_kcal', 0), porcion.get('energia_kj', 0))
            rows.append(("Contenido energético", energia_100, energia_por))
        else:
            rows.append(("Contenido energético", energia_100))

        # Resto de nutrimentos como números
        def _int(v):
            try: return int(float(v))
            except Exception: return 0

        def add_row(nombre, key, unidad=""):
            v100 = _int(por100.get(key, 0))
            if porcion:
                vpor = _int(porcion.get(key, 0))
                rows.append((f"{nombre} {unidad}".strip(), v100, vpor))
            else:
                rows.append((f"{nombre} {unidad}".strip(), v100))

        add_row("Proteína", "proteina", "(g)")
        add_row("Grasa total", "grasa_total", "(g)")
        add_row("Grasa saturada", "grasa_saturada", "(g)")
        add_row("Grasas trans", "grasa_trans", "(mg)")
        add_row("Carbohidratos disponibles", "carbohidratos_disponibles", "(g)")
        add_row("Azúcares", "azucares", "(g)")
        add_row("Azúcares añadidos", "azucares_anadidos", "(g)")
        add_row("Fibra dietética", "fibra_dietetica", "(g)")
        add_row("Sodio", "sodio", "(mg)")

        return rows

    # Ejemplo: donde pintas el encabezado/metadata en el PDF
    def _render_header(self, resultados, canvas):
        # ...existing code...
        env = resultados.get('por_envase', {}) or {}
        if env:
            energia_envase = self._fmt_kcal_kj(env.get('energia_kcal', 0), env.get('energia_kj', 0))
            linea = f"Energía total envase: {energia_envase}"
            # Dibuja esta línea con tu motor actual (reportlab/canvas, etc.)
            # ...existing code...