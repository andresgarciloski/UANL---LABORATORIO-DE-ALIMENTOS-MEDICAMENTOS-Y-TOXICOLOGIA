import tkinter as tk
from PIL import Image, ImageDraw, ImageTk
import os
from ui.base_interface import bind_mousewheel, _BG, _PRIMARY, _PRIMARY_DARK, _TEXT, _SECONDARY, _EMPHASIS

class HomeSection:
    def __init__(self, parent):
        self.parent = parent
        self._hero_photo_cache = None
        self._hero_title_text = 'Laboratorio de Alimentos'
        self._hero_sub_text = ''
        self._hero_user_text = ''
        self._resize_timer = None
        self._last_size = (0, 0)

    def show_home_section(self):
        """Mostrar sección de inicio con estilo moderno y sobrio."""
        # Limpiar contenido previo
        for child in self.parent.content_frame.winfo_children():
            try:
                child.destroy()
            except:
                pass

        main_frame = tk.Frame(self.parent.content_frame, bg=_BG)
        main_frame.pack(fill='both', expand=True)

        # Scroll principal
        body = tk.Frame(main_frame, bg=_BG)
        body.pack(fill='both', expand=True)
        canvas = tk.Canvas(body, bg=_BG, highlightthickness=0, bd=0)
        vsb = tk.Scrollbar(body, orient='vertical', command=canvas.yview)
        canvas.pack(side='left', fill='both', expand=True)
        vsb.pack(side='right', fill='y')
        inner = tk.Frame(canvas, bg=_BG)
        win_id = canvas.create_window((0, 0), window=inner, anchor='nw')

        def _sync(e):
            try:
                canvas.itemconfig(win_id, width=e.width)
                canvas.configure(scrollregion=canvas.bbox('all'))
            except Exception:
                pass
        inner.bind('<Configure>', _sync)
        bind_mousewheel(canvas, inner)
        canvas.configure(yscrollcommand=vsb.set)

        # --- HERO ---
        hero_wrapper = tk.Frame(inner, bg=_BG, height=340)
        hero_wrapper.pack(fill='x', side='top')
        hero_wrapper.pack_propagate(False)
        self._hero_canvas = tk.Canvas(hero_wrapper, bg=_PRIMARY, highlightthickness=0, bd=0)
        self._hero_canvas.pack(fill='both', expand=True)

        self._hero_user_text = f"Bienvenido, {getattr(self.parent,'username','') or 'Usuario'}"

        self._draw_hero()
        hero_wrapper.bind('<Configure>', lambda e: self._schedule_hero_redraw())

        # --- TARJETA BIENVENIDA ---
        card = tk.Frame(inner, bg=_BG)
        card.pack(fill='x', padx=60, pady=(36, 24))

        card_inner = tk.Frame(card, bg='white')
        card_inner.pack(fill='both', expand=True, ipadx=20, ipady=20)
        card_inner.configure(highlightbackground='#E0E0E0', highlightthickness=1)

        tk.Label(card_inner, text='Bienvenida',
                 font=('Segoe UI Semibold', 22),
                 fg=_PRIMARY, bg='white').pack(anchor='w', pady=(4, 2))
        tk.Label(card_inner, text='Resumen general',
                 font=('Segoe UI', 11),
                 fg=_SECONDARY, bg='white').pack(anchor='w')

        tk.Frame(card_inner, bg='#E0E0E0', height=1).pack(fill='x', pady=(12, 20))

        info_text = (
            'Este sistema pertenece al Laboratorio de Alimentos de la Facultad de Ciencias Químicas (UANL).\n\n'
            'Permite realizar cálculos nutrimentales, generar reportes y mantener un historial de análisis.\n'
            'Gracias por formar parte de la comunidad científica de la FCQ-UANL.\n\n'
            'Sitio web: www.fcq.uanl.mx\n'
            'Dirección: Av. Universidad S/N, Cd. Universitaria, San Nicolás de los Garza, N.L.'
        )
        tk.Label(card_inner, text=info_text,
                 justify='left', anchor='w',
                 font=('Segoe UI', 11), fg=_TEXT,
                 bg='white', wraplength=1000).pack(fill='x')

        # --- TARJETA ACERCA DE ---
        extra_card = tk.Frame(inner, bg=_BG)
        extra_card.pack(fill='x', padx=60, pady=(0, 60))

        extra_inner = tk.Frame(extra_card, bg='white')
        extra_inner.pack(fill='both', expand=True, ipadx=20, ipady=20)
        extra_inner.configure(highlightbackground='#E0E0E0', highlightthickness=1)

        tk.Label(extra_inner, text='Acerca de la Plataforma',
                 font=('Segoe UI Semibold', 20),
                 fg=_PRIMARY, bg='white').pack(anchor='w', pady=(0, 4))
        tk.Label(extra_inner, text='Objetivo, alcance y valores institucionales',
                 font=('Segoe UI', 11), fg=_SECONDARY, bg='white').pack(anchor='w')

        tk.Frame(extra_inner, bg='#E0E0E0', height=1).pack(fill='x', pady=(12, 18))

        tk.Label(extra_inner, text=(
            'El sistema digitaliza la generación de tablas nutrimentales, garantizando consistencia y trazabilidad.\n\n'
            'Misión:\n'
            ' • Apoyar la investigación y control de calidad en alimentos.\n'
            ' • Promover herramientas confiables y colaborativas.\n\n'
            'Visión:\n'
            ' • Ser una referencia en automatización de análisis nutrimentales dentro de la UANL.\n\n'
            'Valores institucionales:\n'
            ' • Rigor científico   • Ética   • Innovación   • Servicio a la comunidad\n\n'
            'Beneficios clave:\n'
            ' • Resultados reproducibles\n'
            ' • Exportación rápida y estándar\n'
            ' • Historial centralizado\n'
            ' • Escalabilidad modular\n\n'
            'Contacto institucional:\n'
            ' Facultad de Ciencias Químicas - UANL\n'
            ' www.fcq.uanl.mx'
        ), justify='left', anchor='w', font=('Segoe UI', 10),
        fg=_TEXT, bg='white', wraplength=1000).pack(fill='x', pady=(0, 12))

        footer_bar = tk.Frame(extra_inner, bg=_PRIMARY, height=42)
        footer_bar.pack(fill='x', pady=(20, 0))
        footer_bar.pack_propagate(False)
        tk.Label(footer_bar,
                 text='FCQ-UANL • Laboratorio de Alimentos • Uso interno académico',
                 fg='white', bg=_PRIMARY, font=('Segoe UI', 9, 'bold')).pack(anchor='center', pady=10)

        # Ajustar scroll
        def _update_scroll_region(e=None):
            canvas.configure(scrollregion=canvas.bbox("all"))
        inner.bind("<Configure>", _update_scroll_region)
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(win_id, width=e.width))
        self.parent.after(150, _update_scroll_region)

    # ---------------- HERO helpers -----------------
    def _schedule_hero_redraw(self):
        """Programar redibujo del hero con debounce para evitar parpadeos."""
        if self._resize_timer:
            self.parent.after_cancel(self._resize_timer)
        self._resize_timer = self.parent.after(150, self._draw_hero)

    def _load_hero_image(self):
        """Cargar una sola imagen para el hero."""
        base = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'img'))
        # Intentar cargar fcq.jpg como imagen principal
        path = os.path.join(base, 'fcq.jpg')
        if os.path.exists(path):
            try:
                return Image.open(path).convert('RGB')
            except Exception:
                pass
        # Si no existe, crear placeholder
        return Image.new('RGB', (1200, 400), _PRIMARY)

    def _compose_hero(self, width, height):
        """Componer la imagen del hero con degradado."""
        # Verificar si ya tenemos una imagen del mismo tamaño
        if self._hero_photo_cache and hasattr(self._hero_photo_cache, 'width'):
            if self._hero_photo_cache.width() == width and self._hero_photo_cache.height() == height:
                return self._hero_photo_cache

        # Solo regenerar si el cambio de tamaño es significativo (más de 10px)
        if self._last_size:
            width_diff = abs(width - self._last_size[0])
            height_diff = abs(height - self._last_size[1])
            if width_diff < 10 and height_diff < 10:
                return self._hero_photo_cache

        self._last_size = (width, height)

        img = self._load_hero_image()

        # Cover resize
        scale = max(float(width) / img.width, float(height) / img.height)
        new_w = int(img.width * scale)
        new_h = int(img.height * scale)
        resized = img.resize((new_w, new_h), Image.LANCZOS)
        left = (new_w - width) // 2
        top = (new_h - height) // 2
        cropped = resized.crop((left, top, left + width, top + height))

        # Degradado oscuro moderno
        overlay = Image.new("RGBA", cropped.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        for i in range(height):
            alpha = int(180 * (i / height))
            draw.line([(0, i), (width, i)], fill=(0, 0, 0, alpha))
        combined = Image.alpha_composite(cropped.convert("RGBA"), overlay)

        photo = ImageTk.PhotoImage(combined)
        self._hero_photo_cache = photo
        return photo

    def _draw_text_with_shadow(self, canvas, x, y, text, font, fill='white', shadow='black', offset=2, tags=()):
        canvas.create_text(x + offset, y + offset, text=text, fill=shadow, font=font, anchor='nw', tags=tags)
        canvas.create_text(x, y, text=text, fill=fill, font=font, anchor='nw', tags=tags)

    def _draw_hero(self):
        """Dibujar la imagen hero fija."""
        try:
            w, h = self._hero_canvas.winfo_width(), self._hero_canvas.winfo_height()
        except Exception:
            w, h = 0, 0
        if w < 20 or h < 20:
            self.parent.after(120, self._draw_hero)
            return

        photo = self._compose_hero(w, h)
        if not photo:
            return
        self._hero_canvas.delete("all")
        self._hero_canvas.create_image(0, 0, image=photo, anchor="nw")
        self._hero_canvas.image = photo

        left = int(w * 0.08)
        y_base = int(h * 0.4)

        title_font = ("Segoe UI Semibold", 34)
        sub_font = ("Segoe UI", 14)
        user_font = ("Segoe UI", 12, "italic")

        self._draw_text_with_shadow(self._hero_canvas, left, y_base, self._hero_title_text,
                                    title_font, fill="white", shadow="#1a1a1a", offset=2)
        self._draw_text_with_shadow(self._hero_canvas, left, y_base + 42, self._hero_sub_text,
                                    sub_font, fill="#f0f0f0", shadow="#1a1a1a", offset=1)
        self._draw_text_with_shadow(self._hero_canvas, left, y_base + 72, self._hero_user_text,
                                    user_font, fill="#f5f5f5", shadow="#1a1a1a", offset=1)

    # ---------------- Icon helper -----------------
    def _load_icon(self, name, size=40):
        try:
            base = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'img'))
            path = os.path.join(base, name)
            if not os.path.exists(path):
                return None
            img = Image.open(path).convert('RGBA')
            img = img.resize((size, size), Image.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            if not hasattr(self, '_icon_cache'):
                self._icon_cache = {}
            self._icon_cache[(name, size)] = photo
            return photo
        except Exception:
            return None
