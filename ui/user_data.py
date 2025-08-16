import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import os

# Cargar dinámicamente para evitar problemas de importación circular
def get_user_data_module():
    try:
        from core.user_data_function import get_user_data, update_user_profile
        return get_user_data, update_user_profile
    except ImportError as e:
        print(f"Error importando módulos de datos de usuario: {e}")
        # Funciones dummy en caso de error
        def dummy_get(*args, **kwargs): return None
        def dummy_update(*args, **kwargs): return False, "Error en módulo de datos"
        return dummy_get, dummy_update

class UserProfileSection:
    def __init__(self, parent_window):
        self.parent = parent_window
        self._load_icons()
    
    def _load_icons(self):
        """Carga las imágenes necesarias para la interfaz"""
        self.bruni_img = None
        try:
            img_path = os.path.join(os.path.dirname(__file__), "..", "img", "bruni.png")
            img_path = os.path.abspath(img_path)
            img = Image.open(img_path)
            
            # Ajustar tamaño si es necesario
            w, h = img.size
            if w > 200:
                ratio = 200 / w
                new_size = (int(w * ratio), int(h * ratio))
                img = img.resize(new_size, Image.LANCZOS)
            
            self.bruni_img = ImageTk.PhotoImage(img)
        except Exception as e:
            print(f"Error cargando imagen bruni.png: {e}")
    
    def show_profile_section(self):
        """Muestra la sección de perfil de usuario"""
        # Importar funciones aquí para evitar importaciones circulares
        get_user_data, update_user_profile = get_user_data_module()
        
        # Limpiar la ventana actual
        for widget in self.parent.content_frame.winfo_children():
            try:
                widget.destroy()
            except:
                pass
        
        # Obtener datos del usuario actual
        username = getattr(self.parent, 'username', None)
        if not username:
            messagebox.showerror("Error", "No se ha iniciado sesión correctamente")
            return
        
        user_data = get_user_data(username)
        if not user_data:
            messagebox.showerror("Error", "No se pudieron obtener los datos del usuario")
            return
        
        # Crear el contenedor principal
        main_frame = tk.Frame(self.parent.content_frame, bg="white")
        main_frame.pack(fill="both", expand=True, padx=40, pady=30)
        
        # Header y título
        header_frame = tk.Frame(main_frame, bg="white")
        header_frame.pack(fill="x", pady=(0, 20))
        
        title_label = tk.Label(
            header_frame, 
            text="Mi Perfil",
            font=("Segoe UI", 18, "bold"),
            fg="#0B5394",
            bg="white"
        )
        title_label.pack(side="left")
        
        # Imagen de bruni
        if self.bruni_img:
            bruni_label = tk.Label(header_frame, image=self.bruni_img, bg="white")
            bruni_label.pack(side="right")
        
        # Contenedor de la información del perfil
        profile_container = tk.Frame(main_frame, bg="white", bd=1, relief="solid", padx=30, pady=25)
        profile_container.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Formulario para datos del perfil
        form_frame = tk.Frame(profile_container, bg="white")
        form_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Variables para almacenar los datos del formulario
        self.nombre_var = tk.StringVar(value=user_data.get('nombre', ''))
        self.apellido_var = tk.StringVar(value=user_data.get('apellido', ''))
        self.email_var = tk.StringVar(value=user_data.get('email', ''))
        self.telefono_var = tk.StringVar(value=user_data.get('telefono', ''))
        self.current_password_var = tk.StringVar()
        self.new_password_var = tk.StringVar()
        self.confirm_password_var = tk.StringVar()
        
        # Crear etiquetas y campos del formulario
        campo_styles = {"font": ("Segoe UI", 10), "bg": "white"}
        input_styles = {"width": 25, "font": ("Segoe UI", 10)}
        title_styles = {"font": ("Segoe UI", 12, "bold"), "bg": "white", "fg": "#0B5394"}
        
        # Información básica
        info_label = tk.Label(form_frame, text="Información de Cuenta", **title_styles)
        info_label.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))
        
        tk.Label(form_frame, text="Username:", **campo_styles).grid(row=1, column=0, sticky="w", pady=5)
        username_display = tk.Label(form_frame, text=user_data.get('username', ''), **campo_styles)
        username_display.grid(row=1, column=1, sticky="w", pady=5)
        
        tk.Label(form_frame, text="Rol:", **campo_styles).grid(row=2, column=0, sticky="w", pady=5)
        rol_display = tk.Label(form_frame, text=user_data.get('rol', 'usuario'), **campo_styles)
        rol_display.grid(row=2, column=1, sticky="w", pady=5)
        
        tk.Label(form_frame, text="Fecha de creación:", **campo_styles).grid(row=3, column=0, sticky="w", pady=5)
        created_at = user_data.get('createdAt', '')
        if created_at:
            created_at = created_at.strftime('%d/%m/%Y') if hasattr(created_at, 'strftime') else str(created_at)
        created_display = tk.Label(form_frame, text=created_at, **campo_styles)
        created_display.grid(row=3, column=1, sticky="w", pady=5)
        
        tk.Label(form_frame, text="Email:", **campo_styles).grid(row=4, column=0, sticky="w", pady=5)
        email_entry = tk.Entry(form_frame, textvariable=self.email_var, **input_styles)
        email_entry.grid(row=4, column=1, sticky="w", pady=5)
        
        # Separador
        separator = tk.Frame(form_frame, height=2, bg="#e0e0e0")
        separator.grid(row=5, column=0, columnspan=2, sticky="ew", pady=15)
        
        # Cambio de contraseña
        password_label = tk.Label(form_frame, text="Cambiar Contraseña (opcional)", **title_styles)
        password_label.grid(row=6, column=0, columnspan=2, sticky="w", pady=(0, 10))
        
        tk.Label(form_frame, text="Contraseña actual:", **campo_styles).grid(row=7, column=0, sticky="w", pady=5)
        current_pass_entry = tk.Entry(form_frame, textvariable=self.current_password_var, show="*", **input_styles)
        current_pass_entry.grid(row=7, column=1, sticky="w", pady=5)
        
        tk.Label(form_frame, text="Nueva contraseña:", **campo_styles).grid(row=8, column=0, sticky="w", pady=5)
        new_pass_entry = tk.Entry(form_frame, textvariable=self.new_password_var, show="*", **input_styles)
        new_pass_entry.grid(row=8, column=1, sticky="w", pady=5)
        
        tk.Label(form_frame, text="Confirmar contraseña:", **campo_styles).grid(row=9, column=0, sticky="w", pady=5)
        confirm_pass_entry = tk.Entry(form_frame, textvariable=self.confirm_password_var, show="*", **input_styles)
        confirm_pass_entry.grid(row=9, column=1, sticky="w", pady=5)
        
        # Nota sobre campos editables
        note_frame = tk.Frame(main_frame, bg="#f0f0f0", padx=10, pady=10)
        note_frame.pack(fill="x", pady=(0, 15))
        
        note_label = tk.Label(
            note_frame,
            text="Nota: Solo se pueden modificar el correo electrónico y la contraseña en esta versión.",
            font=("Segoe UI", 10, "italic"),
            fg="#555555",
            bg="#f0f0f0",
            wraplength=600,
            justify="left"
        )
        note_label.pack(anchor="w")
        
        # Botones
        buttons_frame = tk.Frame(profile_container, bg="white")
        buttons_frame.pack(fill="x", pady=(20, 10))
        
        # Para el guardado, capturamos update_user_profile en una variable local
        _update_user_profile = update_user_profile  # Asegurarse de usar la función importada
        save_btn = tk.Button(
            buttons_frame, 
            text="Guardar Cambios",
            font=("Segoe UI", 10, "bold"),
            bg="#0B5394", 
            fg="white",
            padx=15,
            pady=8,
            bd=0,
            cursor="hand2",
            command=lambda: self._save_profile(user_data.get('id'), _update_user_profile)
        )
        save_btn.pack(side="right", padx=10)
        
        cancel_btn = tk.Button(
            buttons_frame, 
            text="Cancelar",
            font=("Segoe UI", 10),
            bg="#cccccc", 
            fg="black",
            padx=15,
            pady=8,
            bd=0,
            cursor="hand2",
            command=self.show_profile_section  # Recargar la página
        )
        cancel_btn.pack(side="right", padx=10)
    
    def _save_profile(self, user_id, update_user_profile):
        """Guarda los cambios del perfil"""
        # Validar campos
        nombre = self.nombre_var.get().strip()
        apellido = self.apellido_var.get().strip()
        email = self.email_var.get().strip()
        telefono = self.telefono_var.get().strip()
        
        current_password = self.current_password_var.get().strip()
        new_password = self.new_password_var.get().strip()
        confirm_password = self.confirm_password_var.get().strip()
        
        # Validación básica de correo (simple)
        if email and '@' not in email:
            messagebox.showerror("Error", "El formato del correo electrónico no es válido.")
            return
        
        # Validar cambio de contraseña (si se proporcionó)
        password_change = False
        if current_password or new_password or confirm_password:
            if not current_password:
                messagebox.showerror("Error", "Debe proporcionar la contraseña actual para cambiarla.")
                return
            
            if not new_password:
                messagebox.showerror("Error", "Debe proporcionar una nueva contraseña.")
                return
                
            if new_password != confirm_password:
                messagebox.showerror("Error", "La confirmación de contraseña no coincide.")
                return
                
            if len(new_password) < 6:
                messagebox.showerror("Error", "La contraseña debe tener al menos 6 caracteres.")
                return
            
            password_change = True
        
        # Actualizar perfil
        success, message = update_user_profile(
            user_id, 
            nombre, 
            apellido, 
            email, 
            telefono,
            current_password if password_change else None,
            new_password if password_change else None
        )
        
        if success:
            messagebox.showinfo("Éxito", message)
            # Actualizar el nombre mostrado en la interfaz si fue cambiado
            if hasattr(self.parent, 'username_display') and self.parent.username_display:
                try:
                    new_display = f"{nombre} {apellido}".strip() if nombre or apellido else self.parent.username
                    self.parent.username_display.config(text=new_display)
                except:
                    pass
            # Recargar la página
            self.show_profile_section()
        else:
            messagebox.showerror("Error", message)

