import tkinter as tk
from PIL import Image, ImageDraw, ImageTk
import os
from ui.base_interface import bind_mousewheel, _BG, _PRIMARY, _PRIMARY_DARK, _TEXT, _SECONDARY, _EMPHASIS

class HomeSection:
    def __init__(self, parent):
        self.parent = parent
        self._hero_images = []  # lista de PIL Images
        self._hero_index = 0
        self._hero_photo_cache = {}  # cache de PhotoImage redimensionados
        # textos del hero (sin recuadro)
        self._hero_title_text = 'Laboratorio de Alimentos'
        self._hero_sub_text = 'Facultad de Ciencias Químicas - UANL'
        self._hero_user_text = ''
        
    def show_home_section(self):
        """Mostrar sección de inicio con hero/carousel y texto original."""
        # Limpiar contenido previo
        for child in self.parent.content_frame.winfo_children():
            try:
                child.destroy()
            except:
                pass

        main_frame = tk.Frame(self.parent.content_frame, bg=_BG)
        main_frame.pack(fill='both', expand=True)

        # CONTENEDOR SCROLLABLE (ahora incluye el HERO para que no sea estático)
        body = tk.Frame(main_frame, bg=_BG)
        body.pack(fill='both', expand=True)
        canvas = tk.Canvas(body, bg=_BG, highlightthickness=0, bd=0)
        vsb = tk.Scrollbar(body, orient='vertical', command=canvas.yview)
        canvas.pack(side='left', fill='both', expand=True)
        vsb.pack(side='right', fill='y')
        inner = tk.Frame(canvas, bg=_BG)
        win_id = canvas.create_window((0,0), window=inner, anchor='nw')

        def _sync(e):
            try:
                canvas.itemconfig(win_id, width=e.width)
                canvas.configure(scrollregion=canvas.bbox('all'))
            except Exception:
                pass
        inner.bind('<Configure>', _sync)
        bind_mousewheel(canvas, inner)
        canvas.configure(yscrollcommand=vsb.set)

        # HERO dentro del área scrollable (sin cuadro rojo)
        hero_wrapper = tk.Frame(inner, bg=_BG, height=320)
        hero_wrapper.pack(fill='x', side='top')
        hero_wrapper.pack_propagate(False)
        self._hero_canvas = tk.Canvas(hero_wrapper, bg=_PRIMARY, highlightthickness=0, bd=0)
        self._hero_canvas.pack(fill='both', expand=True)

        # actualizar textos (incluye usuario)
        self._hero_user_text = f"Bienvenido, {getattr(self.parent,'username','') or 'Usuario'}"

        self._load_hero_images()
        self._draw_current_hero()
        hero_wrapper.bind('<Configure>', lambda e: self._draw_current_hero())
        if len(self._hero_images) > 1:
            self.parent.after(6000, self._rotate_hero)

        # Card texto original (mayor contraste y barra lateral)
        card = tk.Frame(inner, bg=_BG, bd=0)
        card.pack(fill='x', padx=40, pady=(24,16))

        # Contenedor sombra (ligeramente desplazado)
        shadow = tk.Frame(card, bg='#D0D4D8')
        shadow.place(x=10, y=10, relwidth=1, relheight=1)

        card_inner = tk.Frame(card, bg='white', highlightthickness=1, highlightbackground='#CBD0D4')
        card_inner.pack(fill='both', expand=True)

        # Barra de acento a la izquierda
        accent = tk.Frame(card_inner, bg=_PRIMARY, width=8)
        accent.pack(side='left', fill='y')

        content_wrap = tk.Frame(card_inner, bg='white')
        content_wrap.pack(side='left', fill='both', expand=True)

        header = tk.Frame(content_wrap, bg='white')
        header.pack(fill='x', padx=26, pady=(22,6))
        tk.Label(header, text='Bienvenida', font=('Segoe UI',20,'bold'), fg=_PRIMARY, bg='white').pack(anchor='w')
        tk.Label(header, text='Resumen general', font=('Segoe UI',10), fg=_SECONDARY, bg='white').pack(anchor='w', pady=(4,0))

        sep = tk.Frame(content_wrap, bg=_EMPHASIS, height=2)
        sep.pack(fill='x', padx=26, pady=(8,16))

        info_wrapper = tk.Frame(content_wrap, bg='white')
        info_wrapper.pack(fill='x', padx=26, pady=(0,24))
        original_text = (
            'Este sistema es parte del Laboratorio de Alimentos de la '\
            'Facultad de Ciencias Químicas - UANL.\n\n'
            'Aquí podrás realizar cálculos, exportar reportes y consultar tu historial.\n'
            '¡Gracias por formar parte de la comunidad científica de la FCQ-UANL!\n\n'
            'Facultad de Ciencias Químicas\n'
            'Universidad Autónoma de Nuevo León\n'
            'www.fcq.uanl.mx\n'
            'Av. Universidad S/N, Cd. Universitaria, San Nicolás de los Garza, N.L.'
        )
        tk.Label(info_wrapper, text=original_text, justify='left', anchor='w', font=('Segoe UI',11), fg=_TEXT, bg='white', wraplength=1100).pack(fill='x')

        # Pequeño indicador de que hay más contenido (si la pantalla es muy grande)
        hint = tk.Label(content_wrap, text='Desplázate para más información ↓', font=('Segoe UI',9,'italic'), fg=_SECONDARY, bg='white')
        hint.pack(anchor='e', padx=26, pady=(0,4))

        # Segunda tarjeta: información ampliada / propósito
        extra_card = tk.Frame(inner, bg=_BG, bd=0)
        extra_card.pack(fill='x', padx=40, pady=(8,40))
        extra_shadow = tk.Frame(extra_card, bg=_SECONDARY)
        extra_shadow.place(x=6,y=6, relwidth=1, relheight=1)
        extra_inner = tk.Frame(extra_card, bg='white', highlightthickness=1, highlightbackground='#E0E3E6')
        extra_inner.pack(fill='both', expand=True)

        top = tk.Frame(extra_inner, bg='white')
        top.pack(fill='x', padx=28, pady=(24,4))
        tk.Label(top, text='Acerca de la Plataforma', font=('Segoe UI',18,'bold'), fg=_PRIMARY, bg='white').pack(anchor='w')
        tk.Label(top, text='Objetivo, alcance y valores institucionales', font=('Segoe UI',10), fg=_SECONDARY, bg='white').pack(anchor='w', pady=(4,2))

        sep2 = tk.Frame(extra_inner, bg=_EMPHASIS, height=2)
        sep2.pack(fill='x', padx=28, pady=(6,18))

        body_ext = tk.Frame(extra_inner, bg='white')
        body_ext.pack(fill='x', padx=28, pady=(0,26))

        texto_ext = (
            'El sistema digitaliza y estandariza el flujo de generación de tablas nutrimentales, '
            'reduciendo errores manuales y asegurando coherencia en criterios de redondeo y sellos de advertencia.\n\n'
            'Misión:\n'
            ' • Apoyar la investigación y el control de calidad en alimentos mediante herramientas confiables.\n'
            ' • Facilitar la trazabilidad de resultados y la colaboración entre analistas.\n\n'
            'Visión:\n'
            ' • Convertirse en una referencia interna para la automatización de reportes y análisis nutrimentales.\n\n'
            'Valores institucionales (FCQ - UANL):\n'
            ' • Rigor científico   • Ética   • Innovación   • Servicio a la comunidad\n\n'
            'Beneficios clave para el usuario:\n'
            ' • Cálculo reproducible de energía y macronutrientes.\n'
            ' • Exportación rápida (formato estándar).\n'
            ' • Historial centralizado para auditorías.\n'
            ' • Escalabilidad: preparado para agregar nuevos parámetros y normas.\n\n'
            'Contacto institucional:\n'
            ' Facultad de Ciencias Químicas - UANL\n'
            ' Tel: +52 (81) 8329 4000  Ext. (si aplica)\n'
            ' Sitio: www.fcq.uanl.mx\n'
            ' Correo: (coloque_correo@uanl.mx)\n'
        )
        tk.Label(body_ext, text=texto_ext, justify='left', anchor='w', font=('Segoe UI',10), fg=_TEXT, bg='white', wraplength=1100).pack(fill='x')

        # Mini footer institucional estilizado
        footer_bar = tk.Frame(extra_inner, bg=_PRIMARY, height=44)
        footer_bar.pack(fill='x')
        footer_bar.pack_propagate(False)
        tk.Label(footer_bar, text='FCQ-UANL • Laboratorio de Alimentos • Uso interno académico', fg='white', bg=_PRIMARY,
                 font=('Segoe UI',9,'bold')).pack(anchor='center', pady=10)

        # Ajuste scroll
        def _update_scroll_region(e=None):
            canvas.configure(scrollregion=canvas.bbox("all"))
        
        inner.bind("<Configure>", _update_scroll_region)
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(win_id, width=e.width))
        self.parent.after(150, _update_scroll_region)

    # ---------------- HERO helpers -----------------
    def _load_hero_images(self):
        if self._hero_images:
            return
        base = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'img'))
        candidates = [
            'fcq.jpg',
            'fcq2.jpg',
            'fcq3.jpg',
            'fcq4.jpg',
            'fcq5.jpg'
        ]
        loaded = []
        for name in candidates:
            path = os.path.join(base, name)
            if os.path.exists(path):
                try:
                    img = Image.open(path).convert('RGB')
                    loaded.append(img)
                except Exception:
                    pass
        if not loaded:
            # Crear imagen placeholder
            ph = Image.new('RGB', (1200, 400), _PRIMARY)
            loaded.append(ph)
        self._hero_images = loaded

    def _compose_hero(self, width, height):
        # Robust scale-and-center-crop to (width, height)
        if not self._hero_images:
            return None
        key = (self._hero_index, width, height)
        if key in self._hero_photo_cache:
            return self._hero_photo_cache[key]
        img = self._hero_images[self._hero_index]
        # Calculate scale to cover the target area (cover strategy)
        try:
            scale = max(float(width) / img.width, float(height) / img.height)
        except Exception:
            scale = 1.0
        new_w = max(1, int(img.width * scale))
        new_h = max(1, int(img.height * scale))
        resized = img.resize((new_w, new_h), Image.LANCZOS)
        # center crop to target size
        left = max(0, (new_w - width) // 2)
        top = max(0, (new_h - height) // 2)
        right = left + width
        bottom = top + height
        cropped = resized.crop((left, top, right, bottom))
        # Overlay semi-transparent tint for text contrast
        tint = Image.new('RGBA', cropped.size, (229, 57, 53, 90))
        combined = Image.alpha_composite(cropped.convert('RGBA'), tint)
        photo = ImageTk.PhotoImage(combined)
        self._hero_photo_cache[key] = photo
        return photo

    def _draw_text_with_shadow(self, canvas, x, y, text, font, fill='white', shadow='black', offset=2, tags=()):
        # Sombra ligera para legibilidad
        canvas.create_text(x+offset, y+offset, text=text, fill=shadow, font=font, anchor='nw', tags=tags)
        canvas.create_text(x, y, text=text, fill=fill, font=font, anchor='nw', tags=tags)

    def _draw_current_hero(self):
        # Ensure canvas has a usable size; retry shortly if not yet laid out
        try:
            w = self._hero_canvas.winfo_width()
            h = self._hero_canvas.winfo_height()
        except Exception:
            w, h = 0, 0
        if w < 20 or h < 20:
            # retry after a short delay once the widget has been laid out
            try:
                self.parent.after(120, self._draw_current_hero)
            except Exception:
                pass
            return
        try:
            photo = self._compose_hero(w, h)
            if not photo:
                return
            self._hero_canvas.delete('all')
            self._hero_canvas.create_image(0, 0, image=photo, anchor='nw')
            # keep reference to avoid GC
            self._hero_canvas.image = photo

            # Dibujar textos directamente sobre el canvas (sin recuadro rojo)
            self._hero_canvas.delete('hero_text')
            left = int(w * 0.06)
            y_title = int(h * 0.18)
            y_sub = y_title + 46
            y_user = y_sub + 34

            # Colores y fuente
            title_font = ('Segoe UI', 30, 'bold')
            sub_font   = ('Segoe UI', 14)
            user_font  = ('Segoe UI', 14, 'bold')

            # Sombra suave
            shadow_color = '#2a2a2a'

            self._draw_text_with_shadow(self._hero_canvas, left, y_title, self._hero_title_text,
                                        title_font, fill='white', shadow=shadow_color, offset=2, tags=('hero_text',))
            self._draw_text_with_shadow(self._hero_canvas, left, y_sub, self._hero_sub_text,
                                        sub_font, fill='white', shadow=shadow_color, offset=2, tags=('hero_text',))
            self._draw_text_with_shadow(self._hero_canvas, left, y_user, self._hero_user_text,
                                        user_font, fill=_EMPHASIS, shadow=shadow_color, offset=1, tags=('hero_text',))

        except Exception:
            # If composition fails, schedule a retry instead of silently leaving background
            try:
                self.parent.after(250, self._draw_current_hero)
            except Exception:
                pass

    def _rotate_hero(self):
        if not self._hero_images or len(self._hero_images) < 2:
            return
        self._hero_index = (self._hero_index + 1) % len(self._hero_images)
        self._hero_photo_cache.clear()
        self._draw_current_hero()
        self.parent.after(6000, self._rotate_hero)

    # ---------------- Icon helper -----------------
    def _load_icon(self, name, size=40):
        try:
            base = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'img'))
            path = os.path.join(base, name)
            if not os.path.exists(path):
                return None
            img = Image.open(path).convert('RGBA')
            img = img.resize((size,size), Image.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            # cache en atributo dict
            if not hasattr(self, '_icon_cache'):
                self._icon_cache = {}
            self._icon_cache[(name,size)] = photo
            return photo
        except Exception:
            return None