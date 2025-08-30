import tkinter as tk
from tkinter import messagebox
import math
import datetime
"""Módulo de cálculo y visualización de Tabla Nutrimental.

Reglas implementadas (resumen):
1. Todos los nutrientes se muestran como enteros.
2. Redondeo general: HALF_UP (>=0.5 sube) aplicado sobre valor positivo.
3. Sodio (mg) y grasas trans por porción (mg) con regla NOM escalonada:
    - <5 -> 0
    - 5–139 -> múltiplos de 5
    - >=140 -> múltiplos de 10
4. Grasas saturadas = grasa total * (%) saturados, luego HALF_UP.
5. Carbohidratos disponibles = floor( 100 - (humedad + cenizas + proteína + grasa total) - fibra ) usando valores crudos.
6. Energía (kcal) = (Proteína + Carbohidratos disponibles)*4 + Grasa total*9, luego a múltiplo de 10.
7. Energía kJ = (Proteína + Carbohidratos disponibles)*17 + Grasa total*37 (entero).
8. Valores por porción se derivan de los enteros por 100 g/mL (excepto sodio y trans que se recalculan desde crudos y redondean con su regla). 
9. Energía por porción también se redondea a múltiplo de 10.
10. Sellos de advertencia aplican límites definidos en archivo info2.txt (criterios replicados aquí).

Pendientes opcionales que pueden activarse en el futuro:
- Usar energía sólo como entero (sin múltiplo de 10) si se ajusta especificación.
- Balance de carbohidratos usando componentes ya redondeados si se modifica la regla.
"""
import os
from PIL import Image, ImageTk  # sólo si en el futuro se necesita mostrar imágenes en UI
# from core.auth import agregar_historial  # no se usa directamente aquí
from ui.base_interface import bind_mousewheel
import tempfile
from core.exporter import NutrimentalExporter  # solo el exportador, no la lógica de sellos

