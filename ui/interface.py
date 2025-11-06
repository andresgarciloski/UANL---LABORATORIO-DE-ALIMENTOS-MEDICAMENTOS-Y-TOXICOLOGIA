import tkinter as tk
import tkinter.ttk as ttk
from ui.base_interface import BaseInterface
from ui.base_interface import _BG, _PRIMARY, _PRIMARY_DARK, _TEXT
from ui.menu_manager import MenuManager
from ui.nutrimental import NutrimentalModule
from ui.historial import HistorialModule
from ui.home_section import HomeSection
from ui.calculations import CalculationsSection
# --- NUEVO: PIL para generar la imagen de degradado ---
try:
    from PIL import Image, ImageTk
except Exception:
    Image = ImageTk = None

class MainInterface(BaseInterface):
    def __init__(self, username=None, rol="usuario"):
        super().__init__(username, rol)
        
        # Inicializar módulos
        self.menu_manager = MenuManager(self)
        self.nutrimental_module = NutrimentalModule(self)
        self.historial_module = HistorialModule(self)
        self.home_section = HomeSection(self)
        self.calculations_section = CalculationsSection(self)
        
        # Secciones del menú
        self.menu_sections = ["Cálculos", "Tabla Nutrimental", "Historial"]
        
        self.create_widgets()

    def create_widgets(self):
        """Crear widgets de la interfaz"""
        self.create_header()
        self.create_content_frame()
        self.menu_manager.create_side_menu(self.menu_sections)
        # Usar la versión común del degradado
        self.apply_gradient_header(start_color="#B71C1C", end_color="#FFCDD2")
        self.show_section("Inicio")

    # Simplificar para mantener compatibilidad con llamadas existentes
    def _apply_gradient_header(self, start_color="#B71C1C", end_color="#FFCDD2"):
        # Buscar el frame del header en los widgets de la ventana principal
        header = None
        for widget in self.winfo_children():
            # Buscar un Frame que esté en la parte superior (pack side='top' o grid row=0)
            if isinstance(widget, (tk.Frame, ttk.Frame)):
                pack_info = widget.pack_info()
                if pack_info.get('side') == 'top' or not pack_info:
                    # Verificar si tiene altura pequeña (típico de headers)
                    widget.update_idletasks()
                    if widget.winfo_height() < 200:  # Los headers suelen ser < 200px
                        header = widget
                        break

        def make_gradient(w, h):
            """Genera imagen de degradado horizontal"""
            img = Image.new("RGB", (max(1, w), max(1, h)))
            
            def hex_to_rgb(hex_color):
                hex_color = hex_color.lstrip('#')
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
            
            # Crear imagen de degradado
            self._gradient_photo = make_gradient(w, h)
            
            # Buscar el label con la imagen del banner
            banner_label = None
            for widget in header.winfo_children():
                if isinstance(widget, tk.Label):
                    if hasattr(widget, 'image') or widget.cget('image'):
                        banner_label = widget
                        break
            
            # Reemplazar banner con degradado
            if banner_label:
                banner_label.configure(image=self._gradient_photo)
                self._gradient_label = banner_label
                
                # Asegurar que el texto y otros widgets estén encima
                for widget in header.winfo_children():
                    if widget != banner_label:
                        widget.lift()
                
                
            else:
                # Si no hay banner, crear label nuevo
                if not hasattr(self, "_gradient_label"):
                    self._gradient_label = tk.Label(header, bd=0, highlightthickness=0)
                    self._gradient_label.place(x=0, y=0, relwidth=1, relheight=1)
                    self._gradient_label.lower()
                
                self._gradient_label.configure(image=self._gradient_photo)
                
                # Levantar otros widgets
                for widget in header.winfo_children():
                    if widget != self._gradient_label:
                        widget.lift()

        header.bind("<Configure>", refresh_gradient)
        header.after(300, refresh_gradient)

    def toggle_menu(self):
        """Toggle del menú lateral"""
        self.menu_manager.toggle_menu()

    def show_section(self, section_name):
        """Mostrar sección específica"""
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        if section_name == "Inicio":
            self.home_section.show_home_section()
        elif section_name == "Historial":
            self.historial_module.show_historial_section()
        elif section_name == "Tabla Nutrimental":
            self.nutrimental_module.show_nutrimental_section()
        elif section_name == "Cálculos":
            self.calculations_section.show_calculations_section()
        else:
            self._show_default_section(section_name)

    def _show_default_section(self, section_name):
        """Mostrar sección por defecto"""
        label = tk.Label(
            self.content_frame,
            text=f"Sección: {section_name}",
            font=("Segoe UI", 14),
            bg=_BG,
            fg=_TEXT
        )
        label.pack(pady=20)

