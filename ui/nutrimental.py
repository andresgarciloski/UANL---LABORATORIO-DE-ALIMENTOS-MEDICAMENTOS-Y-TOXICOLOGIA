import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
import math
import datetime
"""Módulo de cálculo y visualización de Tabla Nutrimental.

Reglas implementadas (resumen):
1. Todos los nutrientes se muestran como enteros.
2. Redondeo general: HALF_UP (>=0.5 sube) aplicado sobre valor positivo.
3. Sodio (mg) con regla NOM escalonada (<5=0; 5–139 múltiplos de 5; ≥140 múltiplos de 10). Grasas trans (mg) se redondean HALF_UP (sin regla NOM) tanto por 100 g como por porción.
4. Grasas saturadas = grasa total * (%) saturados, luego HALF_UP.
5. Carbohidratos disponibles = (100 - (humedad + cenizas + proteína + grasa total) - fibra) con redondeo HALF_UP (según info.txt: hidratos totales = 100 - (humedad+cenizas+proteína+grasa); hidratos disponibles = hidratos totales - fibra).
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
from ui.base_interface import bind_mousewheel, _BG, _PRIMARY, _PRIMARY_DARK, _TEXT, _SECONDARY, _EMPHASIS
import tempfile
from core.exporter import NutrimentalExporter  # solo el exportador, no la lógica de sellos

class NutrimentalModule:
    def __init__(self, parent_window):
        self.parent = parent_window
        self.exporter = NutrimentalExporter(parent_window)
        # Paleta para tarjetas modernas
        self._CARD_BG = _BG
        self._CARD_BORDER = '#E0E3E6'
        self._CARD_HEADER_BG = _EMPHASIS  # sutil énfasis
        self._CARD_HEADER_FG = _PRIMARY
        self._CARD_HEADER_FONT = ("Segoe UI", 11, 'bold')
        self._CARD_BODY_FONT = ("Segoe UI", 10)

    # --- Helper visual para crear "cards" modernas ---
    def _create_card(self, parent, title, full_height=False):
        outer = tk.Frame(parent, bg=self._CARD_BG, highlightthickness=1, highlightbackground=self._CARD_BORDER, bd=0)
        pack_fill = 'both' if full_height else 'x'
        outer.pack(fill=pack_fill, expand=True, padx=10, pady=8)
        header = tk.Frame(outer, bg=self._CARD_HEADER_BG, bd=0)
        header.pack(fill='x')
        tk.Label(header, text=title, font=self._CARD_HEADER_FONT, fg=self._CARD_HEADER_FG, bg=self._CARD_HEADER_BG).pack(anchor='w', padx=10, pady=(6,6))
        body = tk.Frame(outer, bg=self._CARD_BG)
        body.pack(fill='both', expand=True, padx=10, pady=(0,10))
        return body

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
        """Construye una versión más moderna: encabezado + panel lateral (inputs) + panel de resultados."""
        # Limpia contenido previo
        for w in self.parent.content_frame.winfo_children():
            w.destroy()
        self._init_styles()

        root = tk.Frame(self.parent.content_frame, bg=_BG)
        root.pack(fill="both", expand=True)
        # Header con pseudo degradado simple (dos frames superpuestos)
        header = tk.Frame(root, bg=_PRIMARY, height=70, highlightthickness=0)
        header.pack(fill='x', side='top')
        header.grid_propagate(False)
        tk.Label(header, text="Tabla Nutrimental", bg=_PRIMARY, fg='white', font=("Segoe UI",18,'bold')).pack(anchor='w', padx=18, pady=(10,0))
        tk.Label(header, text="Ingresa los datos base y genera la tabla oficial.", bg=_PRIMARY, fg='white', font=("Segoe UI",10)).pack(anchor='w', padx=18, pady=(0,8))

        # Contenedor principal con PanedWindow (modern split)
        paned = ttk.Panedwindow(root, orient='horizontal')
        paned.pack(fill='both', expand=True)

        # Panel de entradas (scrollable)
        input_wrapper = tk.Frame(paned, bg=_BG)
        paned.add(input_wrapper, weight=3)
        inputs_canvas = tk.Canvas(input_wrapper, bg=_BG, highlightthickness=0, bd=0)
        inputs_scroll = ttk.Scrollbar(input_wrapper, orient='vertical', command=inputs_canvas.yview)
        inputs_canvas.pack(side='left', fill='both', expand=True)
        inputs_scroll.pack(side='right', fill='y')
        inner_inputs = tk.Frame(inputs_canvas, bg=_BG)
        win_id = inputs_canvas.create_window((0,0), window=inner_inputs, anchor='nw')
        inner_inputs.bind('<Configure>', lambda e: inputs_canvas.configure(scrollregion=inputs_canvas.bbox('all')))
        def _sync_width(e):
            try:
                inputs_canvas.itemconfig(win_id, width=e.width)
            except Exception:
                pass
        inputs_canvas.bind('<Configure>', _sync_width)
        bind_mousewheel(inputs_canvas, inner_inputs)

        # Agrupar secciones dentro del panel de inputs
        self._create_basic_fields(inner_inputs)
        self._create_nutrimental_fields(inner_inputs)

        # Panel de resultados
        results_panel = tk.Frame(paned, bg=_BG)
        paned.add(results_panel, weight=4)
        # Card resultados
        self._create_results_area(results_panel)

        # Barra inferior de acciones (flotante en panel resultados)
        actions = tk.Frame(results_panel, bg=_BG)
        actions.pack(fill='x', pady=(4,10))
        self._create_buttons(actions)

        # Ajustar un mínimo para que se perciba la división
        try:
            paned.sashpos(0, int(self.parent.winfo_width()*0.40))
        except Exception:
            pass

        # Guardar referencias mínimas para compatibilidad (no se usa layout responsivo previo)
        self._responsive_parent = None
        try:
            self._attach_tipo_trace()
        except Exception:
            pass

        # Decoración ligera: borde lateral al panel de resultados
        try:
            divider = tk.Frame(results_panel, bg=_SECONDARY, width=1)
            divider.place(relx=0, rely=0, relheight=1)
        except Exception:
            pass

        # Fin nueva versión



    # --- UI builders (sin lógica de exportación) ---
    def _create_basic_fields(self, parent):
        card_body = self._create_card(parent, "Información básica")
        card_body.columnconfigure(1, weight=1)
        frame_bg = self._CARD_BG
        lbl_cfg = {"foreground": _TEXT, "background": frame_bg, "font": ("Segoe UI",10,"bold")}
        # Fila 0
        tk.Label(card_body, text="N° de muestra:", **lbl_cfg).grid(row=0, column=0, sticky="w", padx=(2,8), pady=4)
        self.parent.nombre_entry = ttk.Entry(card_body, font=("Segoe UI",10), style="Input.TEntry")
        self.parent.nombre_entry.grid(row=0, column=1, padx=4, pady=4, sticky="ew")
        # Fila 1
        tk.Label(card_body, text="Descripción:", **lbl_cfg).grid(row=1, column=0, sticky="nw", padx=(2,8), pady=4)
        self.parent.descripcion_entry = tk.Text(card_body, font=("Segoe UI",10), height=3, bd=1, relief="solid")
        self.parent.descripcion_entry.grid(row=1, column=1, padx=4, pady=4, sticky="ew")
        # Fila 2
        tk.Label(card_body, text="Fecha:", **lbl_cfg).grid(row=2, column=0, sticky="w", padx=(2,8), pady=4)
        self.parent.fecha_entry = ttk.Entry(card_body, font=("Segoe UI",10), state="readonly")
        fecha_actual = datetime.datetime.now().strftime("%Y-%m-%d")
        self.parent.fecha_entry.config(state="normal"); self.parent.fecha_entry.insert(0, fecha_actual); self.parent.fecha_entry.config(state="readonly")
        self.parent.fecha_entry.grid(row=2, column=1, padx=4, pady=4, sticky="ew")
        # Fila 3
        tk.Label(card_body, text="Hora:", **lbl_cfg).grid(row=3, column=0, sticky="w", padx=(2,8), pady=4)
        self.parent.hora_entry = ttk.Entry(card_body, font=("Segoe UI",10), state="readonly")
        hora_actual = datetime.datetime.now().strftime("%H:%M:%S")
        self.parent.hora_entry.config(state="normal"); self.parent.hora_entry.insert(0, hora_actual); self.parent.hora_entry.config(state="readonly")
        self.parent.hora_entry.grid(row=3, column=1, padx=4, pady=4, sticky="ew")
        # Sección tipo de muestra como sub-card visual dentro
        sub_frame = tk.Frame(card_body, bg=frame_bg)
        sub_frame.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(8,2))
        tk.Label(sub_frame, text="Tipo de muestra", bg=frame_bg, fg=_PRIMARY, font=("Segoe UI",9,'bold')).pack(anchor='w', pady=(0,4))
        radios = tk.Frame(sub_frame, bg=frame_bg)
        radios.pack(anchor='w')
        self.parent.tipo_muestra = tk.StringVar(value="solida")
        tk.Radiobutton(radios, text="Sólida", variable=self.parent.tipo_muestra, value="solida", bg=frame_bg, fg=_TEXT, selectcolor=_BG, font=("Segoe UI",10)).pack(side="left", padx=(0,10))
        tk.Radiobutton(radios, text="Líquida", variable=self.parent.tipo_muestra, value="liquida", bg=frame_bg, fg=_TEXT, selectcolor=_BG, font=("Segoe UI",10)).pack(side="left", padx=(0,10))
        self.parent.bebida_sin_calorias = tk.BooleanVar(value=False)
        tk.Checkbutton(radios, text="Es bebida sin calorías", variable=self.parent.bebida_sin_calorias, bg=frame_bg, fg=_TEXT, selectcolor=_BG, font=("Segoe UI",10)).pack(side="left", padx=(0,10))

    def _create_nutrimental_fields(self, parent):
        nutri_frame = self._create_card(parent, "Datos nutricionales")
        for c in range(0, 4):
            nutri_frame.columnconfigure(c, weight=1, uniform='nutri')
        self.parent.nutri_vars = {}
        self.parent.nutri_label_widgets = {}

        tipo_var = getattr(self.parent, "tipo_muestra", None)
        es_liquida = False
        try:
            if tipo_var is not None and tipo_var.get() == "liquida":
                es_liquida = True
        except Exception:
            es_liquida = False

        nutri_keys = [
            "humedad", "cenizas", "proteina", "grasa_total",
            "grasa_trans", "fibra_dietetica", "azucares", "azucares_anadidos",
            "sodio", "acidos_grasos_saturados", "porcion", "contenido_neto"
        ]

        for idx, key in enumerate(nutri_keys):
            col = (idx % 2) * 2
            row = idx // 2
            label_text = self._get_label_text(key, es_liquida)
            lbl = tk.Label(nutri_frame, text=label_text, bg=self._CARD_BG, fg=_TEXT, font=("Segoe UI",10,"bold"))
            lbl.grid(row=row, column=col, sticky="w", padx=(4,4), pady=5)
            entry = ttk.Entry(nutri_frame, font=("Segoe UI",10), style="Input.TEntry")
            entry.grid(row=row, column=col+1, sticky="ew", padx=(0,8), pady=5)
            self.parent.nutri_vars[key] = entry
            self.parent.nutri_label_widgets[key] = lbl

    def _create_results_area(self, parent):
        wrapper = self._create_card(parent, "Resultados", full_height=True)
        wrapper.rowconfigure(0, weight=1)
        wrapper.columnconfigure(0, weight=1)
        container = tk.Frame(wrapper, bg=self._CARD_BG)
        container.grid(row=0, column=0, sticky='nsew')
        self.parent.resultados_text = tk.Text(
            container,
            font=("Consolas",10),
            bg=self._CARD_BG, fg="#212121", state="disabled", relief="flat", bd=0,
            wrap="none"
        )
        resultados_scroll = tk.Scrollbar(container, orient="vertical", command=self.parent.resultados_text.yview)
        self.parent.resultados_text.configure(yscrollcommand=resultados_scroll.set)
        self.parent.resultados_text.pack(side="left", fill="both", expand=True, padx=0, pady=0)
        resultados_scroll.pack(side="right", fill="y")
        try:
            self.parent.resultados_text.tag_config('titulo', font=("Segoe UI",11,"bold"), foreground=_PRIMARY)
            self.parent.resultados_text.tag_config('subtitulo', font=("Segoe UI",9), foreground=_TEXT)
            self.parent.resultados_text.tag_config('sellos', font=("Segoe UI",10,"bold"), foreground='#C62828')
        except Exception:
            pass

    def _create_buttons(self, parent):
        """Crea botones estilizados (solo visual)."""
        btn_bar = tk.Frame(parent, bg=_BG)
        btn_bar.pack()
        calc_btn = ttk.Button(
            btn_bar,
            text="Calcular",
            command=self.calcular_tabla_nutrimental,
            style="Primary.TButton",
            width=18
        )
        calc_btn.pack(side="left", padx=6, pady=4)
        guardar_bd_btn = ttk.Button(
            btn_bar,
            text="Guardar en BD",
            command=self.exporter.guardar_solo_bd,
            style="Secondary.TButton",
            width=18
        )
        guardar_bd_btn.pack(side="left", padx=6, pady=4)

    # --------- Estilos (visual only) ---------
    def _init_styles(self):
        if getattr(self, '_styles_inited', False):
            return
        try:
            style = ttk.Style()
            # Usar tema clam si disponible para mejor personalización
            try:
                style.theme_use('clam')
            except Exception:
                pass
            card_bg = _BG
            sub_bg = '#F5F5F5'
            style.configure('Card.TLabelframe', background=card_bg, foreground=_PRIMARY, borderwidth=1, relief='solid')
            style.configure('Card.TLabelframe.Label', background=card_bg, foreground=_PRIMARY, font=("Segoe UI",11,"bold"))
            style.configure('SubCard.TLabelframe', background=sub_bg, foreground=_PRIMARY, borderwidth=1, relief='solid')
            style.configure('SubCard.TLabelframe.Label', background=sub_bg, foreground=_PRIMARY, font=("Segoe UI",9,"bold"))
            style.configure('Primary.TButton', background=_PRIMARY, foreground='white', font=("Segoe UI",10,'bold'), padding=(10,6))
            style.map('Primary.TButton', background=[('active', _PRIMARY_DARK)])
            style.configure('Secondary.TButton', background=_TEXT, foreground='white', font=("Segoe UI",10,'bold'), padding=(10,6))
            style.map('Secondary.TButton', background=[('active', _PRIMARY_DARK)])
            style.configure('Input.TEntry', fieldbackground=_BG, background=_BG)
        except Exception:
            pass
        self._styles_inited = True

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

    def _aplicar_redondeo_energia(self, valor_kcal):
        """Redondea energía a múltiplo de 10 kcal (regla usada para 100 g y por porción)."""
        try:
            v = float(valor_kcal)
        except Exception:
            return 0
        return int(round(v / 10.0) * 10)

    def _round_half_up_05(self, val):
        """Redondea HALF_UP a pasos de 0.5 (ej. 0.0, 0.5, 1.0, ...). Devuelve float."""
        from decimal import Decimal, ROUND_HALF_UP
        try:
            v = float(val)
        except Exception:
            return 0.0
        return float(Decimal(str(v)).quantize(Decimal('0.5'), rounding=ROUND_HALF_UP))

    def _calcular_nutrimental(self, data):
        """Calcula los valores nutrimentales siguiendo las reglas establecidas.

        Pasos clave:
        1) Se toman valores crudos (por 100 g/mL) provenientes de análisis.
        2) Se calculan derivados crudos (grasa saturada, hidratos totales / disponibles).
        3) Se aplican redondeos HALF_UP a todos los nutrientes salvo sodio (regla NOM).
        4) Energía se calcula usando los valores ya redondeados y se ajusta a múltiplo de 10 kcal.
        5) Valores por porción: se escalan desde los enteros por 100 g para todos menos sodio y trans:
           - Sodio por porción: se recalcula desde el valor crudo (mg) * factor y se aplica regla NOM.
           - Grasas trans por porción: crudo*factor con HALF_UP directo (sin regla NOM para evitar 0 cuando debe ser 2 mg).
        6) Por envase (si contenido neto) se escalan energías (enteros).
        7) Se marca warning si la suma de componentes excede tolerancia (>101%).
        """
        aviso_componentes_excedidos = False
        half_up = self._round_half_up

        # 1. Valores crudos
        def _f(key):
            try:
                return float(data.get(key, 0) or 0)
            except Exception:
                return 0.0
        proteina_raw = _f('proteina')
        grasa_total_raw = _f('grasa_total')
        fibra_raw = _f('fibra_dietetica')
        azucares_raw = _f('azucares')
        azucares_anadidos_raw = _f('azucares_anadidos')
        humedad_raw = _f('humedad')
        cenizas_raw = _f('cenizas')
        acidos_sat_pct = _f('acidos_grasos_saturados')
        sodio_raw = _f('sodio')          # mg
        grasa_trans_raw = _f('grasa_trans')  # mg

        # 2. Derivados crudos
        grasa_saturada_cruda = grasa_total_raw * acidos_sat_pct / 100.0 if grasa_total_raw and acidos_sat_pct else 0.0
        hidratos_totales_raw = 100 - (humedad_raw + cenizas_raw + proteina_raw + grasa_total_raw)
        carbo_balance_raw = hidratos_totales_raw - fibra_raw
        if carbo_balance_raw < 0:
            carbo_balance_raw = 0

        # 3. Redondeos por 100 g/mL
        humedad_100g = half_up(humedad_raw)
        cenizas_100g = half_up(cenizas_raw)
        proteina_100g = half_up(proteina_raw)
        grasa_total_100g = half_up(grasa_total_raw)
        fibra_dietetica_100g = half_up(fibra_raw)
        azucares_100g = half_up(azucares_raw)
        azucares_anadidos_100g = half_up(azucares_anadidos_raw)
        # Redondeo de grasa saturada a pasos de 0.5 g (mantener float)
        grasa_saturada_100g = self._round_half_up_05(grasa_saturada_cruda) if grasa_saturada_cruda else 0.0
        carbohidratos_disponibles_100g = half_up(carbo_balance_raw)
        sodio_100g = self._aplicar_regla_redondeo_sodio(sodio_raw)
        grasa_trans_100g = half_up(grasa_trans_raw)

        # Chequeo heurístico de suma
        total_componentes_base = humedad_raw + cenizas_raw + proteina_raw + grasa_total_raw + fibra_raw
        if total_componentes_base > 101:  # tolerancia 1%
            aviso_componentes_excedidos = True

        # 4. Energía por 100 g/mL (usar valores redondeados) y redondear a múltiplo de 10 kcal
        energia_kcal_100g = (proteina_100g + carbohidratos_disponibles_100g) * 4 + grasa_total_100g * 9
        energia_kcal_100g = self._aplicar_redondeo_energia(energia_kcal_100g)
        energia_kj_100g = (proteina_100g + carbohidratos_disponibles_100g) * 17 + grasa_total_100g * 37

        # 5. Por porción
        porcion = _f('porcion')
        factor = porcion / 100.0 if porcion else 0
        proteina_porcion = half_up(proteina_100g * factor)
        grasa_total_porcion = half_up(grasa_total_100g * factor)
        # Use raw saturated-fat amount scaled by portion, luego redondeo a 0.5 g
        grasa_saturada_porcion = self._round_half_up_05(grasa_saturada_cruda * factor) if grasa_saturada_cruda else 0.0
        fibra_dietetica_porcion = half_up(fibra_dietetica_100g * factor)
        azucares_porcion = half_up(azucares_100g * factor)
        azucares_anadidos_porcion = half_up(azucares_anadidos_100g * factor)
        carbohidratos_disponibles_porcion = half_up(carbohidratos_disponibles_100g * factor)
        sodio_porcion = self._aplicar_regla_redondeo_sodio(sodio_raw * factor)
        grasa_trans_porcion = half_up(grasa_trans_raw * factor)
        energia_kcal_porcion = (proteina_porcion + carbohidratos_disponibles_porcion) * 4 + grasa_total_porcion * 9
        energia_kcal_porcion = self._aplicar_redondeo_energia(energia_kcal_porcion)
        energia_kj_porcion = (proteina_porcion + carbohidratos_disponibles_porcion) * 17 + grasa_total_porcion * 37

        # 6. Por envase (opcional)
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

        # 7. Armar resultado
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
            "contenido_neto": f"Contenido neto({'mL' if es_liquida else 'g'})"
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