import tkinter as tk
from tkinter import messagebox, filedialog
import datetime
import os
import pandas as pd
from core.auth import agregar_historial
from ui.base_interface import bind_mousewheel

class NutrimentalModule:
    def __init__(self, parent_window):
        self.parent = parent_window

    def show_nutrimental_section(self):
        """Mostrar sección de tabla nutrimental"""
        # Limpiar contenido
        for widget in self.parent.content_frame.winfo_children():
            widget.destroy()

        title = tk.Label(
            self.parent.content_frame,
            text="Tabla Nutrimental Mexicana",
            font=("Segoe UI", 20, "bold"),
            bg="white",
            fg="#0B5394"
        )
        title.pack(pady=(30, 20))

        # Frame principal con scroll
        main_frame = tk.Frame(self.parent.content_frame, bg="white")
        main_frame.pack(expand=True, fill="both", padx=30, pady=20)

        # Canvas para scroll
        canvas = tk.Canvas(main_frame, bg="white")
        scrollbar = tk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="white")

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Campos básicos
        self._create_basic_fields(scrollable_frame)
        
        # Datos nutricionales
        self._create_nutrimental_fields(scrollable_frame)
        
        # Botones
        self._create_buttons(scrollable_frame)
        
        # Resultados
        self._create_results_area(scrollable_frame)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        bind_mousewheel(canvas, canvas)

    def _create_basic_fields(self, parent):
        """Crear campos básicos"""
        basic_frame = tk.LabelFrame(parent, text="Información Básica", font=("Segoe UI", 12, "bold"), bg="white", fg="#0B5394")
        basic_frame.pack(fill="x", pady=(0, 20), padx=10)

        # # de muestra
        tk.Label(basic_frame, text="# de muestra:", bg="white", font=("Segoe UI", 10)).grid(row=0, column=0, sticky="w", padx=10, pady=5)
        self.parent.nombre_entry = tk.Entry(basic_frame, font=("Segoe UI", 10), width=40)
        self.parent.nombre_entry.grid(row=0, column=1, padx=10, pady=5, sticky="ew")

        # Descripción
        tk.Label(basic_frame, text="Descripción:", bg="white", font=("Segoe UI", 10)).grid(row=1, column=0, sticky="w", padx=10, pady=5)
        self.parent.descripcion_entry = tk.Text(basic_frame, font=("Segoe UI", 10), width=40, height=3)
        self.parent.descripcion_entry.grid(row=1, column=1, padx=10, pady=5, sticky="ew")

        # Fecha automática
        tk.Label(basic_frame, text="Fecha:", bg="white", font=("Segoe UI", 10)).grid(row=2, column=0, sticky="w", padx=10, pady=5)
        self.parent.fecha_entry = tk.Entry(basic_frame, font=("Segoe UI", 10), width=20, state="readonly", bg="#f0f0f0")
        fecha_actual = datetime.datetime.now().strftime("%Y-%m-%d")
        self.parent.fecha_entry.config(state="normal")
        self.parent.fecha_entry.insert(0, fecha_actual)
        self.parent.fecha_entry.config(state="readonly")
        self.parent.fecha_entry.grid(row=2, column=1, padx=10, pady=5, sticky="w")

        # Hora automática
        tk.Label(basic_frame, text="Hora:", bg="white", font=("Segoe UI", 10)).grid(row=3, column=0, sticky="w", padx=10, pady=5)
        self.parent.hora_entry = tk.Entry(basic_frame, font=("Segoe UI", 10), width=20, state="readonly", bg="#f0f0f0")
        hora_actual = datetime.datetime.now().strftime("%H:%M:%S")
        self.parent.hora_entry.config(state="normal")
        self.parent.hora_entry.insert(0, hora_actual)
        self.parent.hora_entry.config(state="readonly")
        self.parent.hora_entry.grid(row=3, column=1, padx=10, pady=5, sticky="w")

        basic_frame.grid_columnconfigure(1, weight=1)

    def _create_nutrimental_fields(self, parent):
        """Crear campos nutricionales"""
        nutri_frame = tk.LabelFrame(parent, text="Datos Nutricionales", font=("Segoe UI", 12, "bold"), bg="white", fg="#0B5394")
        nutri_frame.pack(fill="x", pady=(0, 20), padx=10)

        # Variables para los campos nutricionales
        self.parent.nutri_vars = {}
        nutri_fields = [
            ("humedad", "Humedad (%)", ""),
            ("cenizas", "Cenizas (%)", ""),
            ("proteina", "Proteína (%)", ""),
            ("grasa_total", "Grasa total (%)", ""),
            ("grasa_trans", "Grasas Trans (mg/100g)", ""),
            ("fibra_dietetica", "Fibra dietética (%)", ""),
            ("azucares", "Azúcares totales (%)", ""),
            ("azucares_anadidos", "Azúcares añadidos (%)", ""),
            ("sodio", "Sodio (mg/100g)", ""),
            ("acidos_grasos_saturados", "Ácidos grasos saturados (%)", ""),
            ("porcion", "Tamaño de porción (g o mL)", ""),
            ("contenido_neto", "Contenido neto del envase (opcional)", "")
        ]

        row = 0
        col = 0
        for key, label, placeholder in nutri_fields:
            tk.Label(nutri_frame, text=label + ":", bg="white", font=("Segoe UI", 10)).grid(row=row, column=col*2, sticky="w", padx=10, pady=5)
            entry = tk.Entry(nutri_frame, font=("Segoe UI", 10), width=15)
            if placeholder:
                entry.insert(0, placeholder)
            entry.grid(row=row, column=col*2+1, padx=10, pady=5, sticky="ew")
            self.parent.nutri_vars[key] = entry
            
            col += 1
            if col >= 2:
                col = 0
                row += 1

        nutri_frame.grid_columnconfigure(1, weight=1)
        nutri_frame.grid_columnconfigure(3, weight=1)

    def _create_buttons(self, parent):
        """Crear botones"""
        buttons_frame = tk.Frame(parent, bg="white")
        buttons_frame.pack(fill="x", pady=20, padx=10)

        tk.Button(
            buttons_frame,
            text="Calcular Tabla Nutrimental",
            command=self.calcular_tabla_nutrimental,
            bg="#0B5394",
            fg="white",
            font=("Segoe UI", 12, "bold"),
            relief="flat",
            padx=20,
            pady=10,
            cursor="hand2"
        ).pack(side="left", padx=(0, 10))

        tk.Button(
            buttons_frame,
            text="Exportar a Excel",
            command=self.exportar_nutrimental_excel,
            bg="#28a745",
            fg="white",
            font=("Segoe UI", 12, "bold"),
            relief="flat",
            padx=20,
            pady=10,
            cursor="hand2"
        ).pack(side="left", padx=10)

    def _create_results_area(self, parent):
        """Crear área de resultados"""
        self.parent.resultados_frame = tk.LabelFrame(parent, text="Resultados", font=("Segoe UI", 12, "bold"), bg="white", fg="#0B5394")
        self.parent.resultados_frame.pack(fill="both", expand=True, pady=(20, 0), padx=10)

        self.parent.resultados_text = tk.Text(self.parent.resultados_frame, font=("Courier New", 10), bg="#f8f9fa", state="disabled")
        resultados_scroll = tk.Scrollbar(self.parent.resultados_frame, orient="vertical", command=self.parent.resultados_text.yview)
        self.parent.resultados_text.configure(yscrollcommand=resultados_scroll.set)

        self.parent.resultados_text.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        resultados_scroll.pack(side="right", fill="y", pady=10)

    def calcular_tabla_nutrimental(self):
        """Calcular tabla nutrimental"""
        try:
            # Obtener valores de los campos
            data = {}
            for key, entry in self.parent.nutri_vars.items():
                value = entry.get().strip()
                if value and key != "contenido_neto":
                    data[key] = float(value)
                elif value and key == "contenido_neto":
                    data[key] = float(value) if value else None

            # Campos requeridos
            required_fields = [
                "humedad", "cenizas", "proteina", "grasa_total", "grasa_trans", 
                "fibra_dietetica", "azucares", "azucares_anadidos", "sodio", 
                "acidos_grasos_saturados", "porcion"
            ]
            for field in required_fields:
                if field not in data:
                    field_name = field.replace('_', ' ').title()
                    messagebox.showerror("Error", f"El campo '{field_name}' es requerido")
                    return

            # Cálculos
            resultados = self._calcular_nutrimental(data)
            
            # Mostrar resultados
            self._mostrar_resultados(resultados)
            
            # Guardar para exportar
            self.parent.ultimo_calculo = {
                "datos_basicos": {
                    "nombre": self.parent.nombre_entry.get(),
                    "descripcion": self.parent.descripcion_entry.get("1.0", "end-1c"),
                    "fecha": self.parent.fecha_entry.get(),
                    "hora": self.parent.hora_entry.get()
                },
                "datos_entrada": data,
                "resultados": resultados
            }

        except ValueError:
            messagebox.showerror("Error", "Por favor ingrese valores numéricos válidos")
        except Exception as e:
            messagebox.showerror("Error", f"Error en el cálculo: {str(e)}")

    def _calcular_nutrimental(self, data):
        """Realizar cálculos nutricionales"""
        # No redondear los valores de entrada - mantener decimales para cálculos
        proteina = data["proteina"]
        grasa_total = data["grasa_total"]
        azucares = data["azucares"]
        azucares_anadidos = data["azucares_anadidos"]
        fibra_dietetica = data["fibra_dietetica"]
        
        # Cálculos derivados
        grasa_saturada = grasa_total * (data["acidos_grasos_saturados"] / 100)
        grasa_trans_g = data["grasa_trans"] / 1000  # Convertir mg a g para cálculos
        
        # Hidratos de carbono totales
        hidratos_carbono_totales = 100 - (data["humedad"] + data["cenizas"] + proteina + grasa_total)
        
        # Carbohidratos disponibles
        carbohidratos_disponibles = hidratos_carbono_totales - fibra_dietetica
        
        # Por 100g
        por_100g = {
            "proteina": round(proteina),
            "grasa_total": round(grasa_total),
            "grasa_saturada": round(grasa_saturada),
            "grasa_trans": self._aplicar_regla_redondeo_sodio(data["grasa_trans"]),
            "carbohidratos_disponibles": round(carbohidratos_disponibles),
            "azucares": round(azucares),
            "azucares_anadidos": round(azucares_anadidos),
            "fibra_dietetica": round(fibra_dietetica),
            "sodio": self._aplicar_regla_redondeo_sodio(data["sodio"]),
            "energia_kcal": 0,
            "energia_kj": 0
        }
        
        # Calcular energía
        energia_kcal_100g = (por_100g["proteina"] + por_100g["carbohidratos_disponibles"]) * 4 + por_100g["grasa_total"] * 9
        energia_kj_100g = (por_100g["proteina"] + por_100g["carbohidratos_disponibles"]) * 17 + por_100g["grasa_total"] * 37
        
        por_100g["energia_kcal"] = round(energia_kcal_100g)
        por_100g["energia_kj"] = round(energia_kj_100g)
        
        # Por porción
        proteina_porcion = (proteina * data["porcion"]) / 100
        grasa_total_porcion = (grasa_total * data["porcion"]) / 100
        grasa_saturada_porcion = (grasa_saturada * data["porcion"]) / 100
        grasa_trans_porcion = (data["grasa_trans"] * data["porcion"]) / 100
        carbohidratos_disponibles_porcion = (carbohidratos_disponibles * data["porcion"]) / 100
        azucares_porcion = (azucares * data["porcion"]) / 100
        azucares_anadidos_porcion = (azucares_anadidos * data["porcion"]) / 100
        fibra_dietetica_porcion = (fibra_dietetica * data["porcion"]) / 100
        sodio_porcion = (data["sodio"] * data["porcion"]) / 100
        
        por_porcion = {
            "proteina": round(proteina_porcion),
            "grasa_total": round(grasa_total_porcion),
            "grasa_saturada": round(grasa_saturada_porcion),
            "grasa_trans": self._aplicar_regla_redondeo_sodio(grasa_trans_porcion),
            "carbohidratos_disponibles": round(carbohidratos_disponibles_porcion),
            "azucares": round(azucares_porcion),
            "azucares_anadidos": round(azucares_anadidos_porcion),
            "fibra_dietetica": round(fibra_dietetica_porcion),
            "sodio": self._aplicar_regla_redondeo_sodio(sodio_porcion),
            "energia_kcal": 0,
            "energia_kj": 0
        }
        
        # Calcular energía por porción
        energia_kcal_porcion = (por_porcion["proteina"] + por_porcion["carbohidratos_disponibles"]) * 4 + por_porcion["grasa_total"] * 9
        energia_kj_porcion = (por_porcion["proteina"] + por_porcion["carbohidratos_disponibles"]) * 17 + por_porcion["grasa_total"] * 37
        
        por_porcion["energia_kcal"] = round(energia_kcal_porcion)
        por_porcion["energia_kj"] = round(energia_kj_porcion)
        
        resultados = {
            "por_100g": por_100g,
            "por_porcion": por_porcion
        }
        
        # Por envase (si se especifica)
        if "contenido_neto" in data and data["contenido_neto"]:
            factor_cn = data["contenido_neto"] / 100
            resultados["por_envase"] = {
                "energia_kcal": round(por_100g["energia_kcal"] * factor_cn),
                "energia_kj": round(por_100g["energia_kj"] * factor_cn)
            }
    
        return resultados

    def _aplicar_regla_redondeo_sodio(self, valor):
        """Aplicar reglas de redondeo para sodio y grasas trans"""
        if valor < 5:
            return 0
        elif valor <= 140:
            return round(valor / 5) * 5
        else:
            return round(valor / 10) * 10

    def _mostrar_resultados(self, resultados):
        """Mostrar resultados en el área de texto"""
        self.parent.resultados_text.config(state="normal")
        self.parent.resultados_text.delete("1.0", "end")
        
        texto = "TABLA NUTRIMENTAL MEXICANA\n"
        texto += "=" * 50 + "\n\n"
        
        # Por 100g
        texto += "POR 100g/mL:\n"
        texto += "-" * 20 + "\n"
        for key, value in resultados["por_100g"].items():
            if key == "energia_kcal":
                texto += f"Contenido energético: {value} kcal\n"
            elif key == "energia_kj":
                texto += f"Contenido energético: {value} kJ\n"
            elif key == "sodio":
                texto += f"Sodio: {value} mg\n"
            elif key == "grasa_trans":
                texto += f"Grasas Trans: {value} mg\n"
            else:
                texto += f"{key.replace('_', ' ').title()}: {value} g\n"
        texto += "\n"
        
        # Por porción
        texto += "POR PORCIÓN:\n"
        texto += "-" * 20 + "\n"
        for key, value in resultados["por_porcion"].items():
            if key == "energia_kcal":
                texto += f"Contenido energético: {value} kcal\n"
            elif key == "energia_kj":
                texto += f"Contenido energético: {value} kJ\n"
            elif key == "sodio":
                texto += f"Sodio: {value} mg\n"
            elif key == "grasa_trans":
                texto += f"Grasas Trans: {value} mg\n"
            else:
                texto += f"{key.replace('_', ' ').title()}: {value} g\n"
        texto += "\n"
        
        # Por envase
        if "por_envase" in resultados:
            texto += "POR ENVASE:\n"
            texto += "-" * 20 + "\n"
            for key, value in resultados["por_envase"].items():
                if key == "energia_kcal":
                    texto += f"Contenido energético: {value} kcal\n"
                elif key == "energia_kj":
                    texto += f"Contenido energético: {value} kJ\n"
                else:
                    texto += f"{key.replace('_', ' ').title()}: {value}\n"

        self.parent.resultados_text.insert("1.0", texto)
        self.parent.resultados_text.config(state="disabled")

    def exportar_nutrimental_excel(self):
        """Exportar tabla nutrimental a Excel"""
        if not hasattr(self.parent, "ultimo_calculo"):
            messagebox.showwarning("Advertencia", "Primero debe calcular la tabla nutrimental")
            return
        
        try:
            # Obtener valores actuales
            nombre_actual = self.parent.nombre_entry.get().strip()
            descripcion_actual = self.parent.descripcion_entry.get("1.0", "end-1c").strip()
            
            if not nombre_actual:
                messagebox.showerror("Error", "El campo '# de muestra' es obligatorio para exportar")
                self.parent.nombre_entry.focus()
                return
            
            # Generar nombre de archivo
            fecha_actual = datetime.datetime.now()
            nombre_limpio = "".join(c for c in nombre_actual if c.isalnum() or c in (' ', '-', '_')).rstrip()
            nombre_limpio = nombre_limpio.replace(' ', '_')
            if not nombre_limpio:
                nombre_limpio = "Tabla_Nutrimental"
            
            timestamp = fecha_actual.strftime("%Y-%m-%d_%H%M%S")
            nombre_predeterminado = f"{nombre_limpio}_{timestamp}.xlsx"
            
            # Preparar datos para Excel
            datos_excel = []
            
            # Información básica
            datos_excel.append(["INFORMACIÓN BÁSICA", "", ""])
            datos_excel.append(["# de muestra", nombre_actual, ""])
            datos_excel.append(["Descripción", descripcion_actual, ""])
            datos_excel.append(["Fecha de análisis", fecha_actual.strftime("%Y-%m-%d"), ""])
            datos_excel.append(["Hora de análisis", fecha_actual.strftime("%H:%M:%S"), ""])
            datos_excel.append(["Usuario", self.parent.username, ""])
            datos_excel.append(["Fecha de exportación", fecha_actual.strftime("%Y-%m-%d %H:%M:%S"), ""])
            datos_excel.append(["", "", ""])
            
            # Datos de entrada
            datos_excel.append(["DATOS DE ENTRADA", "", ""])
            for key, value in self.parent.ultimo_calculo["datos_entrada"].items():
                nombre_campo = key.replace('_', ' ').title()
                if key == "sodio":
                    datos_excel.append([f"{nombre_campo} (mg/100g)", value, ""])
                elif key == "grasa_trans":
                    datos_excel.append([f"{nombre_campo} (mg/100g)", value, ""])
                elif key == "porcion":
                    datos_excel.append([f"{nombre_campo} (g)", value, ""])
                elif key == "contenido_neto":
                    datos_excel.append([f"{nombre_campo} (g/mL)", value, ""])
                else:
                    datos_excel.append([f"{nombre_campo} (%)", value, ""])
            datos_excel.append(["", "", ""])
            
            # Tabla nutrimental
            datos_excel.append(["TABLA NUTRIMENTAL MEXICANA", "Por 100g/mL", "Por Porción"])
            resultados = self.parent.ultimo_calculo["resultados"]
            
            for key in resultados["por_100g"].keys():
                if key == "energia_kcal":
                    nombre = "Contenido energético (kcal)"
                elif key == "energia_kj":
                    nombre = "Contenido energético (kJ)"
                elif key == "sodio":
                    nombre = "Sodio (mg)"
                elif key == "grasa_trans":
                    nombre = "Grasas Trans (mg)"
                else:
                    nombre = f"{key.replace('_', ' ').title()} (g)"
                    
                valor_100g = resultados["por_100g"][key]
                valor_porcion = resultados["por_porcion"][key]
                datos_excel.append([nombre, valor_100g, valor_porcion])
            
            # Por envase si existe
            if "por_envase" in resultados:
                datos_excel.append(["", "", ""])
                datos_excel.append(["POR ENVASE COMPLETO", "", ""])
                for key, value in resultados["por_envase"].items():
                    if key == "energia_kcal":
                        nombre = "Contenido energético total (kcal)"
                    elif key == "energia_kj":
                        nombre = "Contenido energético total (kJ)"
                    else:
                        nombre = f"{key.replace('_', ' ').title()}"
                    datos_excel.append([nombre, value, ""])
            
            # Crear DataFrame
            df = pd.DataFrame(datos_excel, columns=["Componente", "Valor 100g/mL", "Valor Porción"])
            
            # Ubicación de descarga
            try:
                desktop = os.path.join(os.path.expanduser("~"), "Desktop")
                if not os.path.exists(desktop):
                    desktop = os.path.expanduser("~")
            except:
                desktop = ""
            
            # Guardar archivo
            filename = filedialog.asksaveasfilename(
                initialfile=nombre_predeterminado,
                initialdir=desktop,
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
                title="Guardar tabla nutrimental"
            )
            
            if filename:
                # Crear archivo Excel
                with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False, sheet_name="Tabla Nutrimental")
                    
                    workbook = writer.book
                    worksheet = writer.sheets["Tabla Nutrimental"]
                    
                    # Ajustar ancho de columnas
                    worksheet.column_dimensions['A'].width = 30
                    worksheet.column_dimensions['B'].width = 15
                    worksheet.column_dimensions['C'].width = 15
                
                # Leer archivo para base de datos
                with open(filename, "rb") as f:
                    archivo_binario = f.read()
                
                # Guardar en base de datos
                usuario_id = self.parent.get_usuario_id()
                
                if usuario_id is None:
                    messagebox.showwarning("Advertencia", "No se pudo guardar en la base de datos: Usuario no válido")
                    return
                
                # Descripción completa
                descripcion_completa = f"{descripcion_actual}\n\n"
                descripcion_completa += "DATOS NUTRICIONALES CALCULADOS:\n"
                descripcion_completa += f"- Proteína: {resultados['por_100g']['proteina']}g/100g\n"
                descripcion_completa += f"- Grasa total: {resultados['por_100g']['grasa_total']}g/100g\n"
                descripcion_completa += f"- Carbohidratos disponibles: {resultados['por_100g']['carbohidratos_disponibles']}g/100g\n"
                descripcion_completa += f"- Energía: {resultados['por_100g']['energia_kcal']} kcal/100g\n"
                descripcion_completa += f"- Tamaño de porción analizada: {self.parent.ultimo_calculo['datos_entrada']['porcion']}g\n"
                descripcion_completa += f"Archivo Excel generado automáticamente: {os.path.basename(filename)}"
                
                agregar_historial(
                    nombre_actual,
                    descripcion_completa,
                    fecha_actual.strftime("%Y-%m-%d"),
                    fecha_actual.strftime("%H:%M:%S"),
                    usuario_id,
                    archivo_binario
                )
                
                messagebox.showinfo(
                    "Exportación Exitosa", 
                    f"✅ Tabla nutrimental exportada correctamente:\n\n"
                    f"📁 Archivo: {os.path.basename(filename)}\n"
                    f"📂 Ubicación: {filename}\n"
                    f"💾 Guardado en base de datos: ✓\n"
                    f"👤 Usuario: {self.parent.username}\n"
                    f"📝 # de muestra: {nombre_actual}\n\n"
                )
            else:
                messagebox.showinfo("Cancelado", "Exportación cancelada por el usuario.")
        
        except ImportError:
            messagebox.showerror("Error", "No se pudo importar pandas. Asegúrate de que esté instalado:\npip install pandas openpyxl")
        except Exception as e:
            messagebox.showerror("Error", f"Error al exportar: {str(e)}")