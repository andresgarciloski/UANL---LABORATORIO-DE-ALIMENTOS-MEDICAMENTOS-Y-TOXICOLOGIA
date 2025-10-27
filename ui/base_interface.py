import tkinter as tk  # <-- NECESARIO
from tkinter import messagebox
from tkinter import ttk
from PIL import Image, ImageTk, ImageDraw
import os

# Paleta de colores refinada (rojo elegante y agradable a la vista)

_BG = "#FAFAFA"             # Fondo muy claro, casi blanco cálido
_PRIMARY = "#E53935"        # Rojo coral (vibrante pero no agresivo)
_PRIMARY_DARK = "#B71C1C"   # Rojo vino oscuro para contraste
_TEXT = "#212121"           # Gris oscuro, máxima legibilidad
_TEXT_SECONDARY = "#5F5F5F" # Gris medio cálido, más suave que el original
_SECONDARY = "#8D6E63"      # Marrón grisáceo (neutral y combina bien con rojo)
_EMPHASIS = "#FFEBEE"       # Rojo muy pálido para fondos de énfasis
_ALERT = "#C62828"          # Rojo de alerta, consistente con el tono principal

# Colores opcionales para superficies y bordes
_SURFACE = "#FFFFFF"        # Superficies elevadas (tarjetas, paneles)
_BORDER = "#E0E0E0"         # Divisores y bordes sutiles

# Importa PIL de forma segura para todo el proyecto
try:
    from PIL import Image, ImageTk
except Exception:
    Image = ImageTk = None

def bind_mousewheel(widget, canvas):
    """Función para enlazar el scroll del mouse a un canvas solo cuando el mouse está sobre el widget"""
    def _on_mousewheel(event):
        try:
            if canvas.winfo_exists():
                canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        except tk.TclError:
            pass

    def _on_mousewheel_linux(event):
        try:
            if canvas.winfo_exists():
                canvas.yview_scroll(int(-1*event.delta), "units")
        except tk.TclError:
            pass

    widget.bind("<Enter>", lambda e: canvas.bind("<MouseWheel>", _on_mousewheel))
    widget.bind("<Leave>", lambda e: canvas.unbind("<MouseWheel>"))
    widget.bind("<Enter>", lambda e: canvas.bind("<Button-4>", _on_mousewheel_linux))
    widget.bind("<Leave>", lambda e: canvas.unbind("<Button-4>"))
    widget.bind("<Enter>", lambda e: canvas.bind("<Button-5>", _on_mousewheel_linux))
    widget.bind("<Leave>", lambda e: canvas.unbind("<Button-5>"))

