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
