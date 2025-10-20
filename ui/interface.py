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
        
        # Aplicar degradado DESPUÉS de que todo esté creado
        self._apply_gradient_header(start_color="#B71C1C", end_color="#FFCDD2")
        
        self.show_section("Inicio")

    def _apply_gradient_header(self, start_color="#B71C1C", end_color="#FFCDD2"):
        if Image is None or ImageTk is None:
            return

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
                    print(f"✅ Label de degradado creado {w}x{h}px")
                
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
                
            # Asegurarse de que tenemos la sección de perfil
            if not hasattr(self, 'profile_section'):
                self.profile_section = UserProfileSection(self)
                
            # Crear popup
            popup = tk.Toplevel(self)
            self._user_popup = popup
            popup.overrideredirect(True)
            popup.configure(bg=_BG, bd=2, highlightthickness=2, highlightbackground=_PRIMARY)
            
            # Posicionar cerca del botón de usuario
            try:
                x = self.winfo_rootx() + self.winfo_width() - 220
                y = self.winfo_rooty() + 70
                popup.geometry(f"200x140+{x}+{y}")
            except:
                popup.geometry("200x140+800+70")  # Posición por defecto
                
            # Mostrar nombre de usuario
            tk.Label(
                popup,
                text=self.username if hasattr(self, 'username') else "Usuario",
                bg=_BG,
                fg=_PRIMARY,
                font=("Segoe UI", 11, "bold")
            ).pack(pady=(10, 2), padx=10)
            
            # Línea separadora
            tk.Frame(popup, bg=_PRIMARY, height=2).pack(fill="x", padx=10, pady=2)
            
            # Botón Mi Perfil (nuevo)
            tk.Button(
                popup,
                text="Perfil",
                font=("Segoe UI", 11),
                bg=_PRIMARY,
                fg="white",
                activebackground=_PRIMARY_DARK,
                activeforeground="white",
                relief="flat",
                cursor="hand2",
                command=lambda: [popup.destroy(), self.profile_section.show_profile_section()]
            ).pack(fill="x", padx=20, pady=8)
            
            # Botón Cerrar Sesión (original)
            tk.Button(
                popup,
                text="Cerrar sesión",
                font=("Segoe UI", 11),
                bg=_PRIMARY,
                fg="white",
                activebackground=_PRIMARY_DARK,
                activeforeground="white",
                relief="flat",
                cursor="hand2",
                command=lambda: [popup.destroy(), self.logout() if hasattr(self, 'logout') else None]
            ).pack(fill="x", padx=20, pady=8)
            
            # Comportamiento del popup
            popup.focus_force()
            popup.bind("<FocusOut>", lambda e: popup.destroy())

        # Reemplazar el método original
        MainInterface.show_user_menu = enhanced_show_user_menu
        
# Iniciar la modificación cuando se importe este módulo
setup_user_profile_menu()