class NutrimentalModule:
    def __init__(self, parent_window):
        self.parent = parent_window
        self.exporter = NutrimentalExporter(parent_window)

    # ----------------- NUEVO: método público para botón -----------------
    def calcular_tabla_nutrimental(self):
        """Lee entradas, calcula resultados, guarda en self.parent.ultimo_calculo y muestra."""
        try:
            entradas = {}
            for key, entry in getattr(self.parent, 'nutri_vars', {}).items():
                val_txt = entry.get().strip()
                if val_txt == '':
                    val_txt = '0'
                entradas[key] = val_txt.replace(',', '.')
            # básicos
            nombre = getattr(self.parent, 'nombre_entry', None).get().strip() if hasattr(self.parent, 'nombre_entry') else ''
            descripcion = getattr(self.parent, 'descripcion_entry', None).get('1.0','end-1c').strip() if hasattr(self.parent, 'descripcion_entry') else ''
            datos_basicos = { 'nombre': nombre, 'descripcion': descripcion }
            resultados = self._calcular_nutrimental(entradas)
            self.parent.ultimo_calculo = {
                'datos_entrada': entradas,
                'resultados': resultados,
                'datos_basicos': datos_basicos
            }
            self._mostrar_resultados(resultados)
        except Exception as e:
            messagebox.showerror('Error', f'No se pudo calcular la tabla nutrimental.\n{e}')

    def show_nutrimental_section(self):
        """Construye la interfaz, sin realizar cálculos todavía."""
        for widget in self.parent.content_frame.winfo_children():
            widget.destroy()

        main_frame = tk.Frame(self.parent.content_frame, bg="#f4f8fc", bd=0)
        main_frame.pack(expand=True, fill="both", padx=20, pady=(5,20))

        canvas = tk.Canvas(main_frame, bg="#f4f8fc", highlightthickness=0)
        scrollbar = tk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Contenedor desplazable
        scrollable_frame = tk.Frame(canvas, bg="#f4f8fc")
        self._scrollable_window_id = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        # Ajustar ancho del frame interno al ancho visible del canvas para evitar corte horizontal
        def _sync_inner_width(event):
            try:
                canvas.itemconfig(self._scrollable_window_id, width=event.width)
            except Exception:
                pass
        canvas.bind('<Configure>', _sync_inner_width)
        bind_mousewheel(canvas, scrollable_frame)

        scrollable_frame.grid_columnconfigure(0, weight=1, uniform="col")
        scrollable_frame.grid_columnconfigure(1, weight=1, uniform="col")
        scrollable_frame.grid_columnconfigure(2, weight=1, uniform="col")

        left_col = tk.Frame(scrollable_frame, bg="#f4f8fc")
        center_col = tk.Frame(scrollable_frame, bg="#f4f8fc")
        right_col = tk.Frame(scrollable_frame, bg="#f4f8fc")
        left_col.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        center_col.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        right_col.grid(row=0, column=2, sticky="nsew", padx=5, pady=5)

        self._create_basic_fields(left_col)
        self._create_nutrimental_fields(center_col)
        self._create_results_area(right_col)

        # Guardar referencias para layout responsivo
        self._responsive_parent = scrollable_frame
        self._col_left = left_col
        self._col_center = center_col
        self._col_right = right_col
        self._layout_mode = None  # para evitar re-dibujar si no cambia

        self._apply_responsive_layout(initial=True)

        # Bind de resize (usar toplevel para captar cambios de ventana)
        toplevel = self.parent.winfo_toplevel()
        try:
            toplevel.bind('<Configure>', lambda e: self._apply_responsive_layout())
        except Exception:
            pass

        try:
            self._attach_tipo_trace()
        except Exception:
            pass

        # Frame de botones (dentro del método, con indentación correcta)
        self._buttons_frame = tk.Frame(scrollable_frame, bg="#f4f8fc")
        self._buttons_frame.grid(row=1, column=0, columnspan=3, sticky="ew", pady=(10,10))
        buttons_container = tk.Frame(self._buttons_frame, bg="#f4f8fc")
        buttons_container.pack(expand=True)
        self._create_buttons(buttons_container)

        # Fin del método show_nutrimental_section



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

        # create fields using label helper so units switch correctly for sólido/liquida
        nutri_keys = [
            "humedad",
            "cenizas",
            "proteina",
            "grasa_total",
            "grasa_trans",
            "fibra_dietetica",
            "azucares",
            "azucares_anadidos",
            "sodio",
            "acidos_grasos_saturados",
            "porcion",
            "contenido_neto",
        ]
        for i, key in enumerate(nutri_keys):
            label_text = self._get_label_text(key, es_liquida)
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
        self.parent.resultados_text = tk.Text(
            self.parent.resultados_frame,
            font=("Courier New",9),
            bg="#f8f9fa", state="disabled", relief="solid", bd=1,
            wrap="none"  # evitar corte de líneas; usamos ajuste dinámico de ancho
        )
        # Scroll horizontal opcional si la línea supera el ancho
        h_scroll = tk.Scrollbar(self.parent.resultados_frame, orient="horizontal", command=self.parent.resultados_text.xview)
        self.parent.resultados_text.configure(xscrollcommand=h_scroll.set)
        resultados_scroll = tk.Scrollbar(self.parent.resultados_frame, orient="vertical", command=self.parent.resultados_text.yview)
        self.parent.resultados_text.configure(yscrollcommand=resultados_scroll.set)
        self.parent.resultados_text.pack(side="left", fill="both", expand=True, padx=8, pady=(8,0))
        resultados_scroll.pack(side="right", fill="y", pady=8)
        h_scroll.pack(side="bottom", fill="x", padx=8, pady=(0,8))

    def _create_buttons(self, parent):
        calc_btn = tk.Button(parent, text="Calcular Tabla Nutrimental", command=self.calcular_tabla_nutrimental,
                             bg="#0B5394", fg="white", font=("Segoe UI",11,"bold"), relief="flat",
                             padx=15, pady=8, cursor="hand2", activebackground="#073763", activeforeground="white")
        calc_btn.pack(side="left", padx=(0,10))

        formato_btn = tk.Button(parent, text="Exportar en formato oficial", command=self.exporter.exportar_a_formato_predefinido,
                                 bg="#ffc107", fg="black", font=("Segoe UI",11,"bold"), relief="flat",
                                 padx=15, pady=8, cursor="hand2")
        formato_btn.pack(side="left", padx=10)

        guardar_bd_btn = tk.Button(parent, text="Guardar en Base de Datos", command=self.exporter.guardar_solo_bd,
                                    bg="#007bff", fg="white", font=("Segoe UI",11,"bold"), relief="flat",
                                    padx=15, pady=8, cursor="hand2")
        guardar_bd_btn.pack(side="left", padx=10)

    def _aplicar_redondeo_nutrientes_porcion(self, valor):
        """Compatibilidad: antes existía un método genérico. Ahora solo aplica HALF_UP global."""
        return self._round_half_up(valor)

    # --- Funciones utilitarias de redondeo ---
    def _round_half_up(self, val):
        from decimal import Decimal, ROUND_HALF_UP
        try:
            v = float(val)
        except Exception:
            return 0
        if v < 0.5:
            return 0
        return int(Decimal(str(v)).quantize(Decimal('1'), rounding=ROUND_HALF_UP))

    def _aplicar_regla_redondeo_sodio(self, valor):
        if valor < 5:
            return 0
        elif valor < 140:
            return int(round(valor / 5) * 5)
        else:
            return int(round(valor / 10) * 10)

    def _calcular_nutrimental(self, data):
        # Validación básica: si suma de componentes mayores a 120 (arbitrario) lanzar aviso silencioso
        # (no interrumpe cálculo, sólo prepara flag interno)
        aviso_componentes_excedidos = False
        def half_up(val):
            return self._round_half_up(val)

        # 1. Valores crudos
        proteina_raw = float(data.get('proteina',0) or 0)
        grasa_total_raw = float(data.get('grasa_total',0) or 0)
        fibra_raw = float(data.get('fibra_dietetica',0) or 0)
        azucares_raw = float(data.get('azucares',0) or 0)
        azucares_anadidos_raw = float(data.get('azucares_anadidos',0) or 0)
        humedad_raw = float(data.get('humedad',0) or 0)
        cenizas_raw = float(data.get('cenizas',0) or 0)
        acidos_sat_pct = float(data.get('acidos_grasos_saturados',0) or 0)
        sodio_raw = float(data.get('sodio',0) or 0)            # mg
        grasa_trans_raw = float(data.get('grasa_trans',0) or 0) # mg

        # 2. Derivados crudos
        grasa_saturada_cruda = grasa_total_raw * acidos_sat_pct / 100.0

        # 3. Redondeos por 100 g
        humedad_100g = half_up(humedad_raw)
        cenizas_100g = half_up(cenizas_raw)
        proteina_100g = half_up(proteina_raw)
        grasa_total_100g = half_up(grasa_total_raw)
        fibra_dietetica_100g = half_up(fibra_raw)
        azucares_100g = half_up(azucares_raw)
        azucares_anadidos_100g = half_up(azucares_anadidos_raw)
        grasa_saturada_100g = half_up(grasa_saturada_cruda)

        # Carbohidratos disponibles (balance crudo -> floor)
        carbo_balance = 100 - (humedad_raw + cenizas_raw + proteina_raw + grasa_total_raw) - fibra_raw
        if carbo_balance < 0: carbo_balance = 0
        carbohidratos_disponibles_100g = int(math.floor(carbo_balance))

        # Chequeo (heurístico) de exceso de suma (sin fibra) para marcar posible inconsistencia
        total_componentes_base = humedad_raw + cenizas_raw + proteina_raw + grasa_total_raw + fibra_raw
        if total_componentes_base > 101:  # tolerancia 1%
            aviso_componentes_excedidos = True

        sodio_100g = self._aplicar_regla_redondeo_sodio(sodio_raw)
        grasa_trans_100g = half_up(grasa_trans_raw)

        # Energía (múltiplo de 10 kcal)
        energia_kcal_100g = (proteina_100g + carbohidratos_disponibles_100g) * 4 + grasa_total_100g * 9
        energia_kcal_100g = int(round(energia_kcal_100g / 10.0) * 10)
        energia_kj_100g = (proteina_100g + carbohidratos_disponibles_100g) * 17 + grasa_total_100g * 37

        # 4. Por porción
        porcion = float(data.get('porcion',0) or 0)
        factor = porcion / 100.0 if porcion else 0
        proteina_porcion = half_up(proteina_100g * factor)
        grasa_total_porcion = half_up(grasa_total_100g * factor)
        grasa_saturada_porcion = half_up(grasa_saturada_100g * factor)
        fibra_dietetica_porcion = half_up(fibra_dietetica_100g * factor)
        azucares_porcion = half_up(azucares_100g * factor)
        azucares_anadidos_porcion = half_up(azucares_anadidos_100g * factor)
        carbohidratos_disponibles_porcion = half_up(carbohidratos_disponibles_100g * factor)
        sodio_porcion = self._aplicar_regla_redondeo_sodio(sodio_raw * factor)
        trans_raw_porcion = grasa_trans_raw * factor
        if trans_raw_porcion < 5:
            grasa_trans_porcion = 0
        elif trans_raw_porcion < 140:
            grasa_trans_porcion = int(round(trans_raw_porcion / 5) * 5)
        else:
            grasa_trans_porcion = int(round(trans_raw_porcion / 10) * 10)
        energia_kcal_porcion = (proteina_porcion + carbohidratos_disponibles_porcion) * 4 + grasa_total_porcion * 9
        energia_kcal_porcion = int(round(energia_kcal_porcion / 10.0) * 10)
        energia_kj_porcion = (proteina_porcion + carbohidratos_disponibles_porcion) * 17 + grasa_total_porcion * 37

        porciones_envase = None
        por_envase = None
        contenido_neto_txt = data.get('contenido_neto')
        if contenido_neto_txt:
            try:
                contenido_neto = float(contenido_neto_txt)
                porciones_envase = contenido_neto / porcion if porcion else None
                factor_env = contenido_neto / 100.0
                energia_kcal_envase = energia_kcal_100g * factor_env
                energia_kj_envase = energia_kj_100g * factor_env
                por_envase = {
                    'energia_kcal': int(round(energia_kcal_envase)),
                    'energia_kj': int(round(energia_kj_envase))
                }
            except Exception:
                porciones_envase = None

        resultados = {
            'por_100g': {
                'proteina': proteina_100g,
                'grasa_total': grasa_total_100g,
                'grasa_saturada': grasa_saturada_100g,
                'grasa_trans': grasa_trans_100g,
                'carbohidratos_disponibles': carbohidratos_disponibles_100g,
                'azucares': azucares_100g,
                'azucares_anadidos': azucares_anadidos_100g,
                'fibra_dietetica': fibra_dietetica_100g,
                'sodio': sodio_100g,
                'energia_kcal': energia_kcal_100g,
                'energia_kj': energia_kj_100g
            },
            'por_porcion': {
                'proteina': proteina_porcion,
                'grasa_total': grasa_total_porcion,
                'grasa_saturada': grasa_saturada_porcion,
                'grasa_trans': grasa_trans_porcion,
                'carbohidratos_disponibles': carbohidratos_disponibles_porcion,
                'azucares': azucares_porcion,
                'azucares_anadidos': azucares_anadidos_porcion,
                'fibra_dietetica': fibra_dietetica_porcion,
                'sodio': sodio_porcion,
                'energia_kcal': energia_kcal_porcion,
                'energia_kj': energia_kj_porcion
            }
        }
        if porciones_envase is not None:
            resultados['porciones_envase'] = porciones_envase
        if por_envase is not None:
            resultados['por_envase'] = por_envase
        resultados['es_porcion_100g'] = (porcion == 100.0)
        if aviso_componentes_excedidos:
            resultados['warning_componentes'] = True
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

        tipo_var = getattr(self.parent, "tipo_muestra", None)
        es_liquida = False
        try:
            if tipo_var is not None and tipo_var.get() == "liquida":
                es_liquida = True
        except Exception:
            es_liquida = False
        unidad_base = "mL" if es_liquida else "g"

        def _int(v):
            try:
                return int(float(v))
            except Exception:
                return 0

        por100 = resultados.get('por_100g', {})
        porcion_dict = resultados.get('por_porcion', {}) if not resultados.get('es_porcion_100g', False) else {}
        filas = [
            ("energia_kcal", "Contenido energético (kcal)", "kcal"),
            ("energia_kj", "Contenido energético (kJ)", "kJ"),
            ("proteina", "Proteína (g)", "g"),
            ("grasa_total", "Grasa total (g)", "g"),
            ("grasa_saturada", "Grasa saturada (g)", "g"),
            ("grasa_trans", "Grasas trans (mg)", "mg"),
            ("carbohidratos_disponibles", "Carbohidratos disponibles (g)", "g"),
            ("azucares", "Azúcares (g)", "g"),
            ("azucares_anadidos", "Azúcares añadidos (g)", "g"),
            ("fibra_dietetica", "Fibra dietética (g)", "g"),
            ("sodio", "Sodio (mg)", "mg"),
        ]
        # Calcular ancho dinámico de la tabla (caracteres) según ancho del widget en píxeles
        try:
            w_px = self.parent.resultados_text.winfo_width()
            # estimación: ~7 px por carácter con Courier New 9
            if w_px and w_px > 50:
                ancho_total = max(60, min(140, int(w_px / 7)))
            else:
                ancho_total = 76
        except Exception:
            ancho_total = 76
        encabezado = "TABLA NUTRIMENTAL MEXICANA".center(ancho_total)
        line = "="*ancho_total
        texto = f"{encabezado}\n{line}\n"
        if 'porciones_envase' in resultados and resultados['porciones_envase'] is not None:
            p = resultados['porciones_envase']
            try:
                p_disp = int(p) if float(p).is_integer() else round(float(p),1)
            except Exception:
                p_disp = p
            texto += f"Porciones por envase: {p_disp}\n"
        if 'por_envase' in resultados:
            texto += f"Energía total envase: {_int(resultados['por_envase'].get('energia_kcal',''))} kcal / {_int(resultados['por_envase'].get('energia_kj',''))} kJ\n"
        texto += "\n"
        tiene_porcion = bool(porcion_dict)
        # Ajustar proporciones de columnas según si hay columna de porción
        col_val = 9  # ancho numérico fijo
        if tiene_porcion:
            restante = ancho_total - (col_val * 2) - 2  # 2 espacios margen
        else:
            restante = ancho_total - col_val - 1
        # Limitar nombre a rango razonable
        col_nombre = max(25, min(55, restante))
        if tiene_porcion:
            titulo_cols = f"{'Componente':<{col_nombre}}{'100 '+unidad_base:>{col_val}}{'Porción':>{col_val}}"
        else:
            titulo_cols = f"{'Componente':<{col_nombre}}{'100 '+unidad_base:>{col_val}}"
        texto += titulo_cols + "\n" + "-"*len(titulo_cols) + "\n"
        for key, nombre, _u in filas:
            if key not in por100:
                continue
            v100 = _int(por100.get(key,0))
            if tiene_porcion:
                vpor = _int(porcion_dict.get(key,0))
                texto += f"{nombre:<{col_nombre}}{v100:>{col_val}}{vpor:>{col_val}}\n"
            else:
                texto += f"{nombre:<{col_nombre}}{v100:>{col_val}}\n"
        texto += "\n"
        sellos = self._calcular_sellos_advertencia(resultados)
        texto += "SELLOS DE ADVERTENCIA".center(ancho_total) + "\n"
        texto += "-"*ancho_total + "\n"
        if any(sellos.values()):
            if sellos.get('exceso_calorias'): texto += "EXCESO DE CALORÍAS\n"
            if sellos.get('exceso_azucares'): texto += "EXCESO DE AZÚCARES\n"
            if sellos.get('exceso_grasas_saturadas'): texto += "EXCESO DE GRASAS SATURADAS\n"
            if sellos.get('exceso_grasas_trans'): texto += "EXCESO DE GRASAS TRANS\n"
            if sellos.get('exceso_sodio'): texto += "EXCESO DE SODIO\n"
        else:
            texto += "No se requieren sellos.\n"
        self.parent.resultados_text.insert("1.0", texto)
        self.parent.resultados_text.config(state="disabled")

    def _get_label_text(self, key, es_liquida):
        """Devuelve el texto correcto para la etiqueta 'key' según si es líquida."""
        ref_unit = "100 mL" if es_liquida else "100 g"
        suf_g = f"(g/{ref_unit})"
        suf_mg = f"(mg/{ref_unit})"
        mapping = {
            # Humedad y Cenizas se piden como g por 100 g/mL
            "humedad": f"Humedad {suf_g}",
            "cenizas": f"Cenizas {suf_g}",
            "proteina": f"Proteína {suf_g}",
            "grasa_total": f"Grasa total {suf_g}",
            "grasa_trans": f"Grasas trans {suf_mg}",
            "fibra_dietetica": f"Fibra dietética {suf_g}",
            "azucares": f"Azúcares totales {suf_g}",
            "azucares_anadidos": f"Azúcares añadidos {suf_g}",
            "sodio": f"Sodio {suf_mg}",
            # Acidos grasos saturados es un porcentaje del total de grasa
            "acidos_grasos_saturados": "Ácidos grasos saturados (%)",
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

    # ================= LAYOUT RESPONSIVO =================
    def _apply_responsive_layout(self, initial=False):
        """Reorganiza columnas según ancho disponible.

        Breakpoints:
        - >= 1400px : 3 columnas (default)
        - 950px–1399px : 2 columnas (Resultados debajo)
        - < 950px : 1 columna (todas apiladas)
        """
        try:
            cont = self._responsive_parent
        except AttributeError:
            return
        if cont is None:
            return
        # Ancho efectivo dentro del canvas/scrollable
        try:
            width = cont.winfo_width()
        except Exception:
            return
        # Durante creación inicial width puede ser muy pequeño (<10); posponer
        if width < 50 and initial:
            cont.after(50, lambda: self._apply_responsive_layout(initial=False))
            return

        if width >= 1400:
            mode = '3'
        elif width >= 950:
            mode = '2'
        else:
            mode = '1'

        if mode == self._layout_mode and not initial:
            return  # sin cambios
        self._layout_mode = mode

        # Limpiar grid actual de columnas
        for f in (self._col_left, self._col_center, self._col_right):
            try:
                f.grid_forget()
            except Exception:
                pass

        # Reset configuraciones de columnas (limpiar indices previos)
        for i in range(0, 4):
            try:
                cont.grid_columnconfigure(i, weight=0)
            except Exception:
                pass

        padx = 5; pady = 5

        if mode == '3':
            cont.grid_columnconfigure(0, weight=1, uniform='col')
            cont.grid_columnconfigure(1, weight=1, uniform='col')
            cont.grid_columnconfigure(2, weight=2, uniform='col')  # dar más espacio a resultados
            self._col_left.grid(row=0, column=0, sticky='nsew', padx=padx, pady=pady)
            self._col_center.grid(row=0, column=1, sticky='nsew', padx=padx, pady=pady)
            self._col_right.grid(row=0, column=2, sticky='nsew', padx=padx, pady=pady)
        elif mode == '2':
            cont.grid_columnconfigure(0, weight=1, uniform='col')
            cont.grid_columnconfigure(1, weight=1, uniform='col')
            self._col_left.grid(row=0, column=0, sticky='nsew', padx=padx, pady=pady)
            self._col_center.grid(row=0, column=1, sticky='nsew', padx=padx, pady=pady)
            self._col_right.grid(row=1, column=0, columnspan=2, sticky='nsew', padx=padx, pady=pady)
        else:  # mode '1'
            cont.grid_columnconfigure(0, weight=1, uniform='col')
            self._col_left.grid(row=0, column=0, sticky='nsew', padx=padx, pady=pady)
            self._col_center.grid(row=1, column=0, sticky='nsew', padx=padx, pady=pady)
            self._col_right.grid(row=2, column=0, sticky='nsew', padx=padx, pady=pady)

        # Ajustar padding inferior de frame de botones si existe
        # (Se busca el frame de botones por convención grid row=1 initial; relocarlo al final)
        try:
            if hasattr(self, '_buttons_frame') and self._buttons_frame.winfo_exists():
                last_row = 0 if mode == '3' else (1 if mode == '2' else 2)
                self._buttons_frame.grid(row=last_row+1, column=0, columnspan=(3 if mode=='3' else (2 if mode=='2' else 1)), sticky='ew', pady=(10,10))
        except Exception:
            pass