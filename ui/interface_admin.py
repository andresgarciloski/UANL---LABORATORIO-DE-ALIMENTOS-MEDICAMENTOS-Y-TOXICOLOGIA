import tkinter as tk
from ui.base_interface import BaseInterface
from ui.menu_manager import MenuManager
from ui.admin.users_management import UsersManagement
from ui.admin.export_import import ExportImportSection
from ui.home_section import HomeSection
from ui.historial import HistorialModule

class MainInterfaceAdmin(BaseInterface):
    def __init__(self, username=None, rol="admin"):
        super().__init__(username, rol)
        
        # Inicializar módulos
        self.menu_manager = MenuManager(self)
        self.users_management = UsersManagement(self)
        self.export_import_section = ExportImportSection(self)
        self.home_section = HomeSection(self)
        self.historial_module = HistorialModule(self)
        
        # Secciones del menú para admin
        self.menu_sections = ["Exportar/Importar DB", "Usuarios", "Registro"]
        
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
        elif section_name == "Exportar/Importar DB":
            self.export_import_section.show_export_import_section()
        elif section_name == "Usuarios":
            self.users_management.show_users_table()
        elif section_name == "Registro":
            self.historial_module.show_historial_section()
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
