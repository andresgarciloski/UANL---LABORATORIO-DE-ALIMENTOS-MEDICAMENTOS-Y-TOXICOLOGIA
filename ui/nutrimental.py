import tkinter as tk
from tkinter import messagebox
import datetime
import os
import pandas as pd
from PIL import Image, ImageDraw, ImageTk
from core.auth import agregar_historial
from ui.base_interface import bind_mousewheel
import tempfile
from core.exporter import NutrimentalExporter  # solo el exportador, no la lógica de sellos

class NutrimentalModule:
    def __init__(self, parent_window):
        self.parent = parent_window
        self.exporter = NutrimentalExporter(parent_window)

    def show_nutrimental_section(self):
        """Interfaz: mantiene solo layout y llamadas a cálculo / visualización"""
        for widget in self.parent.content_frame.winfo_children():
            widget.destroy()

        main_frame = tk.Frame(self.parent.content_frame, bg="#f4f8fc", bd=0)
        main_frame.pack(expand=True, fill="both", padx=20, pady=(5,20))

        canvas = tk.Canvas(main_frame, bg="#f4f8fc", highlightthickness=0)
        scrollbar = tk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        scrollable_frame = tk.Frame(canvas, bg="#f4f8fc")
        window_id = canvas.create_window((0,0), window=scrollable_frame, anchor="nw")

        def resize_inner_frame(event):
            canvas.itemconfig(window_id, width=event.width)
            canvas.configure(scrollregion=canvas.bbox("all"))
        canvas.bind("<Configure>", resize_inner_frame)

        # Mejor manejo de scroll (Windows / Linux)
        def _on_mousewheel(event):
            try:
                if canvas.winfo_exists():
                    canvas.yview_scroll(int(-1*(event.delta/120)), "units")
            except tk.TclError:
                pass

        def _on_mousewheel_linux_up(event):
            try:
                if canvas.winfo_exists():
                    canvas.yview_scroll(-1, "units")
            except tk.TclError:
                pass

        def _on_mousewheel_linux_down(event):
            try:
                if canvas.winfo_exists():
                    canvas.yview_scroll(1, "units")
            except tk.TclError:
                pass

        canvas.bind("<Enter>", lambda e: canvas.bind("<MouseWheel>", _on_mousewheel))
        canvas.bind("<Leave>", lambda e: canvas.unbind("<MouseWheel>"))
        canvas.bind("<Enter>", lambda e: canvas.bind("<Button-4>", _on_mousewheel_linux_up))
        canvas.bind("<Leave>", lambda e: canvas.unbind("<Button-4>"))
        canvas.bind("<Enter>", lambda e: canvas.bind("<Button-5>", _on_mousewheel_linux_down))
        canvas.bind("<Leave>", lambda e: canvas.unbind("<Button-5>"))

        # columnas y frames
        scrollable_frame.grid_columnconfigure(0, weight=1, minsize=220)
        scrollable_frame.grid_columnconfigure(1, weight=1, minsize=280)
        scrollable_frame.grid_columnconfigure(2, weight=2, minsize=300)
        left_col = tk.Frame(scrollable_frame, bg="#f4f8fc")
        center_col = tk.Frame(scrollable_frame, bg="#f4f8fc")
        right_col = tk.Frame(scrollable_frame, bg="#f4f8fc")
        left_col.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        center_col.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        right_col.grid(row=0, column=2, sticky="nsew", padx=5, pady=5)

        self._create_basic_fields(left_col)
        self._create_nutrimental_fields(center_col)
        self._create_results_area(right_col)

        # attach trace so labels update when tipo_muestra changes
        try:
            self._attach_tipo_trace()
        except Exception:
            pass

        buttons_frame = tk.Frame(scrollable_frame, bg="#f4f8fc")
        buttons_frame.grid(row=1, column=0, columnspan=3, sticky="ew", pady=(10,10))
        buttons_container = tk.Frame(buttons_frame, bg="#f4f8fc")
        buttons_container.pack(expand=True)
        self._create_buttons(buttons_container)

    # --- UI builders (sin lógica de exportación) ---
    def _create_basic_fields(self, parent):
        basic_frame = tk.LabelFrame(parent, text="Información Básica", font=("Segoe UI",11,"bold"),
                                    bg="#ffffff", fg="#0B5394", bd=2, relief="groove")
        basic_frame.pack(fill="both", expand=True, padx=2, pady=2, ipadx=6, ipady=6)
        basic_frame.grid_columnconfigure(1, weight=1)
        tk.Label(basic_frame, text="# de muestra:", bg="#ffffff", font=("Segoe UI",9,"bold"), fg="#0B5394").grid(row=0, column=0, sticky="w", padx=8, pady=4)
        self.parent.nombre_entry = tk.Entry(basic_frame, font=("Segoe UI",9), relief="solid", bd=1)
        self.parent.nombre_entry.grid(row=0, column=1, padx=8, pady=4, sticky="ew")

        tk.Label(basic_frame, text="Descripción:", bg="#ffffff", font=("Segoe UI",9,"bold"), fg="#0B5394").grid(row=1, column=0, sticky="nw", padx=8, pady=4)
        self.parent.descripcion_entry = tk.Text(basic_frame, font=("Segoe UI",9), height=3, relief="solid", bd=1)
        self.parent.descripcion_entry.grid(row=1, column=1, padx=8, pady=4, sticky="ew")

        tk.Label(basic_frame, text="Fecha:", bg="#ffffff", font=("Segoe UI",9,"bold"), fg="#0B5394").grid(row=2, column=0, sticky="w", padx=8, pady=4)
        self.parent.fecha_entry = tk.Entry(basic_frame, font=("Segoe UI",9), state="readonly", bg="#f0f0f0", relief="solid", bd=1)
        fecha_actual = datetime.datetime.now().strftime("%Y-%m-%d")
        self.parent.fecha_entry.config(state="normal"); self.parent.fecha_entry.insert(0, fecha_actual); self.parent.fecha_entry.config(state="readonly")
        self.parent.fecha_entry.grid(row=2, column=1, padx=8, pady=4, sticky="ew")

        tk.Label(basic_frame, text="Hora:", bg="#ffffff", font=("Segoe UI",9,"bold"), fg="#0B5394").grid(row=3, column=0, sticky="w", padx=8, pady=4)
        self.parent.hora_entry = tk.Entry(basic_frame, font=("Segoe UI",9), state="readonly", bg="#f0f0f0", relief="solid", bd=1)
        hora_actual = datetime.datetime.now().strftime("%H:%M:%S")
        self.parent.hora_entry.config(state="normal"); self.parent.hora_entry.insert(0, hora_actual); self.parent.hora_entry.config(state="readonly")
        self.parent.hora_entry.grid(row=3, column=1, padx=8, pady=4, sticky="ew")

        tipo_frame = tk.LabelFrame(basic_frame, text="Tipo de Muestra", font=("Segoe UI",9,"bold"), bg="#ffffff", fg="#0B5394", bd=1, relief="groove")
        tipo_frame.grid(row=4, column=0, columnspan=2, sticky="ew", padx=8, pady=4)
        self.parent.tipo_muestra = tk.StringVar(value="solida")
        tk.Radiobutton(tipo_frame, text="Sólida", variable=self.parent.tipo_muestra, value="solida", bg="#ffffff", font=("Segoe UI",9)).pack(side="left", padx=10, pady=4)
        tk.Radiobutton(tipo_frame, text="Líquida", variable=self.parent.tipo_muestra, value="liquida", bg="#ffffff", font=("Segoe UI",9)).pack(side="left", padx=10, pady=4)
        self.parent.bebida_sin_calorias = tk.BooleanVar(value=False)
        tk.Checkbutton(tipo_frame, text="Es bebida sin calorías", variable=self.parent.bebida_sin_calorias, bg="#ffffff", font=("Segoe UI",9)).pack(side="left", padx=10, pady=4)

    def _create_nutrimental_fields(self, parent):
        nutri_frame = tk.LabelFrame(parent, text="Datos Nutricionales", font=("Segoe UI",11,"bold"),
                                    bg="#ffffff", fg="#0B5394", bd=2, relief="groove")
        nutri_frame.pack(fill="both", expand=True, padx=2, pady=2, ipadx=6, ipady=6)
        nutri_frame.grid_columnconfigure(1, weight=1)
        self.parent.nutri_vars = {}
        # almacén de labels para poder actualizarlos dinámicamente según tipo (g / mL)
        self.parent.nutri_label_widgets = {}

        # Determinar si ajustar etiquetas por sólido / líquido (inicial)
        tipo_var = getattr(self.parent, "tipo_muestra", None)
        es_liquida = False
        try:
            if tipo_var is not None and tipo_var.get() == "liquida":
                es_liquida = True
        except Exception:
            es_liquida = False

        # sufijos dinámicos para etiquetas: por 100 g o por 100 mL (la unidad de referencia)
        ref_unit = "100 mL" if es_liquida else "100 g"
        suf_g = f"(g/{ref_unit})"
        suf_mg = f"(mg/{ref_unit})"

        nutri_fields = [
            ("humedad", "Humedad (%)"),
            ("cenizas", "Cenizas (%)"),
            ("proteina", f"Proteína {suf_g}"),
            ("grasa_total", f"Grasa total {suf_g}"),
            ("grasa_trans", f"Grasas trans {suf_mg}"),
            ("fibra_dietetica", f"Fibra dietética {suf_g}"),
            ("azucares", f"Azúcares totales {suf_g}"),
            ("azucares_anadidos", f"Azúcares añadidos {suf_g}"),
            ("sodio", f"Sodio {suf_mg}"),
            ("acidos_grasos_saturados", f"Ácidos grasos saturados {suf_g}"),
            ("porcion", f"Tamaño de porción (g o mL)"),
            ("contenido_neto", "Contenido neto del envase (g o mL, opcional)")
        ]
        for i, (key, label_text) in enumerate(nutri_fields):
            lbl = tk.Label(nutri_frame, text=label_text, bg="#ffffff", font=("Segoe UI",9,"bold"), fg="#0B5394")
            lbl.grid(row=i, column=0, sticky="w", padx=8, pady=3)
            entry = tk.Entry(nutri_frame, font=("Segoe UI",9), relief="solid", bd=1)
            entry.grid(row=i, column=1, padx=8, pady=3, sticky="ew")
            self.parent.nutri_vars[key] = entry
            self.parent.nutri_label_widgets[key] = lbl

    def _create_results_area(self, parent):
        self.parent.resultados_frame = tk.LabelFrame(parent, text="Resultados", font=("Segoe UI",11,"bold"),
                                                     bg="#ffffff", fg="#0B5394", bd=2, relief="groove")
        self.parent.resultados_frame.pack(fill="both", expand=True, padx=2, pady=2, ipadx=6, ipady=6)
        self.parent.resultados_text = tk.Text(self.parent.resultados_frame, font=("Courier New",9), bg="#f8f9fa", state="disabled", relief="solid", bd=1, wrap="word")
        resultados_scroll = tk.Scrollbar(self.parent.resultados_frame, orient="vertical", command=self.parent.resultados_text.yview)
        self.parent.resultados_text.configure(yscrollcommand=resultados_scroll.set)
        self.parent.resultados_text.pack(side="left", fill="both", expand=True, padx=8, pady=8)
        resultados_scroll.pack(side="right", fill="y", pady=8)

    def _create_buttons(self, parent):
        calc_btn = tk.Button(parent, text="Calcular Tabla Nutrimental", command=self.calcular_tabla_nutrimental, bg="#0B5394", fg="white", font=("Segoe UI",11,"bold"), relief="flat", padx=15, pady=8, cursor="hand2", activebackground="#073763", activeforeground="white")
        calc_btn.pack(side="left", padx=(0,10))

        formato_btn = tk.Button(parent, text="Exportar en formato oficial", command=self.exporter.exportar_a_formato_predefinido, bg="#ffc107", fg="black", font=("Segoe UI",11,"bold"), relief="flat", padx=15, pady=8, cursor="hand2")
        formato_btn.pack(side="left", padx=10)

        guardar_bd_btn = tk.Button(parent, text="Guardar en Base de Datos", command=self.exporter.guardar_solo_bd, bg="#007bff", fg="white", font=("Segoe UI",11,"bold"), relief="flat", padx=15, pady=8, cursor="hand2")
        guardar_bd_btn.pack(side="left", padx=10)

    # --- Lógica de cálculo (permanece aquí) ---
    def calcular_tabla_nutrimental(self):
        try:
            data = {}
            for key, entry in self.parent.nutri_vars.items():
                value = entry.get().strip()
                if value == "":
                    # contenido_neto puede quedar vacío, pero other fields required checked later
                    continue
                # sodio and grasa_trans provided as mg/100g but still numeric
                data[key] = float(value)
            required_fields = ["humedad","cenizas","proteina","grasa_total","grasa_trans","fibra_dietetica","azucares","azucares_anadidos","sodio","acidos_grasos_saturados","porcion"]
            for field in required_fields:
                if field not in data:
                    messagebox.showerror("Error", f"El campo '{field.replace('_',' ').title()}' es requerido")
                    return
            resultados = self._calcular_nutrimental(data)
            self._mostrar_resultados(resultados)
            self.parent.ultimo_calculo = {
                "datos_basicos": {
                    "nombre": self.parent.nombre_entry.get(),
                    "descripcion": self.parent.descripcion_entry.get("1.0","end-1c"),
                    "fecha": self.parent.fecha_entry.get(),
                    "hora": self.parent.hora_entry.get()
                },
                "datos_entrada": data,
                "resultados": resultados
            }
        except ValueError:
            messagebox.showerror("Error", "Por favor ingrese valores numéricos válidos")
        except Exception as e:
            messagebox.showerror("Error", f"Error en el cálculo: {e}")

    def _aplicar_redondeo_nutrientes(self, valor):
        if valor < 0.5:
            return 0
        elif valor <= 5:
            return round(valor * 2) / 2
        else:
            return round(valor)

    def _aplicar_redondeo_energia(self, valor):
        if valor < 5:
            return 0
        elif valor <= 50:
            return round(valor / 5) * 5
        else:
            return round(valor / 10) * 10

    def _aplicar_regla_redondeo_sodio(self, valor):
        if valor < 5:
            return 0
        elif valor < 140:
            return int(round(valor / 5) * 5)
        else:
            return int(round(valor / 10) * 10)

    def _calcular_nutrimental(self, data):
        proteina_100g = self._aplicar_redondeo_nutrientes(data["proteina"])
        grasa_total_100g = self._aplicar_redondeo_nutrientes(data["grasa_total"])
        fibra_dietetica_100g = self._aplicar_redondeo_nutrientes(data["fibra_dietetica"])
        azucares_100g = self._aplicar_redondeo_nutrientes(data["azucares"])
        azucares_anadidos_100g = self._aplicar_redondeo_nutrientes(data["azucares_anadidos"])
        grasa_saturada_100g = self._aplicar_redondeo_nutrientes(grasa_total_100g * (data["acidos_grasos_saturados"]/100))
        hidratos_totales = max(0, 100 - (data["humedad"] + data["cenizas"] + proteina_100g + grasa_total_100g))
        carbohidratos_disponibles_100g = max(0, hidratos_totales - fibra_dietetica_100g)
        sodio_100g = self._aplicar_regla_redondeo_sodio(data["sodio"])
        grasa_trans_100g = self._aplicar_regla_redondeo_sodio(data["grasa_trans"])

        energia_kcal_100g = self._aplicar_redondeo_energia((proteina_100g + carbohidratos_disponibles_100g) * 4 + grasa_total_100g * 9)
        energia_kj_100g = self._aplicar_redondeo_energia((proteina_100g + carbohidratos_disponibles_100g) * 17 + grasa_total_100g * 37)

        porcion = data["porcion"]
        proteina_porcion = self._aplicar_redondeo_nutrientes(proteina_100g * porcion / 100)
        grasa_total_porcion = self._aplicar_redondeo_nutrientes(grasa_total_100g * porcion / 100)
        grasa_saturada_porcion = self._aplicar_redondeo_nutrientes(grasa_saturada_100g * porcion / 100)
        fibra_dietetica_porcion = self._aplicar_redondeo_nutrientes(fibra_dietetica_100g * porcion / 100)
        azucares_porcion = self._aplicar_redondeo_nutrientes(azucares_100g * porcion / 100)
        azucares_anadidos_porcion = self._aplicar_redondeo_nutrientes(azucares_anadidos_100g * porcion / 100)
        carbohidratos_disponibles_porcion = self._aplicar_redondeo_nutrientes(carbohidratos_disponibles_100g * porcion / 100)
        sodio_porcion = self._aplicar_regla_redondeo_sodio(sodio_100g * porcion / 100)
        grasa_trans_porcion = self._aplicar_regla_redondeo_sodio(grasa_trans_100g * porcion / 100)

        energia_kcal_porcion = self._aplicar_redondeo_energia((proteina_porcion + carbohidratos_disponibles_porcion) * 4 + grasa_total_porcion * 9)
        energia_kj_porcion = self._aplicar_redondeo_energia((proteina_porcion + carbohidratos_disponibles_porcion) * 17 + grasa_total_porcion * 37)

        porciones_envase = None
        if data.get("contenido_neto"):
            try:
                porciones_envase = data["contenido_neto"] / porcion
            except Exception:
                porciones_envase = None

        por_envase = None
        if data.get("contenido_neto"):
            factor_cn = data["contenido_neto"] / 100
            energia_kcal_envase = int(round(energia_kcal_100g * factor_cn))
            energia_kj_envase = int(round(energia_kj_100g * factor_cn))
            por_envase = {"energia_kcal": energia_kcal_envase, "energia_kj": energia_kj_envase}

        resultados = {
            "por_100g": {
                "proteina": proteina_100g,
                "grasa_total": grasa_total_100g,
                "grasa_saturada": grasa_saturada_100g,
                "grasa_trans": grasa_trans_100g,
                "carbohidratos_disponibles": carbohidratos_disponibles_100g,
                "azucares": azucares_100g,
                "azucares_anadidos": azucares_anadidos_100g,
                "fibra_dietetica": fibra_dietetica_100g,
                "sodio": sodio_100g,
                "energia_kcal": energia_kcal_100g,
                "energia_kj": energia_kj_100g
            },
            "por_porcion": {
                "proteina": proteina_porcion,
                "grasa_total": grasa_total_porcion,
                "grasa_saturada": grasa_saturada_porcion,
                "grasa_trans": grasa_trans_porcion,
                "carbohidratos_disponibles": carbohidratos_disponibles_porcion,
                "azucares": azucares_porcion,
                "azucares_anadidos": azucares_anadidos_porcion,
                "fibra_dietetica": fibra_dietetica_porcion,
                "sodio": sodio_porcion,
                "energia_kcal": energia_kcal_porcion,
                "energia_kj": energia_kj_porcion
            }
        }
        if porciones_envase is not None:
            resultados["porciones_envase"] = porciones_envase
        if por_envase is not None:
            resultados["por_envase"] = por_envase
        resultados["es_porcion_100g"] = porcion == 100.0
        return resultados

    # --- Lógica de sellos (permanece aquí) ---
    def _calcular_sellos_advertencia(self, resultados):
        """Calcula sellos de advertencia siguiendo info2.txt (NOM-like)."""
        sellos = {
            "exceso_calorias": False,
            "exceso_azucares": False,
            "exceso_grasas_saturadas": False,
            "exceso_grasas_trans": False,
            "exceso_sodio": False
        }

        # Tipo de muestra / bebida sin calorías (componentes UI deben existir)
        es_liquida = getattr(self.parent, "tipo_muestra", None) and self.parent.tipo_muestra.get() == "liquida"
        es_bebida_sin_calorias = getattr(self.parent, "bebida_sin_calorias", None) and self.parent.bebida_sin_calorias.get()

        por100 = resultados.get("por_100g", {})

        # Valores esperados: energia_kcal (kcal), azucares (g), grasa_saturada (g),
        # grasa_trans (mg), sodio (mg)
        calorias = float(por100.get("energia_kcal", 0) or 0)
        azucares_g = float(por100.get("azucares", 0) or 0)
        grasa_sat_g = float(por100.get("grasa_saturada", 0) or 0)
        grasa_trans_mg = float(por100.get("grasa_trans", 0) or 0)
        sodio_mg = float(por100.get("sodio", 0) or 0)

        # 1) EXCESO DE CALORÍAS
        # sólido >=275 kcal/100g, líquido >=70 kcal/100mL
        if es_liquida:
            if calorias >= 70:
                sellos["exceso_calorias"] = True
        else:
            if calorias >= 275:
                sellos["exceso_calorias"] = True
        # Alternativa: si azúcares*4 >= 8 kcal
        if (azucares_g * 4) >= 8:
            sellos["exceso_calorias"] = True

        # 2) EXCESO DE AZÚCARES:
        # si (azucares_g * 4) >= 10% de las kcal en 100g/mL
        if calorias > 0:
            if (azucares_g * 4) >= (0.10 * calorias):
                sellos["exceso_azucares"] = True

        # 3) EXCESO DE GRASAS SATURADAS:
        # si (grasa_sat_g * 9) >= 10% de las kcal
        if calorias > 0:
            if (grasa_sat_g * 9) >= (0.10 * calorias):
                sellos["exceso_grasas_saturadas"] = True

        # 4) EXCESO DE GRASAS TRANS:
        # convertir mg -> g ( /1000 ) y luego *9; si >= 1% de kcal
        if calorias > 0:
            energia_trans_kcal = (grasa_trans_mg / 1000.0) * 9.0
            if energia_trans_kcal >= (0.01 * calorias):
                sellos["exceso_grasas_trans"] = True

        # 5) EXCESO DE SODIO:
        # sodio_mg >= 300 OR sodio_mg >= kcal (más mg sodio que kcal)
        # OR (si bebida sin calorías) sodio_mg >= 45
        if sodio_mg >= 300:
            sellos["exceso_sodio"] = True
        elif calorias >= 0 and sodio_mg >= calorias:
            sellos["exceso_sodio"] = True
        elif es_bebida_sin_calorias and sodio_mg >= 45:
            sellos["exceso_sodio"] = True

        return sellos

    def _mostrar_resultados(self, resultados):
        self.parent.resultados_text.config(state="normal")
        self.parent.resultados_text.delete("1.0","end")

        # Determinar unidad de referencia para encabezado según tipo de muestra
        tipo_var = getattr(self.parent, "tipo_muestra", None)
        es_liquida = False
        try:
            if tipo_var is not None and tipo_var.get() == "liquida":
                es_liquida = True
        except Exception:
            es_liquida = False
        unidad_ref = "mL" if es_liquida else "g"

        texto = "TABLA NUTRIMENTAL MEXICANA\n" + "="*50 + "\n\n"
        if "porciones_envase" in resultados and resultados["porciones_envase"] is not None:
            p = resultados["porciones_envase"]
            texto += f"Porciones por envase: {int(p) if p==int(p) else f'{p:.1f}'}\n\n"

        texto += f"POR 100 {unidad_ref}:\n" + "-"*20 + "\n"
        orden_campos = [
            ("proteina","Proteína","g"),
            ("grasa_total","Grasa Total","g"),
            ("grasa_saturada","Grasa Saturada","g"),
            ("grasa_trans","Grasas trans","mg"),
            ("carbohidratos_disponibles","Carbohidratos Disponibles","g"),
            ("azucares","Azúcares","g"),
            ("azucares_anadidos","Azúcares añadidos","g"),
            ("fibra_dietetica","Fibra Dietética","g"),
            ("sodio","Sodio","mg"),
            ("energia_kcal","Contenido energético","kcal"),
            ("energia_kj","Contenido energético","kJ"),
        ]
        for key, nombre, unidad in orden_campos:
            if key in resultados["por_100g"]:
                texto += f"{nombre}: {resultados['por_100g'][key]} {unidad}\n"
        texto += "\n"
        if not resultados.get("es_porcion_100g", False):
            texto += "POR PORCIÓN:\n" + "-"*20 + "\n"
            for key, nombre, unidad in orden_campos:
                if key in resultados["por_porcion"]:
                    texto += f"{nombre}: {resultados['por_porcion'][key]} {unidad}\n"
            texto += "\n"
        if "por_envase" in resultados:
            texto += "POR ENVASE:\n" + "-"*20 + "\n"
            texto += f"Contenido energético: {resultados['por_envase']['energia_kcal']} kcal\n"
            texto += f"Contenido energético: {resultados['por_envase']['energia_kj']} kJ\n"
        sellos = self._calcular_sellos_advertencia(resultados)
        texto += "\nSELLOS DE ADVERTENCIA:\n" + "-"*20 + "\n"
        if any(sellos.values()):
            if sellos["exceso_calorias"]: texto += "• EXCESO DE CALORÍAS\n"
            if sellos["exceso_azucares"]: texto += "• EXCESO DE AZÚCARES\n"
            if sellos["exceso_grasas_saturadas"]: texto += "• EXCESO DE GRASAS SATURADAS\n"
            if sellos["exceso_grasas_trans"]: texto += "• EXCESO DE GRASAS TRANS\n"
            if sellos["exceso_sodio"]: texto += "• EXCESO DE SODIO\n"
        else:
            texto += "No se requieren sellos de advertencia.\n"
        self.parent.resultados_text.insert("1.0", texto)
        self.parent.resultados_text.config(state="disabled")

    def _get_label_text(self, key, es_liquida):
        """Devuelve el texto correcto para la etiqueta 'key' según si es líquida."""
        ref_unit = "100 mL" if es_liquida else "100 g"
        suf_g = f"(g/{ref_unit})"
        suf_mg = f"(mg/{ref_unit})"
        mapping = {
            "humedad": "Humedad (%)",
            "cenizas": "Cenizas (%)",
            "proteina": f"Proteína {suf_g}",
            "grasa_total": f"Grasa total {suf_g}",
            "grasa_trans": f"Grasas trans {suf_mg}",
            "fibra_dietetica": f"Fibra dietética {suf_g}",
            "azucares": f"Azúcares totales {suf_g}",
            "azucares_anadidos": f"Azúcares añadidos {suf_g}",
            "sodio": f"Sodio {suf_mg}",
            "acidos_grasos_saturados": f"Ácidos grasos saturados {suf_g}",
            "porcion": f"Tamaño de porción ({'mL' if es_liquida else 'g'})",
            "contenido_neto": f"Contenido neto del envase ({'mL' if es_liquida else 'g'}, opcional)"
        }
        return mapping.get(key, key)

    def _update_unit_labels(self):
        """Actualiza las etiquetas de unidad en la UI según self.parent.tipo_muestra."""
        tipo_var = getattr(self.parent, "tipo_muestra", None)
        es_liquida = False
        try:
            if tipo_var is not None and tipo_var.get() == "liquida":
                es_liquida = True
        except Exception:
            es_liquida = False
        labels = getattr(self.parent, "nutri_label_widgets", {})
        for key, lbl in labels.items():
            try:
                lbl.config(text=self._get_label_text(key, es_liquida))
            except Exception:
                pass

    def _attach_tipo_trace(self):
        """Agrega trace para que al cambiar el tipo (sólida/liquida) se actualicen las etiquetas."""
        tipo_var = getattr(self.parent, "tipo_muestra", None)
        if tipo_var is None:
            return
        # limpias traces previos si existen (compatibilidad)
        try:
            if hasattr(tipo_var, "trace_vinfo"):
                pass
        except Exception:
            pass
        # trace_add es preferible en py3.7+, fallback a trace
        try:
            tipo_var.trace_add("write", lambda *args: self._update_unit_labels())
        except Exception:
            try:
                tipo_var.trace("w", lambda *args: self._update_unit_labels())
            except Exception:
                pass
        # actualizar ahora mismo para reflejar estado inicial
        self._update_unit_labels()