# Función auxiliar para integración con la app principal
def add_profile_to_menu(app_instance):
    """Integra la sección de perfil en la aplicación principal"""
    
    # Si no existe la instancia de perfil, crearla
    if not hasattr(app_instance, 'profile_section'):
        app_instance.profile_section = UserProfileSection(app_instance)
    
    # Quitar esta parte para que no aparezca en el menú lateral
    # if hasattr(app_instance, 'menu_sections') and isinstance(app_instance.menu_sections, list):
    #     if "Mi Perfil" not in app_instance.menu_sections:
    #         app_instance.menu_sections.append("Mi Perfil")
    
    # Modificar la función show_section para manejar "Mi Perfil" aunque no esté en el menú
    original_show_section = app_instance.show_section
    
    def enhanced_show_section(section_name):
        if section_name == "Mi Perfil":
            app_instance.profile_section.show_profile_section()
        else:
            original_show_section(section_name)
    
    # Sobrescribir el método
    app_instance.show_section = enhanced_show_section
    
    # Modificar el menú de usuario para incluir "Mi Perfil"
    if hasattr(app_instance, 'show_user_menu'):
        original_show_user_menu = app_instance.show_user_menu
        
        def enhanced_user_menu():
            # Cerrar popup existente si hay uno
            if hasattr(app_instance, '_user_popup') and app_instance._user_popup:
                try:
                    app_instance._user_popup.destroy()
                except:
                    pass
            
            # Crear el nuevo popup
            popup = tk.Toplevel(app_instance.root if hasattr(app_instance, 'root') else app_instance)
            app_instance._user_popup = popup
            
            popup.overrideredirect(True)
            popup.configure(bg="white", bd=2, highlightthickness=2, highlightbackground="#0B5394")
            
            # Calcular posición
            try:
                main_x = app_instance.winfo_rootx()
                main_y = app_instance.winfo_rooty()
                main_w = app_instance.winfo_width()
                popup_w, popup_h = 200, 140  # Altura aumentada para incluir Mi Perfil
                x = main_x + main_w - popup_w - 40
                y = main_y + 70
                
                popup.geometry(f"{popup_w}x{popup_h}+{x}+{y}")
            except:
                # Fallback: posición relativa a pantalla
                popup.geometry("200x140+50+50")
            
            # Contenido del popup
            tk.Label(
                popup,
                text=app_instance.username if hasattr(app_instance, 'username') else "Usuario",
                bg="white",
                fg="#0B5394",
                font=("Segoe UI", 11, "bold")
            ).pack(pady=(10, 2), padx=10)
            
            tk.Frame(popup, bg="#0B5394", height=2).pack(fill="x", padx=10, pady=2)
            
            # Botón Mi Perfil
            tk.Button(
                popup,
                text="Mi Perfil",
                font=("Segoe UI", 11),
                bg="#0B5394",
                fg="white",
                activebackground="#073763",
                activeforeground="white",
                relief="flat",
                command=lambda: [popup.destroy(), app_instance.show_section("Mi Perfil")]
            ).pack(fill="x", padx=20, pady=8)
            
            # Botón Cerrar sesión
            tk.Button(
                popup,
                text="Cerrar sesión",
                font=("Segoe UI", 11),
                bg="#0B5394",
                fg="white",
                activebackground="#073763",
                activeforeground="white",
                relief="flat",
                command=lambda: [popup.destroy(), app_instance.logout() if hasattr(app_instance, 'logout') else None]
            ).pack(fill="x", padx=20, pady=8)
            
            popup.focus_force()
            popup.bind("<FocusOut>", lambda e: popup.destroy())
        
        # Sobrescribir el método
        app_instance.show_user_menu = enhanced_user_menu