class BaseInterface(tk.Tk):
    def __init__(self, username=None, rol="usuario"):
        super().__init__()
        self.title("UANL FoodLab")
        self.geometry("1000x600")
        self.configure(bg=_BG)
        self.username = username
        self.rol = rol

        self.menu_visible = True
        self.menu_frame = None

        # Configurar protocolo de cierre
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def on_closing(self):
        """Limpia recursos antes de cerrar"""
        try:
            if hasattr(self, "menu_frame") and self.menu_frame is not None:
                self.menu_frame.destroy()
        except:
            pass
        self.destroy()

    def create_header(self):
        """Crear header común"""
        header = tk.Frame(self, bg=_PRIMARY, height=60)
        header.pack(side="top", fill="x")
        self.header_frame = header  # <-- guardar referencia

        # Botón del menú lateral
        self.menu_toggle_btn = tk.Button(
            header,
            text="☰",
            font=("Segoe UI", 16, "bold"),
            bg=_PRIMARY,
            fg="white",
            bd=0,
            activebackground=_PRIMARY_DARK,
            activeforeground="white",
            cursor="hand2",
            command=self.toggle_menu
        )
        self.menu_toggle_btn.pack(side="left", padx=(20, 10), pady=10)
        self.menu_toggle_btn.configure(relief="flat", highlightthickness=0, bd=0)

        # REEMPLAZO: icono clickeable (en lugar del título)
        try:
            logo_path = os.path.abspath(r"C:\img\home.png")
            logo_img = Image.open(logo_path).resize((28, 28), Image.LANCZOS)
            self.header_logo_img = ImageTk.PhotoImage(logo_img)
            self.home_btn = tk.Button(
                header,
                image=self.header_logo_img,
                bg=_PRIMARY,
                bd=0,
                activebackground=_PRIMARY_DARK,
                cursor="hand2",
                command=lambda: self.show_section("Inicio")
            )
            self.home_btn.pack(side="left", pady=8, padx=(0, 8))
            self.home_btn.configure(relief="flat", highlightthickness=0, bd=0)
        except Exception:
            self.home_btn = tk.Button(
                header,
                text="🏠",
                bg=_PRIMARY,
                fg="white",
                bd=0,
                activebackground=_PRIMARY_DARK,
                activeforeground="white",
                font=("Segoe UI", 16),
                cursor="hand2",
                command=lambda: self.show_section("Inicio")
            )
            self.home_btn.pack(side="left", pady=8, padx=(0, 8))
            self.home_btn.configure(relief="flat", highlightthickness=0, bd=0)

        # Usuario y foto circular
        self.create_user_section(header)

        # --- NUEVO: camuflar fondo de menú y home con el degradado del header ---
        def _hex_to_rgb(hx):
            hx = hx.lstrip("#")
            return tuple(int(hx[i:i+2], 16) for i in (0, 2, 4))

        def _rgb_to_hex(rgb):
            return "#{:02x}{:02x}{:02x}".format(*rgb)

        GRAD_START = "#B71C1C"  # mismo inicio del degradado del header
        GRAD_END   = "#FFCDD2"  # mismo fin del degradado del header

        def _lerp_color(c0, c1, t):
            r0, g0, b0 = _hex_to_rgb(c0)
            r1, g1, b1 = _hex_to_rgb(c1)
            r = int(r0 + (r1 - r0) * t)
            g = int(g0 + (g1 - g0) * t)
            b = int(b0 + (b1 - b0) * t)
            return _rgb_to_hex((r, g, b))

        def _sync_header_btns_bg(event=None):
            try:
                w = header.winfo_width()
                if w <= 1:
                    header.after(50, _sync_header_btns_bg)
                    return
                for btn in (self.menu_toggle_btn, self.home_btn):
                    if not btn or not btn.winfo_exists():
                        continue
                    x = btn.winfo_x() + btn.winfo_width() / 2
                    t = max(0.0, min(1.0, x / max(1, w)))
                    color = _lerp_color(GRAD_START, GRAD_END, t)
                    btn.configure(bg=color, activebackground=color, relief="flat", highlightthickness=0, bd=0)
            except Exception:
                color = header.cget("bg")
                for btn in (self.menu_toggle_btn, self.home_btn):
                    try:
                        btn.configure(bg=color, activebackground=color)
                    except Exception:
                        pass

        header.bind("<Configure>", _sync_header_btns_bg)
        header.after(80, _sync_header_btns_bg)

        # APLICAR DEGRADADO PARA TODOS (usuario y admin)
        try:
            self.apply_gradient_header(header=header, start_color="#B71C1C", end_color="#FFCDD2")
        except Exception:
            pass

        return header

    def create_user_section(self, header):
        """Crear sección de usuario en header"""
        user_bg = "#FFEBEE"  # rojo muy claro (disimula con el header)
        user_frame = tk.Frame(header, bg=user_bg)
        user_frame.pack(side="right", padx=20)

        try:
            img_path = os.path.join(os.path.dirname(__file__), "..", "img", "bruni.png")
            img_path = os.path.abspath(img_path)

            size = 40
            avatar = Image.open(img_path).resize((size, size), Image.LANCZOS).convert("RGBA")

            # Máscara circular
            mask = Image.new("L", (size, size), 0)
            ImageDraw.Draw(mask).ellipse((0, 0, size, size), fill=255)
            avatar.putalpha(mask)

            # Componer sobre un fondo cuadrado del mismo color claro (evita “cuadro” notorio)
            canvas = Image.new("RGB", (size, size), user_bg)
            canvas.paste(avatar, (0, 0), avatar)

            self.user_icon = ImageTk.PhotoImage(canvas)
            self.user_btn = tk.Button(
                user_frame,
                image=self.user_icon,
                bg=user_bg,
                activebackground=user_bg,
                bd=0,
                relief="flat",
                highlightthickness=0,
                cursor="hand2",
                command=self.show_user_menu
            )
            self.user_btn.pack(side="left")
        except Exception:
            # Fallback si no encuentra la imagen
            self.user_btn = tk.Button(
                user_frame,
                text="👤",
                bg=user_bg,
                activebackground=user_bg,
                bd=0,
                relief="flat",
                highlightthickness=0,
                cursor="hand2",
                command=self.show_user_menu,
                font=("Segoe UI", 16)
            )
            self.user_btn.pack(side="left")

        # --- NUEVO: igualar el fondo del botón al color exacto del degradado del header en su posición ---
        def _hex_to_rgb(hx):
            hx = hx.lstrip("#")
            return tuple(int(hx[i:i+2], 16) for i in (0, 2, 4))

        def _rgb_to_hex(rgb):
            return "#{:02x}{:02x}{:02x}".format(*rgb)

        # Ajusta estos colores si cambiaste el degradado del header
        GRAD_START = "#B71C1C"  # rojo intenso
        GRAD_END   = "#FFCDD2"  # rojo claro

        def _lerp_color(c0, c1, t):
            r0, g0, b0 = _hex_to_rgb(c0)
            r1, g1, b1 = _hex_to_rgb(c1)
            r = int(r0 + (r1 - r0) * t)
            g = int(g0 + (g1 - g0) * t)
            b = int(b0 + (b1 - b0) * t)
            return _rgb_to_hex((r, g, b))

        def _sync_user_bg(event=None):
            try:
                w = header.winfo_width()
                if w <= 1:
                    header.after(50, _sync_user_bg)
                    return
                # centro del user_frame respecto al header (para muestrear el degradado horizontal)
                x = user_frame.winfo_x() + user_frame.winfo_width() / 2
                t = max(0.0, min(1.0, x / max(1, w)))
                color = _lerp_color(GRAD_START, GRAD_END, t)

                # aplicar color calculado para “camuflar” el rectángulo
                user_frame.configure(bg=color)
                try:
                    self.user_btn.configure(bg=color, activebackground=color, highlightthickness=0, bd=0, relief="flat")
                except Exception:
                    pass
            except Exception:
                # Fallback: igualar al bg del header si algo falla
                color = header.cget("bg")
                user_frame.configure(bg=color)
                try:
                    self.user_btn.configure(bg=color, activebackground=color)
                except Exception:
                    pass

        # Actualizar cuando el header cambie de tamaño/posición (degradado)
        header.bind("<Configure>", _sync_user_bg)
        header.after(80, _sync_user_bg)

    def create_content_frame(self):
        """Crear frame de contenido"""
        self.content_frame = tk.Frame(self, bg=_BG)
        self.content_frame.pack(expand=True, fill="both")

    def show_user_menu(self):
        """Mostrar menú de usuario"""
        popup = tk.Toplevel(self)
        popup.overrideredirect(True)
        popup.configure(bg=_BG, bd=2, highlightthickness=2, highlightbackground=_PRIMARY)

        # Calcular posición
        main_x = self.winfo_rootx()
        main_y = self.winfo_rooty()
        main_w = self.winfo_width()
        popup_w, popup_h = 200, 90
        x = main_x + main_w - popup_w - 40
        y = main_y + 70

        popup.geometry(f"{popup_w}x{popup_h}+{x}+{y}")

        # Contenido del popup
        tk.Label(
            popup,
            text=self.username if self.username else "Usuario",
            bg=_BG,
            fg=_PRIMARY,
            font=("Segoe UI", 11, "bold")
        ).pack(pady=(10, 2), padx=10)

        tk.Frame(popup, bg=_PRIMARY, height=2).pack(fill="x", padx=10, pady=2)

        tk.Button(
            popup,
            text="Cerrar sesión",
            font=("Segoe UI", 11),
            bg=_PRIMARY,
            fg="white",
            activebackground=_PRIMARY_DARK,
            activeforeground="white",
            relief="flat",
            command=lambda: [popup.destroy(), self.logout()]
        ).pack(fill="x", padx=20, pady=10)

        popup.focus_force()
        popup.bind("<FocusOut>", lambda e: popup.destroy())

    def logout(self):
        """Cerrar sesión"""
        if messagebox.askyesno("Cerrar sesión", "¿Deseas cerrar sesión?"):
            try:
                if hasattr(self, "menu_frame") and self.menu_frame is not None:
                    self.menu_frame.destroy()
            except:
                pass
                
            self.destroy()
            from ui.login_screen import LoginWindow
            login = LoginWindow()
            login.mainloop()

    def get_usuario_id(self):
        """Obtiene el ID del usuario actual con manejo de errores mejorado"""
        try:
            from core.auth import obtener_id_por_username
            if not self.username:
                messagebox.showerror("Error", "No hay usuario autenticado")
                return None
            
            user_id = obtener_id_por_username(self.username)
            if user_id is None:
                messagebox.showerror("Error", f"Usuario '{self.username}' no encontrado en la base de datos")
                return None
            
            return user_id
        except Exception as e:
            messagebox.showerror("Error", f"Error al obtener ID de usuario: {e}")
            return None

    def apply_gradient_header(self, header=None, start_color="#B71C1C", end_color="#FFCDD2"):
        """Aplica un degradado al header indicado; si header es None, intenta localizarlo."""
        try:
            Image, ImageTk  # asegurar PIL
        except Exception:
            return

        # Usar header explícito o detectar el primero en top
        if header is None:
            for widget in self.winfo_children():
                if isinstance(widget, (tk.Frame, ttk.Frame)):
                    try:
                        pack_info = widget.pack_info()
                    except Exception:
                        pack_info = {}
                    if pack_info.get("side") == "top" or not pack_info:
                        widget.update_idletasks()
                        if widget.winfo_height() < 200:
                            header = widget
                            break
            if header is None:
                return

        def make_gradient(w, h):
            img = Image.new("RGB", (max(1, w), max(1, h)))
            def hex_to_rgb(hex_color):
                hex_color = hex_color.lstrip("#")
                return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
            r0, g0, b0 = hex_to_rgb(start_color)
            r1, g1, b1 = hex_to_rgb(end_color)
            for x in range(max(1, w)):
                t = x / max(1, w - 1)
                r = int(r0 + (r1 - r0) * t)
                g = int(g0 + (g1 - g0) * t)
                b = int(b0 + (b1 - b0) * t)
                for y in range(h):
                    img.putpixel((x, y), (r, g, b))
            return ImageTk.PhotoImage(img)

        def refresh_gradient(event=None):
            w = header.winfo_width()
            h = header.winfo_height()
            if w <= 1 or h <= 1:
                header.after(100, refresh_gradient)
                return
            self._gradient_photo = make_gradient(w, h)

            # Label de fondo para el degradado
            if not hasattr(self, "_gradient_label") or (self._gradient_label.winfo_exists() == 0):
                self._gradient_label = tk.Label(header, bd=0, highlightthickness=0)
                self._gradient_label.place(x=0, y=0, relwidth=1, relheight=1)
                self._gradient_label.lower()
            self._gradient_label.configure(image=self._gradient_photo)

            # Asegurar que los demás widgets queden encima
            for wdg in header.winfo_children():
                if wdg != self._gradient_label:
                    wdg.lift()

        header.bind("<Configure>", refresh_gradient)
        header.after(300, refresh_gradient)

    # Métodos que deben ser implementados por las clases hijas
    def toggle_menu(self):
        raise NotImplementedError
    
    def show_section(self, section_name):
        raise NotImplementedError