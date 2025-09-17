import tkinter as tk
from tkinter import messagebox  # AGREGAR ESTE IMPORT
import os
from PIL import Image, ImageTk, ImageDraw

_BG = "#F5F5F5"            # fondo claro neutro
_PRIMARY = "#C62828"       # rojo principal (Material Red 800)
_PRIMARY_DARK = "#B71C1C"  # variante oscura coherente (Material Red 700)
_TEXT = "#212121"          # gris oscuro, alta legibilidad
_TEXT_SECONDARY = "#616161" # gris medio (mejor contraste que #9E9E9E)
_SECONDARY = "#607D8B"     # azul grisáceo suave (equilibrio)
_EMPHASIS = "#FFCDD2"      # acentos suaves (tinte del primario)
_ALERT = "#D32F2F"         # rojo de alerta (Material Red 700/600)

# Opcionales de paleta (por si otros módulos los usan)
_SURFACE = "#FFFFFF"       # tarjetas/fondos elevados
_BORDER = "#E0E0E0"        # líneas y divisores sutiles


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

        # Título clickable
        title = tk.Label(
            header,
            text="Facultad de Ciencias Químicas - UANL",
            bg=_PRIMARY,
            fg="white",
            font=("Segoe UI", 16, "bold"),
            padx=10,
            cursor="hand2"
        )
        title.pack(side="left", pady=10)
        title.bind("<Button-1>", lambda e: self.show_section("Inicio"))

        # Usuario y foto circular
        self.create_user_section(header)

    def create_user_section(self, header):
        """Crear sección de usuario en header"""
        user_frame = tk.Frame(header, bg=_PRIMARY)
        user_frame.pack(side="right", padx=20)

        user_label = tk.Label(
            user_frame,
            text=self.username if self.username else "Usuario",
            bg=_PRIMARY,
            fg="white",
            font=("Segoe UI", 12, "bold"),
            padx=10
        )
        user_label.pack(side="left")

        # Imagen circular
        try:
            img_path = os.path.join(os.path.dirname(__file__), "..", "img", "bruni.png")
            img_path = os.path.abspath(img_path)
            user_img = Image.open(img_path).resize((40, 40), Image.LANCZOS)
            mask = Image.new('L', (40, 40), 0)
            draw = ImageDraw.Draw(mask)
            draw.ellipse((0, 0, 40, 40), fill=255)
            user_img.putalpha(mask)
            self.user_icon = ImageTk.PhotoImage(user_img)
            
            self.user_btn = tk.Button(
                user_frame,
                image=self.user_icon,
                bg=_PRIMARY,
                bd=0,
                activebackground=_PRIMARY,
                cursor="hand2",
                command=self.show_user_menu
            )
            self.user_btn.pack(side="left")
        except Exception:
            # Fallback si no encuentra la imagen
            self.user_btn = tk.Button(
                user_frame,
                text="👤",
                bg=_PRIMARY,
                bd=0,
                activebackground=_PRIMARY,
                cursor="hand2",
                command=self.show_user_menu,
                font=("Segoe UI", 16)
            )
            self.user_btn.pack(side="left")

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

    # Métodos que deben ser implementados por las clases hijas
    def toggle_menu(self):
        raise NotImplementedError
    
    def show_section(self, section_name):
        raise NotImplementedError