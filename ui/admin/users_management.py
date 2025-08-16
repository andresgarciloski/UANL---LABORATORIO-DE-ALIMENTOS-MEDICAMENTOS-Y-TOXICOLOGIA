import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import os
from core.auth import obtener_usuarios, crear_usuario, actualizar_usuario, eliminar_usuario, eliminar_historial_por_usuario
from ui.base_interface import bind_mousewheel

class UsersManagement:
    def __init__(self, parent):
        self.parent = parent
        
    def show_users_table(self):
        """Mostrar tabla de usuarios"""
        # Limpiar contenido anterior de manera segura
        for widget in self.parent.content_frame.winfo_children():
            try:
                widget.destroy()
            except:
                pass

        # Contenedor centrado con padding y margen lateral reducido para usar más ancho
        outer = tk.Frame(self.parent.content_frame, bg="white")
        outer.pack(expand=True, fill="both", padx=24, pady=24)

        center_container = tk.Frame(outer, bg="white")
        # usar relwidth alto para ocupar casi todo el ancho manteniendo espacios laterales
        center_container.place(relx=0.5, rely=0.02, relwidth=0.96, relheight=0.96, anchor="n")

        # Título centrado
        title = tk.Label(
            center_container,
            text="Gestión de Usuarios",
            font=("Segoe UI", 18, "bold"),
            fg="#0B5394",
            bg="white"
        )
        title.pack(pady=(6, 12))

        # Canvas y Scrollbar
        main_canvas = tk.Canvas(center_container, bg="white", highlightthickness=0)
        main_scrollbar = tk.Scrollbar(center_container, orient="vertical", command=main_canvas.yview)
        self.users_table_frame = tk.Frame(main_canvas, bg="white")

        self.users_table_frame.bind(
            "<Configure>",
            lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all"))
        )

        window_id = main_canvas.create_window((0, 0), window=self.users_table_frame, anchor="nw")
        main_canvas.configure(yscrollcommand=main_scrollbar.set)

        # Cuando el canvas cambie de tamaño, ajustar el width de la ventana interna
        main_canvas.bind("<Configure>", lambda e: main_canvas.itemconfig(window_id, width=e.width))

        main_canvas.pack(side="left", fill="both", expand=True)
        main_scrollbar.pack(side="right", fill="y")

        bind_mousewheel(self.users_table_frame, main_canvas)

        # Botón agregar usuario con borde y estilo mejorado
        actions_frame = tk.Frame(self.users_table_frame, bg="white")
        actions_frame.pack(fill="x", padx=12, pady=(5, 10))

        # Subtítulo explicativo
        subtitle = tk.Label(
            actions_frame, 
            text="Administración de cuentas del sistema",
            font=("Segoe UI", 12, "bold"),
            fg="#0B5394",
            bg="white"
        )
        subtitle.pack(side="left", anchor="w")

        # Cargar icono "+" para agregar usuario
        plus_path = os.path.join(os.path.dirname(__file__), "..", "..", "img", "+.png")
        plus_path = os.path.abspath(plus_path)
        
        try:
            plus_img = Image.open(plus_path).resize((24, 24), Image.LANCZOS)
            plus_icon = ImageTk.PhotoImage(plus_img)
            self.plus_icon = plus_icon
        except Exception:
            plus_icon = None

        # Botón con estilo unificado
        add_btn = tk.Button(
            actions_frame,
            text="Agregar Usuario" + (" " if plus_icon else ""),
            image=plus_icon if plus_icon else None,
            compound="right" if plus_icon else "center",
            bg="#0B5394",
            fg="white",
            font=("Segoe UI", 10, "bold"),
            bd=0,
            padx=15,
            pady=6,
            cursor="hand2",
            activebackground="#073763",
            activeforeground="white",
            command=self.add_user_popup
        )
        add_btn.pack(side="right", pady=5)

        # Frame contenedor para la tabla con borde
        table_container = tk.Frame(self.users_table_frame, bg="white", padx=12, pady=12)
        table_container.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        # Crear tabla de usuarios
        self._create_users_table(table_container)

    def _create_users_table(self, container):
        """Crear una tabla normal y centrada usando ttk.Treeview (apariencia tipo tabla)"""
        from tkinter import ttk

        # Limpiar contenedor
        for w in container.winfo_children():
            try:
                w.destroy()
            except:
                pass

        # Título y encabezado ya están fuera; construimos tabla limpia
        cols = ("id", "username", "email", "rol")

        # Frame para la tabla y scrollbar
        table_frame = tk.Frame(container, bg="white")
        table_frame.pack(fill="both", expand=True, padx=8, pady=8)

        v_scroll = tk.Scrollbar(table_frame, orient="vertical")
        v_scroll.pack(side="right", fill="y")

        h_scroll = tk.Scrollbar(table_frame, orient="horizontal")
        h_scroll.pack(side="bottom", fill="x")

        style = ttk.Style()
        style.theme_use('default')
        # Ajustes visuales: encabezado color y fuente
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"), background="#0B5394", foreground="white")
        style.configure("Treeview", font=("Segoe UI", 10), rowheight=28)
        # Eliminar borde resaltado para que se vea más "plano"
        style.layout("Treeview", [('Treeview.treearea', {'sticky': 'nswe'})])

        tree = ttk.Treeview(
            table_frame,
            columns=cols,
            show="headings",
            yscrollcommand=v_scroll.set,
            xscrollcommand=h_scroll.set,
            selectmode="browse"
        )
        v_scroll.config(command=tree.yview)
        h_scroll.config(command=tree.xview)

        # Definir encabezados y anchos
        tree.heading("id", text="ID", anchor="center")
        tree.heading("username", text="Usuario", anchor="center")
        tree.heading("email", text="Email", anchor="center")
        tree.heading("rol", text="Rol", anchor="center")

        # Ajuste de columnas (ancho relativo)
        tree.column("id", width=70, anchor="center", stretch=False)
        tree.column("username", width=220, anchor="center")
        tree.column("email", width=340, anchor="center")
        tree.column("rol", width=140, anchor="center")

        tree.pack(fill="both", expand=True, side="left")

        # Obtener usuarios y poblar árbol
        try:
            usuarios = obtener_usuarios()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron cargar los usuarios: {e}")
            usuarios = []

        for user in usuarios:
            user_id, username, email, rol = user
            tree.insert("", "end", iid=str(user_id), values=(user_id, username, email, rol))

        # Frame de acciones (editar/eliminar) debajo de la tabla
        actions_bottom = tk.Frame(container, bg="white")
        actions_bottom.pack(fill="x", pady=(12, 2), padx=8)

        def get_selected_user():
            sel = tree.selection()
            if not sel:
                messagebox.showwarning("Seleccionar usuario", "Por favor selecciona un usuario de la tabla.")
                return None
            item_id = sel[0]
            vals = tree.item(item_id, "values")
            # vals: (id, username, email, rol)
            return (int(vals[0]), vals[1], vals[2], vals[3])

        def on_edit_selected():
            u = get_selected_user()
            if u:
                # abrir popup para editar
                self.edit_user_popup(u)

        def on_delete_selected():
            u = get_selected_user()
            if u:
                uid = u[0]
                self.delete_user(uid)

        edit_btn = tk.Button(
            actions_bottom,
            text="Editar seleccionado",
            font=("Segoe UI", 11),
            bg="#0B5394",
            fg="white",
            bd=0,
            padx=12,
            pady=8,
            cursor="hand2",
            command=on_edit_selected
        )
        edit_btn.pack(side="left", padx=(0, 8))

        delete_btn = tk.Button(
            actions_bottom,
            text="Eliminar seleccionado",
            font=("Segoe UI", 11),
            bg="#d9534f",
            fg="white",
            bd=0,
            padx=12,
            pady=8,
            cursor="hand2",
            command=on_delete_selected
        )
        delete_btn.pack(side="left")

        # Doble click en fila abre edición
        def on_double_click(event):
            item = tree.identify_row(event.y)
            if item:
                vals = tree.item(item, "values")
                self.edit_user_popup((int(vals[0]), vals[1], vals[2], vals[3]))

        tree.bind("<Double-1>", on_double_click)

        # Ajustar foco/selección inicial
        if tree.get_children():
            first = tree.get_children()[0]
            tree.selection_set(first)

    def add_user_popup(self):
        """Popup para agregar usuario"""
        popup = tk.Toplevel(self.parent)
        popup.title("Agregar nuevo usuario")
        
        # Ventana más grande: 520x560
        window_width = 520
        window_height = 560
        
        popup.geometry(f"{window_width}x{window_height}")
        popup.configure(bg="white")
        popup.resizable(False, False)
        popup.grab_set()
        
        # Centrar popup con nuevas dimensiones
        popup.transient(self.parent)
        popup.update_idletasks()
        x = (popup.winfo_screenwidth() // 2) - (window_width // 2)
        y = (popup.winfo_screenheight() // 2) - (window_height // 2)
        popup.geometry(f"{window_width}x{window_height}+{x}+{y}")

        # Título
        tk.Label(
            popup, 
            text="Nuevo Usuario",
            font=("Segoe UI", 18, "bold"),
            fg="#0B5394",
            bg="white"
        ).pack(pady=(30, 20))  # Ajuste de espaciado

        # Formulario estilizado
        form_frame = tk.Frame(popup, bg="white")
        form_frame.pack(fill="both", expand=True, padx=40, pady=0)  # Más padding horizontal

        field_style = {"font": ("Segoe UI", 12), "bg": "white"}
        entry_style = {"font": ("Segoe UI", 12), "width": 36}  # Campos más anchos

        tk.Label(form_frame, text="Usuario:", **field_style).pack(anchor="w", pady=(0, 6))
        username_entry = tk.Entry(form_frame, **entry_style)
        username_entry.pack(fill="x", pady=(0, 18))  # Más espacio entre campos

        tk.Label(form_frame, text="Email:", **field_style).pack(anchor="w", pady=(0, 6))
        email_entry = tk.Entry(form_frame, **entry_style)
        email_entry.pack(fill="x", pady=(0, 18))

        tk.Label(form_frame, text="Contraseña:", **field_style).pack(anchor="w", pady=(0, 6))
        password_entry = tk.Entry(form_frame, show="*", **entry_style)
        password_entry.pack(fill="x", pady=(0, 18))

        tk.Label(form_frame, text="Rol:", **field_style).pack(anchor="w", pady=(0, 6))
        rol_var = tk.StringVar(value="usuario")
        rol_frame = tk.Frame(form_frame, bg="white")
        rol_frame.pack(fill="x", pady=(0, 18))
        
        # Opciones de rol con mejor estilo y distribución más espaciada
        rb_style = {"font": ("Segoe UI", 11), "bg": "white", "activebackground": "white"}
        tk.Radiobutton(rol_frame, text="Usuario", variable=rol_var, value="usuario", **rb_style).pack(side="left", padx=24)
        tk.Radiobutton(rol_frame, text="Administrador", variable=rol_var, value="admin", **rb_style).pack(side="left", padx=24)

        # Botones con estilo
        btn_frame = tk.Frame(popup, bg="white")
        btn_frame.pack(fill="x", pady=28, padx=40)  # Más espacio para botones

        def create_user():
            username = username_entry.get().strip()
            email = email_entry.get().strip()
            password = password_entry.get()
            rol = rol_var.get()
            
            if not username or not email or not password:
                messagebox.showerror("Error", "Todos los campos son obligatorios.", parent=popup)
                return
                
            try:
                crear_usuario(username, email, password, rol)
                messagebox.showinfo("Éxito", "Usuario creado correctamente.", parent=popup)
                popup.destroy()
                self.show_users_table()
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo crear el usuario: {e}", parent=popup)

        # Botón estilo consistente pero más grande
        btn_create = tk.Button(
            btn_frame,
            text="Crear Usuario",
            font=("Segoe UI", 13, "bold"),  # Fuente más grande
            bg="#0B5394",
            fg="white",
            activebackground="#073763",
            activeforeground="white",
            relief="flat",
            cursor="hand2",
            padx=24,
            pady=12,  # Botón más alto
            command=create_user
        )
        btn_create.pack(fill="x")

    def edit_user_popup(self, user):
        """Popup para editar usuario con estilo mejorado"""
        user_id, username, email, rol = user
        popup = tk.Toplevel(self.parent)
        popup.title(f"Editar usuario: {username}")
        
        # Ventana más grande: 500x520
        window_width = 500
        window_height = 520
        
        popup.geometry(f"{window_width}x{window_height}")
        popup.configure(bg="white")
        popup.resizable(False, False)
        popup.grab_set()
        
        # Centrar popup
        popup.transient(self.parent)
        popup.update_idletasks()
        x = (popup.winfo_screenwidth() // 2) - (window_width // 2)
        y = (popup.winfo_screenheight() // 2) - (window_height // 2)
        popup.geometry(f"{window_width}x{window_height}+{x}+{y}")

        # Título
        tk.Label(
            popup, 
            text=f"Editar Usuario",
            font=("Segoe UI", 16, "bold"),
            fg="#0B5394",
            bg="white"
        ).pack(pady=(22, 8))

        # Subtítulo con usuario
        tk.Label(
            popup, 
            text=username,
            font=("Segoe UI", 12),
            fg="#555555",
            bg="white"
        ).pack(pady=(0, 16))

        # Formulario estilizado
        form_frame = tk.Frame(popup, bg="white")
        form_frame.pack(fill="both", expand=True, padx=36, pady=0)

        field_style = {"font": ("Segoe UI", 12), "bg": "white"}
        entry_style = {"font": ("Segoe UI", 12), "width": 34}

        tk.Label(form_frame, text="Usuario:", **field_style).pack(anchor="w", pady=(0, 6))
        username_entry = tk.Entry(form_frame, **entry_style)
        username_entry.insert(0, username)
        username_entry.pack(fill="x", pady=(0, 14))

        tk.Label(form_frame, text="Email:", **field_style).pack(anchor="w", pady=(0, 6))
        email_entry = tk.Entry(form_frame, **entry_style)
        email_entry.insert(0, email)
        email_entry.pack(fill="x", pady=(0, 14))

        tk.Label(form_frame, text="Contraseña nueva:", **field_style).pack(anchor="w", pady=(0, 6))
        password_entry = tk.Entry(form_frame, show="*", **entry_style)
        password_entry.pack(fill="x", pady=(0, 8))
        
        tk.Label(form_frame, text="(Dejar vacío para mantener la actual)", 
                font=("Segoe UI", 10), bg="white", fg="#888").pack(anchor="w", pady=(0, 14))

        tk.Label(form_frame, text="Rol:", **field_style).pack(anchor="w", pady=(0, 6))
        rol_var = tk.StringVar(value=rol)
        rol_frame = tk.Frame(form_frame, bg="white")
        rol_frame.pack(fill="x", pady=(0, 14))
        
        # Opciones de rol con mejor estilo
        rb_style = {"font": ("Segoe UI", 11), "bg": "white", "activebackground": "white"}
        tk.Radiobutton(rol_frame, text="Usuario", variable=rol_var, value="usuario", **rb_style).pack(side="left", padx=12)
        tk.Radiobutton(rol_frame, text="Administrador", variable=rol_var, value="admin", **rb_style).pack(side="left", padx=12)

        # Botones con estilo
        btn_frame = tk.Frame(popup, bg="white")
        btn_frame.pack(fill="x", pady=20, padx=36)

        def save_changes():
            nuevo_username = username_entry.get().strip()
            nuevo_email = email_entry.get().strip()
            nuevo_rol = rol_var.get()
            nueva_contra = password_entry.get().strip()
            
            if not nuevo_username or not nuevo_email:
                messagebox.showerror("Error", "Usuario y email son obligatorios.", parent=popup)
                return
                
            try:
                if nueva_contra:
                    actualizar_usuario(user_id, nuevo_username, nuevo_email, nuevo_rol, nueva_contra)
                else:
                    actualizar_usuario(user_id, nuevo_username, nuevo_email, nuevo_rol)
                messagebox.showinfo("Éxito", "Usuario actualizado correctamente.", parent=popup)
                popup.destroy()
                self.show_users_table()
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo actualizar el usuario: {e}", parent=popup)

        # Botones con estilos consistentes
        btn_save = tk.Button(
            btn_frame,
            text="Guardar Cambios",
            font=("Segoe UI", 12, "bold"),
            bg="#0B5394",
            fg="white",
            activebackground="#073763",
            activeforeground="white",
            relief="flat",
            cursor="hand2",
            padx=18,
            pady=10,
            command=save_changes
        )
        btn_save.pack(fill="x")

    def delete_user(self, user_id):
        """Eliminar usuario con confirmación mejorada"""
        if messagebox.askyesno("Eliminar usuario", 
                              "¿Estás seguro de que deseas eliminar este usuario?\n\n"
                              "Esta acción eliminará también todo su historial asociado y no se puede deshacer.",
                              icon='warning'):
            try:
                eliminar_historial_por_usuario(user_id)
                eliminar_usuario(user_id)
                messagebox.showinfo("Éxito", "Usuario eliminado correctamente.")
                self.show_users_table()
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo eliminar el usuario: {e}")