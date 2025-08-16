import tkinter as tk
from ui.base_interface import BaseInterface
from ui.menu_manager import MenuManager
from ui.nutrimental import NutrimentalModule
from ui.historial import HistorialModule
from ui.home_section import HomeSection
from ui.calculations import CalculationsSection

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
        self.show_section("Inicio")

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
            bg="white"
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
            popup.configure(bg="white", bd=2, highlightthickness=2, highlightbackground="#0B5394")
            
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
                bg="white",
                fg="#0B5394",
                font=("Segoe UI", 11, "bold")
            ).pack(pady=(10, 2), padx=10)
            
            # Línea separadora
            tk.Frame(popup, bg="#0B5394", height=2).pack(fill="x", padx=10, pady=2)
            
            # Botón Mi Perfil (nuevo)
            tk.Button(
                popup,
                text="Mi Perfil",
                font=("Segoe UI", 11),
                bg="#0B5394",
                fg="white",
                activebackground="#073763",
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
                bg="#0B5394",
                fg="white",
                activebackground="#073763",
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