# En vez de importar directamente al inicio del archivo, importa dentro de la función
def _initialize_interfaces():
    try:
        from ui.user_data import add_profile_to_menu
        
        original_init = MainInterface.__init__
        
        def enhanced_init(self, *args, **kwargs):
            original_init(self, *args, **kwargs)
            # Añadir la sección de perfil después de la inicialización
            add_profile_to_menu(self)
        
        MainInterface.__init__ = enhanced_init
    except Exception as e:
        print(f"Error al inicializar interfaces: {e}")

# Llamar a la función al final del archivo
if __name__ != "__main__":  # Solo si se importa, no al ejecutar directo
    _initialize_interfaces()

# Importar e integrar la funcionalidad de perfil de usuario
from ui.user_data import UserProfileSection

# Modificar la clase MainInterface para agregar la funcionalidad de perfil
def setup_user_profile_menu():
    # Modificar el método show_user_menu de MainInterface
    if hasattr(MainInterface, 'show_user_menu'):
        original_show_user_menu = MainInterface.show_user_menu
        
        def enhanced_show_user_menu(self):
            # Cerrar popup existente
            if hasattr(self, '_user_popup') and self._user_popup:
                try:
                    self._user_popup.destroy()
                except:
                    pass
                self._user_popup = None
                
            # Asegurar sección de perfil
            if not hasattr(self, 'profile_section'):
                self.profile_section = UserProfileSection(self)

            # Helper de estilo (mismo tamaño/estilo para todos)
            def style_button(btn):
                btn.configure(
                    bg=_PRIMARY, fg="white",
                    activebackground=_PRIMARY_DARK, activeforeground="white",
                    relief="flat", bd=0, cursor="hand2",
                    font=("Segoe UI", 11), height=1
                )

            # Acción "Acerca de"
            def open_about():
                try:
                    if self._user_popup: self._user_popup.destroy()
                except:
                    pass
                win = tk.Toplevel(self)
                win.title("Acerca de")
                win.configure(bg=_BG)
                win.resizable(False, False)
                win.transient(self)
                win.update_idletasks()
                ww, wh = 420, 220
                sx = self.winfo_rootx() + (self.winfo_width() - ww)//2
                sy = self.winfo_rooty() + (self.winfo_height() - wh)//3
                win.geometry(f"{ww}x{wh}+{max(0, sx)}+{max(0, sy)}")

                wrapper = tk.Frame(win, bg=_BG)
                wrapper.pack(fill="both", expand=True, padx=16, pady=16)

                tk.Label(wrapper, text="Contacto", bg=_BG, fg=_PRIMARY,
                         font=("Segoe UI", 12, "bold")).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0,8))

                # Datos fijos solicitados
                tk.Label(wrapper, text="Nombre:", bg=_BG, fg=_TEXT, font=("Segoe UI", 10, "bold"))\
                    .grid(row=1, column=0, sticky="w", padx=(0,8), pady=4)
                tk.Label(wrapper, text="Andrés Alejandro García Guerrero", bg=_BG, fg=_TEXT, font=("Segoe UI", 10))\
                    .grid(row=1, column=1, sticky="w", pady=4)

                tk.Label(wrapper, text="Email:", bg=_BG, fg=_TEXT, font=("Segoe UI", 10, "bold"))\
                    .grid(row=2, column=0, sticky="w", padx=(0,8), pady=4)
                email_lbl = tk.Label(wrapper, text="andres.garciag@uanl.edu.mx", bg=_BG, fg=_TEXT,
                                     font=("Segoe UI", 10), cursor="hand2")
                email_lbl.grid(row=2, column=1, sticky="w", pady=4)

                tk.Label(wrapper, text="Teléfono:", bg=_BG, fg=_TEXT, font=("Segoe UI", 10, "bold"))\
                    .grid(row=3, column=0, sticky="w", padx=(0,8), pady=4)
                phone_lbl = tk.Label(wrapper, text="8110310901", bg=_BG, fg=_TEXT,
                                     font=("Segoe UI", 10), cursor="hand2")
                phone_lbl.grid(row=3, column=1, sticky="w", pady=4)

                # Copiar al portapapeles al hacer clic (sin dependencias externas)
                def copy_to_clip(text):
                    try:
                        win.clipboard_clear()
                        win.clipboard_append(text)
                    except:
                        pass
                email_lbl.bind("<Button-1>", lambda e: copy_to_clip("andres.garciag@uanl.edu.mx"))
                phone_lbl.bind("<Button-1>", lambda e: copy_to_clip("8110310901"))

                close_btn = tk.Button(wrapper, text="Cerrar", command=win.destroy)
                style_button(close_btn)
                close_btn.grid(row=4, column=1, sticky="e", pady=(12,0))

            # Crear popup
            popup = tk.Toplevel(self)
            self._user_popup = popup
            popup.overrideredirect(True)
            popup.wm_attributes("-topmost", True)
            popup.configure(bg=_BG, bd=2, highlightthickness=2, highlightbackground=_PRIMARY)

            # Posición: anclado al botón de usuario si existe
            try:
                ux = self.user_btn.winfo_rootx()
                uy = self.user_btn.winfo_rooty()
                uw = self.user_btn.winfo_width()
                uh = self.user_btn.winfo_height()
                popup_w = 240
                x = int(ux + uw - popup_w)
                y = int(uy + uh + 6)
            except:
                popup_w = 240
                x = self.winfo_rootx() + self.winfo_width() - popup_w - 20
                y = self.winfo_rooty() + 70

            container = tk.Frame(popup, bg=_BG)
            container.pack(fill="both", expand=True, padx=8, pady=8)

            tk.Label(container,
                     text=self.username if hasattr(self, 'username') and self.username else "Usuario",
                     bg=_BG, fg=_PRIMARY, font=("Segoe UI", 11, "bold"),
                     anchor="w").pack(fill="x", padx=6, pady=(2,6))

            tk.Frame(container, bg=_PRIMARY, height=2).pack(fill="x", padx=6, pady=(0,8))

            btns = tk.Frame(container, bg=_BG)
            btns.pack(fill="x")

            perfil_btn = tk.Button(btns, text="Perfil",
                                   command=lambda: [popup.destroy(), self.profile_section.show_profile_section()])
            style_button(perfil_btn)
            perfil_btn.pack(fill="x", padx=6, pady=(0,8), ipady=8)

            cerrar_btn = tk.Button(btns, text="Cerrar sesión",
                                   command=lambda: [popup.destroy(), self.logout() if hasattr(self, 'logout') else None])
            style_button(cerrar_btn)
            cerrar_btn.pack(fill="x", padx=6, pady=(0,8), ipady=8)

            acerca_btn = tk.Button(btns, text="Acerca de", command=open_about)
            style_button(acerca_btn)
            acerca_btn.pack(fill="x", padx=6, pady=(0,0), ipady=8)

            popup.update_idletasks()
            popup_h = popup.winfo_reqheight()
            popup.geometry(f"{popup_w}x{popup_h}+{x}+{y}")

            popup.focus_force()
            popup.bind("<FocusOut>", lambda e: popup.destroy())
            popup.bind("<Escape>", lambda e: popup.destroy())

        # Reemplazar el método original
        MainInterface.show_user_menu = enhanced_show_user_menu
# Iniciar la modificación cuando se importe este módulo
setup_user_profile_menu()
