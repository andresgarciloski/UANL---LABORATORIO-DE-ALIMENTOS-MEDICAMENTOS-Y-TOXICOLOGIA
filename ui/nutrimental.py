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
8. Valores por porción se derivan de los valores crudos por 100 g/mL (NO desde los enteros), excepto reglas especiales (sodio y trans).
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
# NUEVO: utilidades para validación
import re, time
import threading
from ui.loading import LoadingOverlay
from core.calculos import calcular_nutrimental, calcular_sellos_advertencia

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
        # NUEVO: estado de validación y throttling de avisos
        self._vcmd_num = self._ivcmd_num = self._vcmd_int = self._ivcmd_int = None
        self._last_warn_num = 0.0
        self._last_warn_desc = 0.0
        self._warn_cooldown = 0.9

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
        # Validar longitud mínima de Descripción
        if not self._check_description_min_length():
            return
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
            datos_basicos = {'nombre': nombre, 'descripcion': descripcion}
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
        # NUEVO: inicializar validadores de entradas
        self._init_validation()

        root = tk.Frame(self.parent.content_frame, bg=_BG)
        root.pack(fill="both", expand=True)
        
        # CONTENEDOR FIJO SIN PANEDWINDOW
        content = tk.Frame(root, bg=_BG)
        content.pack(fill='both', expand=True)
        content.columnconfigure(0, weight=1, uniform='split')  # mitad izquierda
        content.columnconfigure(1, weight=1, uniform='split')  # mitad derecha
        content.rowconfigure(0, weight=1)     # NUEVO: que ambos paneles aprovechen el alto

        # Panel izquierdo con scroll (define inner_inputs)
        input_wrapper = tk.Frame(content, bg=_BG)
        input_wrapper.grid(row=0, column=0, sticky='nsew')
        inputs_canvas = tk.Canvas(input_wrapper, bg=_BG, highlightthickness=0, bd=0)
        inputs_scroll = ttk.Scrollbar(input_wrapper, orient='vertical', command=inputs_canvas.yview)
        inputs_canvas.configure(yscrollcommand=inputs_scroll.set)
        inputs_canvas.pack(side='left', fill='both', expand=True)
        inputs_scroll.pack(side='right', fill='y')
        inner_inputs = tk.Frame(inputs_canvas, bg=_BG)
        win_id = inputs_canvas.create_window((0, 0), window=inner_inputs, anchor='nw')
        inner_inputs.bind('<Configure>', lambda e: inputs_canvas.configure(scrollregion=inputs_canvas.bbox('all')))
        inputs_canvas.bind('<Configure>', lambda e: inputs_canvas.itemconfig(win_id, width=e.width))
        bind_mousewheel(inputs_canvas, inner_inputs)

        # Agrupar secciones dentro del panel de inputs
        self._create_basic_fields(inner_inputs)
        self._create_nutrimental_fields(inner_inputs)

        # NUEVO: que las etiquetas de los campos se adapten y no se corten
        self._enable_label_autowrap(inner_inputs)

        # Botón "Calcular" centrado debajo de Datos nutricionales (panel izquierdo)
        left_actions = tk.Frame(inner_inputs, bg=_BG)
        left_actions.pack(fill='x', padx=10, pady=(0, 10))
        tk.Frame(left_actions, bg=_BG).pack()  # separador fino
        calc_btn_left = ttk.Button(
            left_actions,
            text="Calcular",
            command=self.calcular_tabla_nutrimental,
            style="Primary.TButton",
            width=18
        )
        calc_btn_left.pack(anchor='center', pady=4)
        # Deshabilitado hasta que los campos estén completos
        self._btn_calcular = calc_btn_left
        try:
            self._btn_calcular.state(['disabled'])
        except Exception:
            pass

        # Panel de resultados (50% del ancho, todo el alto)
        results_panel = tk.Frame(content, bg=_BG)
        results_panel.grid(row=0, column=1, sticky='nsew')
        # NUEVO: que ocupe todo el alto
        results_panel.grid_propagate(False)

        # Card resultados
        self._create_results_area(results_panel)

        # Barra inferior de acciones (en panel resultados)
        actions = tk.Frame(results_panel, bg=_BG)
        actions.pack(fill='x', pady=(4,10))
        self._create_buttons(actions)

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
        # NUEVO: permite letras/números/símbolos; validación mínima por longitud
        self.parent.nombre_entry = ttk.Entry(
            card_body, font=("Segoe UI",10), style="Input.TEntry"
        )
        self.parent.nombre_entry.grid(row=0, column=1, padx=4, pady=4, sticky="ew")
        # Actualizar estado del botón y validar longitud mínima
        self.parent.nombre_entry.bind("<KeyRelease>", lambda e: self._update_calc_button())
        self.parent.nombre_entry.bind("<<Paste>>", lambda e: self.parent.after(0, self._update_calc_button), add="+")
        self.parent.nombre_entry.bind("<FocusOut>", lambda e: self._check_nombre_min_length())
        # Fila 1
        tk.Label(card_body, text="Descripción:", **lbl_cfg).grid(row=1, column=0, sticky="nw", padx=(2,8), pady=4)
        self.parent.descripcion_entry = tk.Text(card_body, font=("Segoe UI",10), height=3, bd=1, relief="solid")
        self.parent.descripcion_entry.grid(row=1, column=1, padx=4, pady=4, sticky="ew")
        # NUEVO: sanitizar y validar
        self.parent.descripcion_entry.bind("<KeyRelease>", lambda e: self._sanitize_description())
        self.parent.descripcion_entry.bind("<<Paste>>", lambda e: self.parent.after(0, self._sanitize_description))
        self.parent.descripcion_entry.bind("<FocusOut>", lambda e: self._check_description_min_length())
        # También actualizar estado del botón cuando cambie
        self.parent.descripcion_entry.bind("<KeyRelease>", lambda e: self._update_calc_button(), add="+")
        self.parent.descripcion_entry.bind("<<Paste>>", lambda e: self.parent.after(0, self._update_calc_button), add="+")
        self.parent.descripcion_entry.bind("<FocusOut>", lambda e: self._update_calc_button(), add="+")
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
            # NUEVO: solo números (decimales con punto)
            entry = ttk.Entry(
                nutri_frame, font=("Segoe UI",10), style="Input.TEntry",
                validate="key", validatecommand=self._vcmd_num, invalidcommand=self._ivcmd_num
            )
            entry.grid(row=row, column=col+1, sticky="ew", padx=(0,8), pady=5)
            # Actualizar estado del botón al escribir/pegar
            entry.bind("<KeyRelease>", lambda e: self._update_calc_button(), add="+")
            entry.bind("<<Paste>>", lambda e: self.parent.after(0, self._update_calc_button), add="+")
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
        # NUEVO: Guardar (verde) y Limpiar (azul)
        guardar_bd_btn = ttk.Button(
            btn_bar,
            text="Guardar",
            command=self._guardar_con_loading,
            style="Success.TButton",
            width=18
        )
        guardar_bd_btn.pack(side="left", padx=6, pady=4)
        limpiar_btn = ttk.Button(
            btn_bar,
            text="Limpiar",
            command=self.limpiar_campos,
            style="Info.TButton",
            width=18
        )
        limpiar_btn.pack(side="left", padx=6, pady=4)

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
            # Rojo por defecto; gris cuando está deshabilitado
            style.map('Primary.TButton',
                      background=[('disabled', '#BDBDBD'), ('active', _PRIMARY_DARK)],
                      foreground=[('disabled', '#EEEEEE')])
            # NUEVO: estilos de botones Guardar (verde) y Limpiar (azul)
            style.configure('Success.TButton', background='#3ECF36', foreground='white', font=("Segoe UI",10,'bold'), padding=(10,6))
            style.map('Success.TButton', background=[('active', '#3ECF36')])
            style.configure('Info.TButton', background='#1E88E5', foreground='white', font=("Segoe UI",10,'bold'), padding=(10,6))
            style.map('Info.TButton', background=[('active', '#42A5F5')])
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
        """Delegador a core.calculos.calcular_nutrimental"""
        try:
            res = calcular_nutrimental(data)
        except Exception:
            return {}
        # FIX: grasa saturada, energía y porción calculados desde crudos
        try:
            res = self._fix_grasa_saturada_desde_porcentaje(res, data)
            res = self._fix_energia_desde_enteros(res, data)
            res = self._fix_porcion_desde_crudos(res, data)  # <--- NUEVO
            return res
        except Exception:
            return res

    def _calcular_sellos_advertencia(self, resultados):
        """Delegador a core.calculos.calcular_sellos_advertencia"""
        try:
            tipo_var = getattr(self.parent, "tipo_muestra", None)
            es_liquida = False
            try:
                if tipo_var is not None and tipo_var.get() == "liquida":
                    es_liquida = True
            except Exception:
                es_liquida = False
            es_bebida_sin_calorias = getattr(self.parent, "bebida_sin_calorias", None) and self.parent.bebida_sin_calorias.get()
            return calcular_sellos_advertencia(resultados, es_liquida=es_liquida, es_bebida_sin_calorias=es_bebida_sin_calorias)
        except Exception:
            return {
                "exceso_calorias": False,
                "exceso_azucares": False,
                "exceso_grasas_saturadas": False,
                "exceso_grasas_trans": False,
                "exceso_sodio": False
            }

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
        """Layout responsivo (no usado actualmente)."""
        pass

    # ================= VALIDACIÓN (solo lo pedido) =================
    def _init_validation(self):
        """Registra validadores para numéricos, enteros y sanitiza Descripción."""
        try:
            reg = self.parent.register
            self._vcmd_num = (reg(self._validate_number), "%P", "%W")
            self._ivcmd_num = (reg(self._on_invalid_number), "%W")
            self._vcmd_int = (reg(self._validate_integer), "%P", "%W")
            self._ivcmd_int = (reg(self._on_invalid_integer), "%W")
        except Exception:
            self._vcmd_num = self._ivcmd_num = self._vcmd_int = self._ivcmd_int = None

    def _validate_number(self, proposed: str, widget_path: str) -> bool:
        """Permite solo números con punto decimal opcional. Vacío permitido para poder borrar."""
        if proposed == "":
            return True
        return re.fullmatch(r"\d*\.?\d*", proposed) is not None and proposed.count(".") <= 1

    def _on_invalid_number(self, widget_path: str):
        """Aviso cuando se intenta ingresar letras en campos numéricos."""
        now = time.monotonic()
        if now - self._last_warn_num >= self._warn_cooldown:
            self._last_warn_num = now
            try:
                self.parent.bell()
                messagebox.showwarning("Entrada inválida", "Solo se permiten números (usa punto para decimales).")
            except Exception:
                pass
        return False

    def _validate_integer(self, proposed: str, widget_path: str) -> bool:
        """Solo enteros positivos. Vacío permitido para poder borrar."""
        if proposed == "":
            return True
        return re.fullmatch(r"\d+", proposed) is not None

    def _on_invalid_integer(self, widget_path: str):
        """Aviso para campos enteros (N° de muestra)."""
        now = time.monotonic()
        if now - self._last_warn_num >= self._warn_cooldown:
            self._last_warn_num = now
            try:
                self.parent.bell()
                messagebox.showwarning("Entrada inválida", "Este campo solo acepta números enteros.")
            except Exception:
                pass
        return False

    def _sanitize_description(self):
        """Descripción: solo letras, números y espacios (incluye acentos y ñ)."""
        try:
            txt = self.parent.descripcion_entry.get("1.0", "end-1c")
        except Exception:
            return
        cleaned = re.sub(r"[^A-Za-zÁÉÍÓÚáéíóúÑñ0-9 ]+", "", txt)
        if cleaned != txt:
            try:
                self.parent.descripcion_entry.delete("1.0", "end")
                self.parent.descripcion_entry.insert("1.0", cleaned)
            except Exception:
                pass
            now = time.monotonic()
            if now - self._last_warn_desc >= self._warn_cooldown:
                self._last_warn_desc = now
                try:
                    self.parent.bell()
                    messagebox.showwarning("Texto inválido", "Descripción solo permite letras y números (y espacios).")
                except Exception:
                    pass
        return cleaned

    def _check_description_min_length(self) -> bool:
        """Valida que Descripción tenga mínimo 5 caracteres (tras sanitizar)."""
        try:
            text = (self._sanitize_description() or "").strip()
        except Exception:
            return True
        ok = len(text) >= 5
        try:
            # feedback visual suave
            self.parent.descripcion_entry.config(bg=("white" if ok else "#FFF5F5"))
        except Exception:
            pass
        if not ok:
            try:
                self.parent.bell()
                messagebox.showwarning("Descripción muy corta", "La descripción debe tener al menos 5 caracteres.")
                self.parent.descripcion_entry.focus_set()
            except Exception:
                pass
        return ok

    # NUEVO: validación para N° de muestra (mínimo 5 caracteres, cualquier símbolo permitido)
    def _check_nombre_min_length(self) -> bool:
        try:
            s = self.parent.nombre_entry.get().strip()
        except Exception:
            return True
        ok = len(s) >= 5
        if not ok:
            try:
                self.parent.bell()
                messagebox.showwarning("Dato inválido", 'El campo "N° de muestra" debe tener al menos 5 caracteres.')
                self.parent.nombre_entry.focus_set()
            except Exception:
                pass
        return ok

    def limpiar_campos(self):
        """Limpia todos los campos del formulario y el panel de resultados."""
        try:
            # Básicos
            if hasattr(self.parent, 'nombre_entry'):
                self.parent.nombre_entry.delete(0, 'end')
            if hasattr(self.parent, 'descripcion_entry'):
                self.parent.descripcion_entry.delete('1.0', 'end')

            # Datos nutricionales
            for entry in getattr(self.parent, 'nutri_vars', {}).values():
                try:
                    entry.delete(0, 'end')
                except Exception:
                    pass

            # Resultados
            if hasattr(self.parent, 'resultados_text'):
                self.parent.resultados_text.config(state='normal')
                self.parent.resultados_text.delete('1.0', 'end')
                self.parent.resultados_text.config(state='disabled')

            # Estado de último cálculo (opcional)
            try:
                self.parent.ultimo_calculo = None
            except Exception:
                pass
        except Exception:
            pass

        # Deshabilitar botón "Calcular" (volver a gris) tras limpiar
        try:
            if hasattr(self, "_btn_calcular") and self._btn_calcular:
                self._btn_calcular.state(['disabled'])
        except Exception:
            pass
        # Revalidar por si hay lógica adicional basada en entradas
        try:
            self._update_calc_button()
        except Exception:
            pass

    # ---------- Habilitar/Deshabilitar "Calcular" ----------
    def _inputs_complete_and_valid(self) -> bool:
        """Nombre (min 5 carac.), Descripción >=5, y todos los nutrimentales numéricos y no vacíos."""
        # Nombre
        try:
            txt = self.parent.nombre_entry.get().strip()
            if len(txt) < 5:
                return False
        except Exception:
            return False
        # Descripción
        try:
            desc = self.parent.descripcion_entry.get("1.0", "end-1c").strip()
            if len(desc) < 5:
                return False
        except Exception:
            return False
        # Nutrimentales
        try:
            for entry in getattr(self.parent, 'nutri_vars', {}).values():
                s = entry.get().strip()
                if s == "":
                    return False
                float(s)  # valida numérico (con decimales)
        except Exception:
            return False
        return True

    def _update_calc_button(self):
        """Actualiza el estado del botón Calcular según completitud/validez."""
        try:
            btn = getattr(self, "_btn_calcular", None)
            if not btn:
                return
            if self._inputs_complete_and_valid():
                btn.state(['!disabled'])
            else:
                btn.state(['disabled'])
        except Exception:
            pass

    def _guardar_con_loading(self):
        """Muestra overlay de carga mientras se guarda en BD y lo cierra al mostrar el mensaje de resultado."""
        # Crear overlay
        try:
            overlay = LoadingOverlay(self.parent)
            overlay.show()
        except Exception:
            overlay = None

        # Parche temporal de messagebox para cerrar overlay antes de mostrar cualquier diálogo
        orig_info = messagebox.showinfo
        orig_err = messagebox.showerror
        orig_warn = messagebox.showwarning

        def _wrap_dialog(orig_func):
            def _wrapped(title, message, *a, **k):
                def _do():
                    # cerrar overlay justo antes de mostrar el diálogo
                    try:
                        if overlay:
                            overlay.close()
                    except Exception:
                        pass
                    try:
                        orig_func(title, message, *a, **k)
                    except Exception:
                        pass
                # asegurar que el diálogo se ejecute en el hilo principal de Tk
                try:
                    self.parent.after(0, _do)
                except Exception:
                    _do()
                return ""  # resultado no usado
            return _wrapped

        messagebox.showinfo = _wrap_dialog(orig_info)
        messagebox.showerror = _wrap_dialog(orig_err)
        messagebox.showwarning = _wrap_dialog(orig_warn)

        # Ejecutar guardado en hilo
        def run():
            try:
                self.exporter.guardar_solo_bd()
            except Exception as e:
                def _notify_err():
                    try:
                        if overlay:
                            overlay.close()
                    except Exception:
                        pass
                    try:
                        orig_err("Error", f"No se pudo completar el guardado.\n{e}")
                    except Exception:
                        pass
                self.parent.after(0, _notify_err)
            finally:
                # Restaurar messagebox y asegurar cierre del overlay
                def _restore():
                    try:
                        messagebox.showinfo = orig_info
                        messagebox.showerror = orig_err
                        messagebox.showwarning = orig_warn
                    except Exception:
                        pass
                    try:
                        if overlay:
                            overlay.close()
                    except Exception:
                        pass
                self.parent.after(0, _restore)

        threading.Thread(target=run, daemon=True).start()

    # ================== NUEVO: autowrap en etiquetas de inputs ==================
    def _enable_label_autowrap(self, root_container):
        """Hace que las Label dentro de los formularios envuelvan el texto según su ancho.
        Evita los headers (bg=_PRIMARY y bg de header de card). Se aplica recursivamente."""
        import tkinter as tk

        # No aplicar autowrap a labels de headers
        header_bgs = {_PRIMARY, self._CARD_HEADER_BG}

        def _apply(lbl: tk.Label):
            # Configurar el wrap y actualizarlo cuando cambie el tamaño
            def _upd(_e=None, _l=lbl):
                try:
                    w = _l.winfo_width()
                    if w <= 1:
                        w = _l.winfo_reqwidth()
                    w = max(80, w - 8)  # margen visual
                    _l.configure(wraplength=w, justify='left')
                except Exception:
                    pass
            lbl.bind('<Configure>', _upd)
            lbl.after(50, _upd)

        def _walk(widget):
            for child in widget.winfo_children():
                try:
                    is_label = child.winfo_class() == 'Label'
                    bg = child.cget('bg') if is_label else None
                except Exception:
                    is_label = False
                    bg = None
                # Evitar aplicar a headers
                if is_label and bg not in header_bgs:
                    _apply(child)
                # Recurse
                _walk(child)

        _walk(root_container)

    def _fix_grasa_saturada_desde_porcentaje(self, resultados: dict, data: dict) -> dict:
        """
        Recalcula 'grasa_saturada' a partir del % de ácidos grasos saturados (AGS)
        ingresado por el usuario.

        grasa_saturada_100g = ROUND_HALF_UP(grasa_total * (AGS%/100))
        grasa_saturada_porcion = ROUND_HALF_UP(grasa_saturada_100g * (porcion/100))
        """
        # datos crudos del formulario
        try:
            gt = float((data.get('grasa_total') or '0').replace(',', '.'))
        except Exception:
            gt = 0.0
        try:
            ags_pct = float((data.get('acidos_grasos_saturados') or '0').replace(',', '.'))
        except Exception:
            ags_pct = 0.0
        try:
            porcion = float((data.get('porcion') or '0').replace(',', '.'))
        except Exception:
            porcion = 0.0

        # por 100 g/mL
        g_sat_100 = self._round_half_up(max(0.0, gt * (ags_pct / 100.0)))
        por_100 = resultados.setdefault('por_100g', {})
        por_100['grasa_saturada'] = g_sat_100

        # por porción (derivado del entero de 100 g/mL)
        if porcion > 0:
            g_sat_porcion = self._aplicar_redondeo_nutrientes_porcion(g_sat_100 * (porcion / 100.0))
            resultados.setdefault('por_porcion', {})['grasa_saturada'] = g_sat_porcion

        return resultados

    def _fix_energia_desde_enteros(self, resultados: dict, data: dict) -> dict:
        """
        Energía (kcal/kJ):
        - Por 100 g/mL: usar nutrimentos ENTEROS por 100 g/mL.
        - Por porción: calcular desde valores CRUDOS por 100 g/mL (no desde los enteros).
        - Por envase: escalar desde la energía por 100 g/mL.
        """
        por100 = resultados.setdefault('por_100g', {})
        # Enteros por 100 g
        p100 = self._round_half_up(por100.get('proteina', 0))
        c100 = self._round_half_up(por100.get('carbohidratos_disponibles', 0))
        g100 = self._round_half_up(por100.get('grasa_total', 0))

        # Energía por 100 g (enteros)
        kcal_100 = (p100 + c100) * 4 + g100 * 9
        kj_100 = (p100 + c100) * 17 + g100 * 37
        por100['energia_kcal'] = self._round_half_up(kcal_100)
        por100['energia_kj'] = self._round_half_up(kj_100)

        # Porción: desde CRUDOS
        def _f(k):
            try:
                return float((data.get(k) or '0').replace(',', '.'))
            except Exception:
                return 0.0

        try:
            porcion = float((data.get('porcion') or '0').replace(',', '.'))
        except Exception:
            porcion = 0.0

        if porcion > 0 and not resultados.get('es_porcion_100g', False):
            # crudos por 100 g
            prot = _f('proteina')
            grasa = _f('grasa_total')
            fibra = _f('fibra_dietetica')
            hum = _f('humedad')
            cen = _f('cenizas')
            carbs_disp = max(0.0, (100.0 - (hum + cen + prot + grasa)) - fibra)

            factor = porcion / 100.0
            p_por = self._aplicar_redondeo_nutrientes_porcion(prot * factor)
            c_por = self._aplicar_redondeo_nutrientes_porcion(carbs_disp * factor)
            g_por = self._aplicar_redondeo_nutrientes_porcion(grasa * factor)

            kcal_por = (p_por + c_por) * 4 + g_por * 9
            kj_por = (p_por + c_por) * 17 + g_por * 37

            pp = resultados.setdefault('por_porcion', {})
            # ANTES: setdefault(...) no sobrescribía
            pp['energia_kcal'] = self._round_half_up(kcal_por)
            pp['energia_kj'] = self._round_half_up(kj_por)

        # Envase (desde energía por 100 g)
        try:
            neto = float((data.get('contenido_neto') or '0').replace(',', '.'))
        except Exception:
            neto = 0.0
        if neto > 0:
            factor = neto / 100.0
            kcal_env = self._round_half_up(kcal_100 * factor)
            kj_env = self._round_half_up(kj_100 * factor)
            env = resultados.setdefault('por_envase', {})
            env['energia_kcal'] = kcal_env
            env['energia_kj'] = kj_env
            try:
                if 'porciones_envase' not in resultados and porcion > 0:
                    resultados['porciones_envase'] = neto / porcion
            except Exception:
                pass

        return resultados

    def _fix_porcion_desde_crudos(self, resultados: dict, data: dict) -> dict:
        """
        Recalcula TODOS los nutrimentos 'por porción' desde los valores crudos por 100 g,
        no desde los enteros de 100 g. Reglas:
          - g: HALF_UP a entero.
          - Sodio (mg): regla NOM escalonada.
          - Grasas trans (mg): HALF_UP a entero.
          - Carbohidratos disponibles crudos = (100 - (hum+cen+prot+grasa)) - fibra.
        """
        try:
            porcion = float((data.get('porcion') or '0').replace(',', '.'))
        except Exception:
            porcion = 0.0
        if porcion <= 0 or resultados.get('es_porcion_100g', False):
            return resultados

        def _f(k):
            try:
                return float((data.get(k) or '0').replace(',', '.'))
            except Exception:
                return 0.0

        factor = porcion / 100.0
        prot = _f('proteina')
        grasa = _f('grasa_total')
        fibra = _f('fibra_dietetica')
        hum = _f('humedad')
        cen = _f('cenizas')
        azu = _f('azucares')
        azu_add = _f('azucares_anadidos')
        sodio_mg = _f('sodio')
        trans_mg = _f('grasa_trans')

        carbs_disp_crudos = max(0.0, (100.0 - (hum + cen + prot + grasa)) - fibra)

        pp = resultados.setdefault('por_porcion', {})
        # g -> HALF_UP (primero calculamos variables locales)
        prot_por = self._aplicar_redondeo_nutrientes_porcion(prot * factor)
        grasa_por = self._aplicar_redondeo_nutrientes_porcion(grasa * factor)
        carbs_por = self._aplicar_redondeo_nutrientes_porcion(carbs_disp_crudos * factor)
        azu_por = self._aplicar_redondeo_nutrientes_porcion(azu * factor)
        azu_add_por = self._aplicar_redondeo_nutrientes_porcion(azu_add * factor)
        # Capar: azúcares añadidos no pueden exceder a azúcares totales por porción
        if azu_add_por > azu_por:
            azu_add_por = azu_por
        fibra_por = self._aplicar_redondeo_nutrientes_porcion(fibra * factor)

        pp['proteina'] = prot_por
        pp['grasa_total'] = grasa_por
        pp['carbohidratos_disponibles'] = carbs_por
        pp['azucares'] = azu_por
        pp['azucares_anadidos'] = azu_add_por
        pp['fibra_dietetica'] = fibra_por
        # mg: reglas
        pp['sodio'] = self._aplicar_regla_redondeo_sodio(sodio_mg * factor)
        pp['grasa_trans'] = self._round_half_up(trans_mg * factor)
        # Nota: 'grasa_saturada' ya se corrige en _fix_grasa_saturada_desde_porcentaje
        return resultados