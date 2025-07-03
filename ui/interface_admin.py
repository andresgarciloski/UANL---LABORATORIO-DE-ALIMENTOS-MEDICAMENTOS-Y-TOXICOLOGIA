import tkinter as tk
from tkinter import messagebox, filedialog
from PIL import Image, ImageDraw, ImageTk
import os
import pandas as pd
import zipfile
import io
import datetime
from tkcalendar import DateEntry  # Agrega esto al inicio del archivo

from core.auth import (
    obtener_usuarios, 
    actualizar_usuario, 
    eliminar_usuario, 
    obtener_historial, 
    agregar_historial, 
    crear_usuario,
    eliminar_historial_por_usuario,
    eliminar_registro_historial,
    importar_registro
)

def bind_mousewheel(widget, canvas):
    """Función para enlazar el scroll del mouse a un canvas"""
    def _on_mousewheel(event):
        canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    
    def _bind_to_mousewheel(event):
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
    
    def _unbind_from_mousewheel(event):
        canvas.unbind_all("<MouseWheel>")
    
    widget.bind('<Enter>', _bind_to_mousewheel)
    widget.bind('<Leave>', _unbind_from_mousewheel)

class MainInterfaceAdmin(tk.Tk):
    def __init__(self, username=None, rol="admin"):
        super().__init__()
        self.title("UANL FoodLab")
        self.geometry("1000x600")
        self.configure(bg="white")
        self.username = username
        self.rol = rol  # Puedes usarlo si lo necesitas

        self.menu_visible = True  # Estado del menú lateral

        self.create_widgets()

    def create_widgets(self):
        # Header
        header = tk.Frame(self, bg="#0B5394", height=60)
        header.pack(side="top", fill="x")

        # Botón del menú lateral
        self.menu_toggle_btn = tk.Button(
            header,
            text="☰",
            font=("Segoe UI", 16, "bold"),
            bg="#0B5394",
            fg="white",
            bd=0,
            activebackground="#073763",
            activeforeground="white",
            cursor="hand2",
            command=self.toggle_menu
        )
        self.menu_toggle_btn.pack(side="left", padx=(20, 10), pady=10)

        # Título clickable
        title = tk.Label(
            header,
            text="UANL FoodLab",
            bg="#0B5394",
            fg="white",
            font=("Segoe UI", 16, "bold"),
            padx=10,
            cursor="hand2"
        )
        title.pack(side="left", pady=10)
        title.bind("<Button-1>", lambda e: self.show_section("Inicio"))

        # --- Usuario y foto circular ---
        user_frame = tk.Frame(header, bg="#0B5394")
        user_frame.pack(side="right", padx=20)

        user_label = tk.Label(
            user_frame,
            text=self.username if self.username else "Usuario",
            bg="#0B5394",
            fg="white",
            font=("Segoe UI", 12, "bold"),
            padx=10
        )
        user_label.pack(side="left")

        # Imagen circular (ahora user.png)
        img_path = os.path.join(os.path.dirname(__file__), "..", "img", "user.png")
        img_path = os.path.abspath(img_path)
        user_img = Image.open(img_path).resize((40, 40), Image.LANCZOS)  # Tamaño reducido
        mask = Image.new('L', (40, 40), 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0, 40, 40), fill=255)
        user_img.putalpha(mask)
        self.user_icon = ImageTk.PhotoImage(user_img)
        self.user_btn = tk.Button(
            user_frame,
            image=self.user_icon,
            bg="#0B5394",
            bd=0,
            activebackground="#0B5394",
            cursor="hand2",
            command=self.show_user_menu
        )
        self.user_btn.pack(side="left")

        # Menú lateral (Frame) - ahora será un Toplevel para transparencia y overlay
        self.menu_frame = None
        self.create_side_menu()

        # Zona de contenido
        self.content_frame = tk.Frame(self, bg="white")
        self.content_frame.pack(expand=True, fill="both")

        self.show_section("Inicio")

    def create_side_menu(self):
        # Si ya existe, destrúyelo para evitar duplicados
        if hasattr(self, "menu_frame") and self.menu_frame is not None:
            self.menu_frame.destroy()

        # Crear menú lateral como Toplevel SIN transparencia
        self.menu_frame = tk.Toplevel(self)
        self.menu_frame.overrideredirect(True)
        self.menu_frame.attributes('-topmost', True)
        self.menu_frame.configure(bg="#0B5394")  # Mismo color que el header

        self.update_side_menu_geometry()

        # Contenido del menú
        menu_label = tk.Label(
            self.menu_frame,
            text="Menú",
            bg="#0B5394",
            fg="white",
            font=("Segoe UI", 15, "bold")
        )
        menu_label.pack(pady=(25, 15), anchor="w", padx=30)

        # Solo las opciones requeridas para admin
        sections = ["Exportar/Importar DB", "Usuarios", "Registro"]
        self.menu_buttons = []
        for section in sections:
            btn = tk.Button(
                self.menu_frame,
                text=section,
                relief="flat",
                bg="#0B5394",
                fg="white",
                font=("Segoe UI", 13),
                anchor="w",
                padx=30,
                pady=12,
                activebackground="#073763",
                activeforeground="white",
                command=lambda s=section: [self.show_section(s), self.toggle_menu()]
            )
            btn.pack(fill="x", pady=2)
            self.menu_buttons.append(btn)

        # Línea separadora
        sep = tk.Frame(self.menu_frame, bg="#073763", height=2)
        sep.pack(fill="x", padx=20, pady=10)

        # Botón para cerrar el menú
        close_btn = tk.Button(
            self.menu_frame,
            text="⨉",
            font=("Segoe UI", 16, "bold"),
            bg="#0B5394",
            fg="white",
            bd=0,
            activebackground="#073763",
            activeforeground="white",
            command=self.toggle_menu,
            cursor="hand2"
        )
        close_btn.place(x=220, y=10, width=30, height=30)

        # Mantener menú alineado al cambiar tamaño/mover ventana
        self.bind("<Configure>", lambda e: self.update_side_menu_geometry() if self.menu_visible else None)

    def update_side_menu_geometry(self):
        # Calcula posición y tamaño para cubrir todo el lateral izquierdo, justo debajo del header
        self.update_idletasks()
        x = self.winfo_rootx()
        y = self.winfo_rooty()
        h = self.winfo_height()
        header_height = 60  # Altura del banner superior
        self.menu_frame.geometry(f"260x{h-header_height}+{x}+{y+header_height}")

    def toggle_menu(self):
        if hasattr(self, "menu_frame") and self.menu_frame is not None and self.menu_visible:
            self.menu_frame.withdraw()
            self.menu_visible = False
        else:
            self.create_side_menu()
            self.menu_frame.deiconify()
            self.menu_visible = True

    def show_user_menu(self):
        # Crear ventana tipo popup personalizada dentro de la ventana principal
        popup = tk.Toplevel(self)
        popup.overrideredirect(True)
        popup.configure(bg="white", bd=2, highlightthickness=2, highlightbackground="#0B5394")

        # Calcular posición centrada respecto a la ventana principal
        main_x = self.winfo_rootx()
        main_y = self.winfo_rooty()
        main_w = self.winfo_width()
        popup_w, popup_h = 200, 90
        x = main_x + main_w - popup_w - 40  # 40px de margen a la derecha
        y = main_y + 70  # Debajo del header

        popup.geometry(f"{popup_w}x{popup_h}+{x}+{y}")

        # Nombre de usuario en negritas
        tk.Label(
            popup,
            text=self.username if self.username else "Usuario",
            bg="white",
            fg="#0B5394",
            font=("Segoe UI", 11, "bold")
        ).pack(pady=(10, 2), padx=10)

        # Línea separadora
        tk.Frame(popup, bg="#0B5394", height=2).pack(fill="x", padx=10, pady=2)

        # Botón cerrar sesión
        tk.Button(
            popup,
            text="Cerrar sesión",
            font=("Segoe UI", 11),
            bg="#0B5394",
            fg="white",
            activebackground="#073763",
            activeforeground="white",
            relief="flat",
            command=lambda: [popup.destroy(), self.logout()]
        ).pack(fill="x", padx=20, pady=10)

        # Cerrar el popup si pierde foco
        popup.focus_force()
        popup.bind("<FocusOut>", lambda e: popup.destroy())

    def logout(self):
        if messagebox.askyesno("Cerrar sesión", "¿Deseas cerrar sesión?"):
            self.destroy()
            from ui.login_screen import LoginWindow
            login = LoginWindow()
            login.mainloop()

    def show_section(self, section_name):
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        if section_name == "Inicio":
            # CAMBIO: Crear un frame principal que ocupe todo el espacio
            main_frame = tk.Frame(self.content_frame, bg="white")
            main_frame.pack(fill="both", expand=True)
            
            # CAMBIO: Canvas y Scrollbar para scroll
            canvas = tk.Canvas(main_frame, bg="white")
            scrollbar = tk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
            
            # CAMBIO: Frame contenedor centrado
            content_frame = tk.Frame(canvas, bg="white")
            
            # CAMBIO: Función para centrar el contenido cuando cambie el tamaño
            def center_content(event=None):
                canvas.update_idletasks()
                
                # Obtener dimensiones
                canvas_width = canvas.winfo_width()
                canvas_height = canvas.winfo_height()
                content_width = content_frame.winfo_reqwidth()
                content_height = content_frame.winfo_reqheight()
                
                # Calcular posición centrada
                x = max(0, (canvas_width - content_width) // 2)
                y = max(0, (canvas_height - content_height) // 2)
                
                # Configurar la región de scroll y posición
                canvas.configure(scrollregion=(0, 0, content_width, content_height))
                canvas.coords(canvas_window_id, x, y)

            # Crear ventana del contenido en el canvas
            canvas_window_id = canvas.create_window(0, 0, window=content_frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)

            # Imagen de Bruni centrada (más grande)
            img_path = os.path.join(os.path.dirname(__file__), "..", "img", "bruni.png")
            img_path = os.path.abspath(img_path)
            bruni_img = Image.open(img_path).resize((200, 200), Image.LANCZOS)
            mask = Image.new('L', (200, 200), 0)
            draw = ImageDraw.Draw(mask)
            draw.ellipse((0, 0, 200, 200), fill=255)
            bruni_img.putalpha(mask)
            bruni_photo = ImageTk.PhotoImage(bruni_img)
            img_label = tk.Label(content_frame, image=bruni_photo, bg="white")
            img_label.image = bruni_photo  # Referencia para evitar garbage collection
            img_label.pack(pady=(20, 20))

            # Texto de bienvenida
            welcome = tk.Label(
                content_frame,
                text=f"¡Bienvenido, {self.username if self.username else 'Usuario'}!",
                font=("Segoe UI", 22, "bold"),
                fg="#0B5394",
                bg="white"
            )
            welcome.pack(pady=(0, 15))

            # NUEVO TEXTO INFORMATIVO
            info = tk.Label(
                content_frame,
                text=(
                    "Panel de administración de la base de datos FoodLab.\n\n"
                    "Desde este panel puedes:\n"
                    "• Exportar e importar todos los registros y archivos adjuntos de la base de datos en formato ZIP.\n"
                    "• Consultar, editar, eliminar y agregar nuevos usuarios fácilmente (usa el botón '+').\n"
                    "• Cambiar el rol de usuario entre 'usuario' y 'admin'.\n"
                    "• Consultar, descargar o eliminar registros del historial.\n"
                    "• Eliminar usuarios junto con su historial asociado.\n\n"
                    "Utiliza las opciones del menú lateral para acceder a cada funcionalidad."
                ),
                font=("Segoe UI", 13),
                fg="#333333",
                bg="white",
                justify="center"
            )
            info.pack(pady=(0, 20))

            # CAMBIO: Enlazar eventos para centrar
            content_frame.bind("<Configure>", center_content)
            canvas.bind("<Configure>", center_content)
            
            # Configurar el layout
            canvas.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")
            
            # NUEVO: Enlazar scroll del mouse
            bind_mousewheel(canvas, canvas)
            
            # Llamar center_content después de un breve delay para asegurar que todo esté renderizado
            self.after(100, center_content)

        elif section_name == "Usuarios":
            self.show_users_table()
        elif section_name == "Registro":
            self.show_historial_table()
        elif section_name == "Exportar/Importar DB":
            self.show_exportar_excel()
        else:
            label = tk.Label(
                self.content_frame,
                text=f"Sección: {section_name}",
                font=("Segoe UI", 14),
                bg="white"
            )
            label.pack(pady=20)

    def show_users_table(self):
        # Si ya existe el frame de la tabla, destrúyelo para evitar duplicados
        if hasattr(self, "users_table_frame") and self.users_table_frame is not None:
            self.users_table_frame.destroy()

        # CAMBIO: Agregar Canvas y Scrollbar
        main_canvas = tk.Canvas(self.content_frame, bg="white")
        main_scrollbar = tk.Scrollbar(self.content_frame, orient="vertical", command=main_canvas.yview)
        self.users_table_frame = tk.Frame(main_canvas, bg="white")

        self.users_table_frame.bind(
            "<Configure>",
            lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all"))
        )

        main_canvas.create_window((0, 0), window=self.users_table_frame, anchor="nw")
        main_canvas.configure(yscrollcommand=main_scrollbar.set)

        # --- Botón agregar usuario (+) ---
        plus_path = os.path.join(os.path.dirname(__file__), "..", "img", "+.png")
        plus_path = os.path.abspath(plus_path)
        plus_img = Image.open(plus_path).resize((24, 24), Image.LANCZOS)
        plus_icon = ImageTk.PhotoImage(plus_img)
        self.plus_icon = plus_icon  # Mantener referencia

        # CAMBIO: Agregar padding superior
        padding_frame = tk.Frame(self.users_table_frame, bg="white", height=30)
        padding_frame.pack(fill="x")

        add_btn = tk.Button(
            self.users_table_frame,
            image=self.plus_icon,
            bg="white",
            bd=0,
            activebackground="#b3d1f7",
            cursor="hand2",
            command=self.add_user_popup
        )
        add_btn.pack(anchor="w", padx=30, pady=(0, 8))

        # CAMBIO: Frame contenedor para la tabla con ancho completo y bordes
        table_frame = tk.Frame(self.users_table_frame, bg="white")
        table_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))  # Borde de 20px

        # Encabezados con diseño azul
        headers = ["ID", "Usuario", "Email", "Rol", "Editar", "Eliminar"]
        header_bg = "#0B5394"
        header_fg = "white"
        for col, h in enumerate(headers):
            header_label = tk.Label(
                table_frame, text=h, font=("Segoe UI", 11, "bold"),
                bg=header_bg, fg=header_fg, padx=15, pady=12, borderwidth=0, relief="flat"
            )
            header_label.grid(row=0, column=col, sticky="nsew", padx=1, pady=1)

        # Cargar imagen de lápiz y basura
        lapiz_path = os.path.join(os.path.dirname(__file__), "..", "img", "lapiz.png")
        lapiz_path = os.path.abspath(lapiz_path)
        lapiz_img = Image.open(lapiz_path).resize((20, 20), Image.LANCZOS)
        lapiz_icon = ImageTk.PhotoImage(lapiz_img)
        self.lapiz_icon = lapiz_icon  # Mantener referencia

        basura_path = os.path.join(os.path.dirname(__file__), "..", "img", "basura.png")
        basura_path = os.path.abspath(basura_path)
        basura_img = Image.open(basura_path).resize((20, 20), Image.LANCZOS)
        basura_icon = ImageTk.PhotoImage(basura_img)
        self.basura_icon = basura_icon  # Mantener referencia

        # Obtener usuarios de la base de datos
        usuarios = obtener_usuarios()  # Debe regresar una lista de tuplas: (id, username, email, rol)

        row_bg1 = "#e6f0fa"
        row_bg2 = "#f7fbff"
        for row, user in enumerate(usuarios, start=1):
            user_id, username, email, rol = user
            bg = row_bg1 if row % 2 == 1 else row_bg2

            # CAMBIO: Agregar más padding y mejor espaciado
            tk.Label(table_frame, text=user_id, bg=bg, font=("Segoe UI", 10), borderwidth=0, relief="flat", padx=15, pady=8).grid(row=row, column=0, sticky="nsew", padx=1, pady=1)
            tk.Label(table_frame, text=username, bg=bg, font=("Segoe UI", 10), borderwidth=0, relief="flat", padx=15, pady=8).grid(row=row, column=1, sticky="nsew", padx=1, pady=1)
            tk.Label(table_frame, text=email, bg=bg, font=("Segoe UI", 10), borderwidth=0, relief="flat", padx=15, pady=8).grid(row=row, column=2, sticky="nsew", padx=1, pady=1)
            tk.Label(table_frame, text=rol, bg=bg, font=("Segoe UI", 10), borderwidth=0, relief="flat", padx=15, pady=8).grid(row=row, column=3, sticky="nsew", padx=1, pady=1)

            edit_btn = tk.Button(
                table_frame,
                image=self.lapiz_icon,
                bg=bg,
                bd=0,
                activebackground="#b3d1f7",
                cursor="hand2",
                command=lambda u=user: self.edit_user_popup(u)
            )
            edit_btn.grid(row=row, column=4, padx=8, pady=4, sticky="nsew")

            delete_btn = tk.Button(
                table_frame,
                image=self.basura_icon,
                bg=bg,
                bd=0,
                activebackground="#f7bdbd",
                cursor="hand2",
                command=lambda uid=user_id: self.delete_user(uid)
            )
            delete_btn.grid(row=row, column=5, padx=8, pady=4, sticky="nsew")

        # CAMBIO: Hacer que las columnas se expandan proporcionalmente
        table_frame.grid_columnconfigure(0, weight=1, minsize=60)   # ID - más pequeña
        table_frame.grid_columnconfigure(1, weight=3, minsize=120)  # Usuario - más grande
        table_frame.grid_columnconfigure(2, weight=4, minsize=180)  # Email - la más grande
        table_frame.grid_columnconfigure(3, weight=2, minsize=80)   # Rol - mediana
        table_frame.grid_columnconfigure(4, weight=1, minsize=60)   # Editar - pequeña
        table_frame.grid_columnconfigure(5, weight=1, minsize=60)   # Eliminar - pequeña

        main_canvas.pack(side="left", fill="both", expand=True)
        main_scrollbar.pack(side="right", fill="y")
        
        # NUEVO: Enlazar scroll del mouse
        bind_mousewheel(main_canvas, main_canvas)

    def edit_user_popup(self, user):
        user_id, username, email, rol = user
        popup = tk.Toplevel(self)
        popup.title(f"Editar usuario: {username}")
        popup.geometry("350x370")
        popup.configure(bg="white")
        popup.resizable(False, False)
        popup.grab_set()

        tk.Label(popup, text="Usuario:", font=("Segoe UI", 11), bg="white").pack(pady=(20, 5))
        username_entry = tk.Entry(popup, font=("Segoe UI", 11), width=25)
        username_entry.insert(0, username)
        username_entry.pack()

        tk.Label(popup, text="Email:", font=("Segoe UI", 11), bg="white").pack(pady=(10, 5))
        email_entry = tk.Entry(popup, font=("Segoe UI", 11), width=25)
        email_entry.insert(0, email)
        email_entry.pack()

        tk.Label(popup, text="Contraseña nueva:", font=("Segoe UI", 11), bg="white").pack(pady=(10, 5))
        password_entry = tk.Entry(popup, font=("Segoe UI", 11), width=25, show="*")
        password_entry.pack()
        tk.Label(popup, text="(Déjalo vacío si no deseas cambiar la contraseña)", font=("Segoe UI", 9), bg="white", fg="#888").pack(pady=(0, 5))

        tk.Label(popup, text="Rol:", font=("Segoe UI", 11), bg="white").pack(pady=(10, 5))
        rol_var = tk.StringVar(value=rol)
        rol_frame = tk.Frame(popup, bg="white")
        rol_frame.pack()
        tk.Radiobutton(rol_frame, text="usuario", variable=rol_var, value="usuario", font=("Segoe UI", 10), bg="white").pack(side="left", padx=10)
        tk.Radiobutton(rol_frame, text="admin", variable=rol_var, value="admin", font=("Segoe UI", 10), bg="white").pack(side="left", padx=10)

        def save_changes():
            nuevo_username = username_entry.get().strip()
            nuevo_email = email_entry.get().strip()
            nuevo_rol = rol_var.get()
            nueva_contra = password_entry.get().strip()
            
            if not nuevo_username or not nuevo_email:
                messagebox.showerror("Error", "Usuario y email son obligatorios.", parent=popup)
                return
                
            try:
                # Si la contraseña está vacía, no la cambies
                if nueva_contra:
                    actualizar_usuario(user_id, nuevo_username, nuevo_email, nuevo_rol, nueva_contra)
                else:
                    actualizar_usuario(user_id, nuevo_username, nuevo_email, nuevo_rol)
                messagebox.showinfo("Éxito", "Usuario actualizado correctamente.", parent=popup)
                popup.destroy()
                self.show_users_table()  # Actualizar la tabla
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo actualizar el usuario: {e}", parent=popup)

        tk.Button(
            popup,
            text="Guardar cambios",
            font=("Segoe UI", 11, "bold"),
            bg="#0B5394",
            fg="white",
            activebackground="#073763",
            activeforeground="white",
            relief="flat",
            command=save_changes
        ).pack(fill="x", padx=40, pady=20, ipady=8)

    def update_user_row(self, user_id, nuevo_username, nuevo_email, nuevo_rol):
        # Busca la fila correspondiente y actualiza solo los valores de esa fila
        for widget in self.users_table_frame.winfo_children():
            info = widget.grid_info()
            if info.get("row") is not None and info.get("column") == 0:
                if str(widget.cget("text")) == str(user_id):
                    row = info["row"]
                    # Actualiza los campos de esa fila
                    for w in self.users_table_frame.winfo_children():
                        if w.grid_info().get("row") == row:
                            col = w.grid_info().get("column")
                            if col == 1:
                                w.config(text=nuevo_username)
                            elif col == 2:
                                w.config(text=nuevo_email)
                            elif col == 3:
                                w.config(text=nuevo_rol)
                    break

    def delete_user(self, user_id):
        """Elimina un usuario y su historial asociado"""
        if messagebox.askyesno("Eliminar usuario", "¿Estás seguro de que deseas eliminar este usuario?\nEsto también eliminará su historial asociado."):
            try:
                # Primero eliminar el historial del usuario
                eliminar_historial_por_usuario(user_id)
                # Luego eliminar el usuario
                eliminar_usuario(user_id)
                messagebox.showinfo("Éxito", "Usuario eliminado correctamente.")
                self.show_users_table()  # Actualizar la tabla
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo eliminar el usuario: {e}")

    def show_historial_table(self):
        # Si ya existe el frame de la tabla, destrúyelo para evitar duplicados
        if hasattr(self, "historial_table_frame") and self.historial_table_frame is not None:
            self.historial_table_frame.destroy()

        self.historial_table_frame = tk.Frame(self.content_frame, bg="white")
        self.historial_table_frame.pack(expand=True, fill="both", padx=0, pady=0)

        # --- FILTROS --- SIEMPRE SE CREAN NUEVOS ---
        filtro_frame = tk.Frame(self.historial_table_frame, bg="white")
        filtro_frame.grid(row=0, column=0, columnspan=9, sticky="ew", pady=(0, 10), padx=30)
        self.historial_table_frame.grid_rowconfigure(0, weight=0)
        self.historial_table_frame.grid_columnconfigure(0, weight=1)

        # CAMBIO: Agregar variables para los filtros (incluyendo descripción)
        self.usuario_id_var = tk.StringVar()
        self.muestra_var = tk.StringVar()  # CAMBIO: Renombrado de nombre_var a muestra_var
        self.descripcion_var = tk.StringVar()  # NUEVO: Variable para filtro de descripción
        self.fecha_var = tk.StringVar()

        # Primera fila de filtros
        filtro_row1 = tk.Frame(filtro_frame, bg="white")
        filtro_row1.pack(fill="x", pady=(0, 5))

        tk.Label(filtro_row1, text="Usuario ID:", bg="white", font=("Segoe UI", 10)).pack(side="left", padx=(0, 5))
        usuario_id_entry = tk.Entry(filtro_row1, textvariable=self.usuario_id_var, width=8, font=("Segoe UI", 10))
        usuario_id_entry.pack(side="left", padx=(0, 10))

        # CAMBIO: Cambiar "Nombre" por "# de muestra"
        tk.Label(filtro_row1, text="# de muestra:", bg="white", font=("Segoe UI", 10)).pack(side="left", padx=(0, 5))
        muestra_entry = tk.Entry(filtro_row1, textvariable=self.muestra_var, width=15, font=("Segoe UI", 10))
        muestra_entry.pack(side="left", padx=(0, 10))

        tk.Label(filtro_row1, text="Fecha:", bg="white", font=("Segoe UI", 10)).pack(side="left", padx=(0, 5))
        self.fecha_entry = DateEntry(filtro_row1, textvariable=self.fecha_var, width=12, date_pattern="yyyy-mm-dd", background="#0B5394", foreground="white", font=("Segoe UI", 10))
        self.fecha_entry.pack(side="left", padx=(0, 10))

        # Segunda fila de filtros
        filtro_row2 = tk.Frame(filtro_frame, bg="white")
        filtro_row2.pack(fill="x", pady=(0, 5))

        # NUEVO: Filtro por descripción
        tk.Label(filtro_row2, text="Descripción:", bg="white", font=("Segoe UI", 10)).pack(side="left", padx=(0, 5))
        descripcion_entry = tk.Entry(filtro_row2, textvariable=self.descripcion_var, width=30, font=("Segoe UI", 10))
        descripcion_entry.pack(side="left", padx=(0, 10))

        # Tercera fila - Botones
        filtro_row3 = tk.Frame(filtro_frame, bg="white")
        filtro_row3.pack(fill="x")

        def aplicar_filtro():
            self._actualizar_tabla_historial_filtrada()

        def limpiar_filtro():
            self.usuario_id_var.set("")
            self.muestra_var.set("")  # CAMBIO: Actualizado nombre de variable
            self.descripcion_var.set("")  # NUEVO: Limpiar filtro de descripción
            self.fecha_var.set("")
            self._actualizar_tabla_historial_filtrada()

        tk.Button(filtro_row3, text="Filtrar", command=aplicar_filtro, bg="#0B5394", fg="white", font=("Segoe UI", 10, "bold"), relief="flat", padx=12, pady=2, cursor="hand2").pack(side="left", padx=10)
        tk.Button(filtro_row3, text="Limpiar", command=limpiar_filtro, bg="#888", fg="white", font=("Segoe UI", 10), relief="flat", padx=10, pady=2, cursor="hand2").pack(side="left", padx=5)

        # --- Tabla con Scrollbar ---
        if hasattr(self, "table_container") and self.table_container is not None:
            self.table_container.destroy()

        self.table_container = tk.Frame(self.historial_table_frame, bg="white", highlightbackground="#b3c6e7", highlightthickness=1)
        self.table_container.grid(row=1, column=0, sticky="nsew", padx=0, pady=(0, 0))
        self.historial_table_frame.grid_rowconfigure(1, weight=1)
        self.historial_table_frame.grid_columnconfigure(0, weight=1)

        canvas = tk.Canvas(self.table_container, bg="white", highlightthickness=0)
        scrollbar = tk.Scrollbar(self.table_container, orient="vertical", command=canvas.yview)
        self.tabla_historial_frame = tk.Frame(canvas, bg="white")

        self.tabla_historial_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=self.tabla_historial_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # ARREGLAR: Enlazar scroll del mouse correctamente
        bind_mousewheel(canvas, canvas)

        self._actualizar_tabla_historial_filtrada()

    def _actualizar_tabla_historial_filtrada(self):
        # Borra la tabla anterior si existe
        for widget in self.tabla_historial_frame.winfo_children():
            widget.destroy()

        usuario_id = self.usuario_id_var.get()
        muestra = self.muestra_var.get()  # CAMBIO: Renombrado de nombre a muestra
        descripcion = self.descripcion_var.get()  # NUEVO: Obtener filtro de descripción
        fecha = self.fecha_var.get()

        historial = obtener_historial()
        filtrado = []
        for item in historial:
            Id, Nombre, Descripcion, Fecha, Hora, UsuarioId, Archivo = item
            if usuario_id and str(UsuarioId) != usuario_id:
                continue
            # CAMBIO: Buscar en el campo Nombre (que ahora representa # de muestra)
            if muestra and muestra.lower() not in str(Nombre).lower():
                continue
            # NUEVO: Filtro por descripción con búsqueda por palabras
            if descripcion:
                descripcion_texto = str(Descripcion).lower()
                filtro_texto = descripcion.lower().strip()
                
                # Si el filtro contiene espacios, buscar por palabras individuales
                if ' ' in filtro_texto:
                    palabras_filtro = filtro_texto.split()
                    # Buscar si CUALQUIER palabra del filtro está en la descripción
                    encontrado = any(palabra in descripcion_texto for palabra in palabras_filtro)
                else:
                    # Si es una sola palabra, buscar coincidencia directa
                    encontrado = filtro_texto in descripcion_texto
                
                if not encontrado:
                    continue
                    
            if fecha and str(Fecha) != fecha:
                continue
            filtrado.append(item)
        self._pintar_historial_tabla(filtrado, start_row=0, parent_frame=self.tabla_historial_frame)

    def _pintar_historial_tabla(self, historial, start_row=0, parent_frame=None):
        if parent_frame is None:
            parent_frame = self.tabla_historial_frame

        # CAMBIO: Actualizar encabezado de "Nombre" a "# de muestra"
        headers = ["ID", "# de muestra", "Descripción", "Fecha", "Hora", "UsuarioId", "Archivo", "Descargar", "Eliminar"]
        header_bg = "#0B5394"
        header_fg = "white"
        for col, h in enumerate(headers):
            tk.Label(
                parent_frame, text=h, font=("Segoe UI", 11, "bold"),
                bg=header_bg, fg=header_fg, padx=10, pady=10, borderwidth=0, relief="flat"
            ).grid(row=start_row, column=col, sticky="nsew", padx=1, pady=1)

        # Cargar imagen de descarga
        download_path = os.path.join(os.path.dirname(__file__), "..", "img", "download.png")
        download_path = os.path.abspath(download_path)
        download_img = Image.open(download_path).resize((20, 20), Image.LANCZOS)
        download_icon = ImageTk.PhotoImage(download_img)
        self.download_icon = download_icon  # Mantener referencia

        # Cargar imagen de eliminar (basura)
        trash_path = os.path.join(os.path.dirname(__file__), "..", "img", "basura.png")
        trash_path = os.path.abspath(trash_path)
        trash_img = Image.open(trash_path).resize((20, 20), Image.LANCZOS)
        trash_icon = ImageTk.PhotoImage(trash_img)
        self.trash_icon = trash_icon  # Mantener referencia

        row_bg1 = "#f4f8fb"
        row_bg2 = "#e6f0fa"
        for row, item in enumerate(historial, start=start_row+1):
            Id, Nombre, Descripcion, Fecha, Hora, UsuarioId, Archivo = item
            bg = row_bg1 if row % 2 == 1 else row_bg2

            tk.Label(parent_frame, text=Id, bg=bg, font=("Segoe UI", 10), borderwidth=0, relief="flat", padx=8, pady=6).grid(row=row, column=0, sticky="nsew", padx=1, pady=1)
            # El campo "Nombre" de la BD ahora se muestra como "# de muestra" en la interfaz
            tk.Label(parent_frame, text=Nombre, bg=bg, font=("Segoe UI", 10), borderwidth=0, relief="flat", padx=8, pady=6).grid(row=row, column=1, sticky="nsew", padx=1, pady=1)
            tk.Label(parent_frame, text=Descripcion, bg=bg, font=("Segoe UI", 10), borderwidth=0, relief="flat", padx=8, pady=6, wraplength=220, justify="left").grid(row=row, column=2, sticky="nsew", padx=1, pady=1)
            tk.Label(parent_frame, text=str(Fecha), bg=bg, font=("Segoe UI", 10), borderwidth=0, relief="flat", padx=8, pady=6).grid(row=row, column=3, sticky="nsew", padx=1, pady=1)
            tk.Label(parent_frame, text=str(Hora), bg=bg, font=("Segoe UI", 10), borderwidth=0, relief="flat", padx=8, pady=6).grid(row=row, column=4, sticky="nsew", padx=1, pady=1)
            tk.Label(parent_frame, text=UsuarioId, bg=bg, font=("Segoe UI", 10), borderwidth=0, relief="flat", padx=8, pady=6).grid(row=row, column=5, sticky="nsew", padx=1, pady=1)
            archivo_text = "Sí" if Archivo else "No"
            tk.Label(parent_frame, text=archivo_text, bg=bg, font=("Segoe UI", 10), borderwidth=0, relief="flat", padx=8, pady=6).grid(row=row, column=6, sticky="nsew", padx=1, pady=1)

            # Botón para descargar archivo
            download_btn = tk.Button(
                parent_frame,
                image=self.download_icon,
                bg=bg,
                bd=0,
                activebackground="#b3d1f7",
                cursor="hand2",
                command=lambda archivo=Archivo, nombre=Nombre: self.descargar_archivo_historial(archivo, nombre)
            )
            download_btn.grid(row=row, column=7, padx=2, pady=1, sticky="nsew")

            # Botón para eliminar registro
            delete_btn = tk.Button(
                parent_frame,
                image=self.trash_icon,
                bg=bg,
                bd=0,
                activebackground="#f7bdbd",
                cursor="hand2",
                command=lambda id_hist=Id: self.delete_historial_record(id_hist)
            )
            delete_btn.grid(row=row, column=8, padx=2, pady=1, sticky="nsew")

        # Hacer columnas expandibles
        for col in range(len(headers)):
            parent_frame.grid_columnconfigure(col, weight=1)

    def descargar_archivo_historial(self, archivo_bin, nombre):
        if not archivo_bin:
            messagebox.showerror("Error", "No hay archivo para descargar.")
            return
        # Sugerir extensión .xlsx si el nombre lo requiere
        if not nombre.lower().endswith(".xlsx"):
            nombre = nombre + ".xlsx"
        file_path = filedialog.asksaveasfilename(
            title="Guardar archivo",
            initialfile=nombre,
            defaultextension=".xlsx",
            filetypes=[("Archivos Excel", "*.xlsx"), ("Todos los archivos", "*.*")]
        )
        if file_path:
            try:
                with open(file_path, "wb") as f:
                    f.write(archivo_bin)
                messagebox.showinfo("Éxito", f"Archivo guardado en:\n{file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo guardar el archivo: {e}")

    def show_exportar_excel(self):
        # CAMBIO: Crear frame principal simple
        main_frame = tk.Frame(self.content_frame, bg="white")
        main_frame.pack(fill="both", expand=True)
        
        # NUEVO: Canvas y Scrollbar para scroll
        canvas = tk.Canvas(main_frame, bg="white")
        scrollbar = tk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        container = tk.Frame(canvas, bg="white")

        container.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=container, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Imagen decorativa de Bruni centrada arriba
        bruni_path = os.path.join(os.path.dirname(__file__), "..", "img", "bruni.png")
        bruni_path = os.path.abspath(bruni_path)
        bruni_img = Image.open(bruni_path).resize((120, 120), Image.LANCZOS)
        mask = Image.new('L', (120, 120), 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0, 120, 120), fill=255)
        bruni_img.putalpha(mask)
        bruni_photo = ImageTk.PhotoImage(bruni_img)
        bruni_label = tk.Label(container, image=bruni_photo, bg="white")
        bruni_label.image = bruni_photo  # Mantener referencia
        bruni_label.pack(pady=(30, 20))

        # Título
        title = tk.Label(
            container,
            text="Exportar / Importar Base de Datos",
            font=("Segoe UI", 20, "bold"),
            fg="#0B5394",
            bg="white"
        )
        title.pack(pady=(0, 15))

        # NUEVO: Sección de Exportación con filtros
        export_frame = tk.LabelFrame(
            container,
            text="Exportar Datos",
            font=("Segoe UI", 14, "bold"),
            fg="#0B5394",
            bg="white",
            padx=20,
            pady=15
        )
        export_frame.pack(pady=(0, 20), padx=40, fill="x")

        # Descripción de exportación
        export_info = tk.Label(
            export_frame,
            text="Selecciona los filtros para exportar registros específicos:",
            font=("Segoe UI", 11),
            fg="#333333",
            bg="white"
        )
        export_info.pack(pady=(0, 15))

        # NUEVO: Filtros de exportación
        filters_frame = tk.Frame(export_frame, bg="white")
        filters_frame.pack(fill="x", pady=(0, 15))

        # Variables para los filtros
        self.export_usuario_id_var = tk.StringVar()
        self.export_muestra_var = tk.StringVar()
        self.export_descripcion_var = tk.StringVar()
        self.export_fecha_desde_var = tk.StringVar()
        self.export_fecha_hasta_var = tk.StringVar()
        self.export_incluir_archivos_var = tk.BooleanVar(value=True)

        # Primera fila de filtros
        filter_row1 = tk.Frame(filters_frame, bg="white")
        filter_row1.pack(fill="x", pady=(0, 8))

        tk.Label(filter_row1, text="Usuario ID:", bg="white", font=("Segoe UI", 10)).grid(row=0, column=0, sticky="w", padx=(0, 5))
        tk.Entry(filter_row1, textvariable=self.export_usuario_id_var, width=8, font=("Segoe UI", 10)).grid(row=0, column=1, padx=(0, 15), sticky="w")

        tk.Label(filter_row1, text="# de muestra:", bg="white", font=("Segoe UI", 10)).grid(row=0, column=2, sticky="w", padx=(0, 5))
        tk.Entry(filter_row1, textvariable=self.export_muestra_var, width=15, font=("Segoe UI", 10)).grid(row=0, column=3, padx=(0, 15), sticky="w")

        # Segunda fila de filtros
        filter_row2 = tk.Frame(filters_frame, bg="white")
        filter_row2.pack(fill="x", pady=(0, 8))

        tk.Label(filter_row2, text="Descripción:", bg="white", font=("Segoe UI", 10)).grid(row=0, column=0, sticky="w", padx=(0, 5))
        tk.Entry(filter_row2, textvariable=self.export_descripcion_var, width=40, font=("Segoe UI", 10)).grid(row=0, column=1, columnspan=3, padx=(0, 15), sticky="ew")

        # Tercera fila de filtros - Fechas
        filter_row3 = tk.Frame(filters_frame, bg="white")
        filter_row3.pack(fill="x", pady=(0, 8))

        tk.Label(filter_row3, text="Fecha desde:", bg="white", font=("Segoe UI", 10)).grid(row=0, column=0, sticky="w", padx=(0, 5))
        self.export_fecha_desde_entry = DateEntry(filter_row3, textvariable=self.export_fecha_desde_var, width=12, date_pattern="yyyy-mm-dd", background="#0B5394", foreground="white", font=("Segoe UI", 10))
        self.export_fecha_desde_entry.grid(row=0, column=1, padx=(0, 15), sticky="w")

        tk.Label(filter_row3, text="Fecha hasta:", bg="white", font=("Segoe UI", 10)).grid(row=0, column=2, sticky="w", padx=(0, 5))
        self.export_fecha_hasta_entry = DateEntry(filter_row3, textvariable=self.export_fecha_hasta_var, width=12, date_pattern="yyyy-mm-dd", background="#0B5394", foreground="white", font=("Segoe UI", 10))
        self.export_fecha_hasta_entry.grid(row=0, column=3, padx=(0, 15), sticky="w")

        # Cuarta fila - Opciones adicionales
        filter_row4 = tk.Frame(filters_frame, bg="white")
        filter_row4.pack(fill="x", pady=(0, 8))

        tk.Checkbutton(
            filter_row4,
            text="Incluir archivos adjuntos",
            variable=self.export_incluir_archivos_var,
            bg="white",
            font=("Segoe UI", 10),
            activebackground="white"
        ).pack(side="left")

        # Quinta fila - Botones de filtros
        filter_row5 = tk.Frame(filters_frame, bg="white")
        filter_row5.pack(fill="x", pady=(8, 0))

        def limpiar_filtros_export():
            self.export_usuario_id_var.set("")
            self.export_muestra_var.set("")
            self.export_descripcion_var.set("")
            self.export_fecha_desde_var.set("")
            self.export_fecha_hasta_var.set("")
            self.export_incluir_archivos_var.set(True)

        tk.Button(
            filter_row5,
            text="Limpiar filtros",
            command=limpiar_filtros_export,
            bg="#888",
            fg="white",
            font=("Segoe UI", 10),
            relief="flat",
            padx=15,
            pady=5,
            cursor="hand2"
        ).pack(side="left", padx=(0, 10))

        # Configurar expansión de columnas
        filter_row2.grid_columnconfigure(1, weight=1)

        # Cargar imagen del botón exportar
        upload_path = os.path.join(os.path.dirname(__file__), "..", "img", "upload.png")
        upload_path = os.path.abspath(upload_path)
        upload_img = Image.open(upload_path).resize((25, 25), Image.LANCZOS)
        upload_icon = ImageTk.PhotoImage(upload_img)
        self.upload_icon = upload_icon  # Mantener referencia

        # Botón de exportar
        export_btn = tk.Button(
            export_frame,
            text=" Exportar con filtros",
            image=self.upload_icon,
            compound="left",
            font=("Segoe UI", 12, "bold"),
            bg="#0B5394",
            fg="white",
            activebackground="#073763",
            activeforeground="white",
            relief="flat",
            padx=20,
            pady=10,
            cursor="hand2",
            command=self.exportar_excel_filtrado
        )
        export_btn.pack(pady=(10, 0))

        # Separador
        separator = tk.Frame(container, bg="#0B5394", height=2)
        separator.pack(fill="x", padx=40, pady=20)

        # SECCIÓN DE IMPORTACIÓN (sin cambios)
        import_frame = tk.LabelFrame(
            container,
            text="Importar Datos",
            font=("Segoe UI", 14, "bold"),
            fg="#0B5394",
            bg="white",
            padx=20,
            pady=15
        )
        import_frame.pack(pady=(0, 30), padx=40, fill="x")

        import_info = tk.Label(
            import_frame,
            text="Importa un archivo ZIP previamente exportado para restaurar registros:",
            font=("Segoe UI", 11),
            fg="#333333",
            bg="white"
        )
        import_info.pack(pady=(0, 15))

        # Cargar imagen del botón importar
        download_path = os.path.join(os.path.dirname(__file__), "..", "img", "download.png")
        download_path = os.path.abspath(download_path)
        download_img = Image.open(download_path).resize((25, 25), Image.LANCZOS)
        download_icon = ImageTk.PhotoImage(download_img)
        self.download_icon = download_icon  # Mantener referencia

        import_btn = tk.Button(
            import_frame,
            text=" Importar desde ZIP",
            image=self.download_icon,
            compound="left",
            font=("Segoe UI", 12, "bold"),
            bg="#0B5394",
            fg="white",
            activebackground="#073763",
            activeforeground="white",
            relief="flat",
            padx=20,
            pady=10,
            cursor="hand2",
            command=self.importar_excel
        )
        import_btn.pack()

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
        # Enlazar scroll del mouse
        bind_mousewheel(canvas, canvas)

    def exportar_excel_filtrado(self):
        try:
            # Obtener todos los registros
            historial = obtener_historial()
            
            if not historial:
                messagebox.showinfo("Exportar", "No hay registros para exportar.")
                return

            # Aplicar filtros
            filtrado = []
            for item in historial:
                Id, Nombre, Descripcion, Fecha, Hora, UsuarioId, Archivo = item
                
                # Filtro por Usuario ID
                if self.export_usuario_id_var.get() and str(UsuarioId) != self.export_usuario_id_var.get():
                    continue
                    
                # Filtro por # de muestra
                if self.export_muestra_var.get() and self.export_muestra_var.get().lower() not in str(Nombre).lower():
                    continue
                    
                # Filtro por descripción (con búsqueda por palabras)
                if self.export_descripcion_var.get():
                    descripcion_texto = str(Descripcion).lower()
                    filtro_texto = self.export_descripcion_var.get().lower().strip()
                    
                    if ' ' in filtro_texto:
                        palabras_filtro = filtro_texto.split()
                        encontrado = any(palabra in descripcion_texto for palabra in palabras_filtro)
                    else:
                        encontrado = filtro_texto in descripcion_texto
                    
                    if not encontrado:
                        continue
                
                # Filtro por fecha desde
                if self.export_fecha_desde_var.get():
                    fecha_desde = self.export_fecha_desde_var.get()
                    if str(Fecha) < fecha_desde:
                        continue
                        
                # Filtro por fecha hasta
                if self.export_fecha_hasta_var.get():
                    fecha_hasta = self.export_fecha_hasta_var.get()
                    if str(Fecha) > fecha_hasta:
                        continue
            
                filtrado.append(item)

            if not filtrado:
                messagebox.showinfo("Exportar", "No se encontraron registros que coincidan con los filtros aplicados.")
                return

            # Preparar datos para exportación
            data = []
            archivos = []
            incluir_archivos = self.export_incluir_archivos_var.get()
            
            for row in filtrado:
                Id, Nombre, Descripcion, Fecha, Hora, UsuarioId, Archivo = row
                
                if incluir_archivos and Archivo:
                    archivo_nombre = f"{Id}_{Nombre}.bin"
                    archivos.append((archivo_nombre, Archivo))
                else:
                    archivo_nombre = ""
                    
                data.append([Id, Nombre, Descripcion, Fecha, Hora, UsuarioId, archivo_nombre])

            df = pd.DataFrame(data, columns=["Id", "Nombre", "Descripcion", "Fecha", "Hora", "UsuarioId", "ArchivoNombre"])

            # Generar nombre de archivo con fecha y hora actual
            now = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filtros_aplicados = []
            if self.export_usuario_id_var.get():
                filtros_aplicados.append(f"user{self.export_usuario_id_var.get()}")
            if self.export_fecha_desde_var.get() or self.export_fecha_hasta_var.get():
                filtros_aplicados.append("filtered")
            
            sufijo = "_" + "_".join(filtros_aplicados) if filtros_aplicados else ""
            default_filename = f"export_{now}{sufijo}.zip"

            file_path = filedialog.asksaveasfilename(
                defaultextension=".zip",
                filetypes=[("Archivo ZIP", "*.zip")],
                title="Guardar como",
                initialfile=default_filename
            )
            if not file_path:
                return

            with zipfile.ZipFile(file_path, "w") as zf:
                # Guardar el Excel dentro del ZIP
                excel_buffer = io.BytesIO()
                df.to_excel(excel_buffer, index=False)
                zf.writestr("historial.xlsx", excel_buffer.getvalue())
                
                # Guardar archivos binarios solo si se seleccionó incluirlos
                if incluir_archivos:
                    for archivo_nombre, archivo_bin in archivos:
                        zf.writestr(archivo_nombre, archivo_bin)

            # Mensaje de éxito con estadísticas
            mensaje = f"Archivo ZIP exportado correctamente:\n{file_path}\n\n"
            mensaje += f"Registros exportados: {len(filtrado)}\n"
            if incluir_archivos:
                mensaje += f"Archivos adjuntos incluidos: {len(archivos)}"
            else:
                mensaje += "Sin archivos adjuntos"
                
            messagebox.showinfo("Exportar", mensaje)
            
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo exportar: {e}")

    def exportar_excel(self):
        """Método para exportar todos los datos sin filtros (método original)"""
        try:
            historial = obtener_historial()
            
            if not historial:
                messagebox.showinfo("Exportar", "No hay registros para exportar.")
                return

            # Preparar datos
            data = []
            archivos = []
            
            for row in historial:
                Id, Nombre, Descripcion, Fecha, Hora, UsuarioId, Archivo = row
                
                if Archivo:
                    archivo_nombre = f"{Id}_{Nombre}.bin"
                    archivos.append((archivo_nombre, Archivo))
                else:
                    archivo_nombre = ""
                    
                data.append([Id, Nombre, Descripcion, Fecha, Hora, UsuarioId, archivo_nombre])

            df = pd.DataFrame(data, columns=["Id", "Nombre", "Descripcion", "Fecha", "Hora", "UsuarioId", "ArchivoNombre"])

            # Generar nombre de archivo
            now = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            default_filename = f"export_completo_{now}.zip"

            file_path = filedialog.asksaveasfilename(
                defaultextension=".zip",
                filetypes=[("Archivo ZIP", "*.zip")],
                title="Guardar como",
                initialfile=default_filename
            )
            if not file_path:
                return

            with zipfile.ZipFile(file_path, "w") as zf:
                # Guardar el Excel
                excel_buffer = io.BytesIO()
                df.to_excel(excel_buffer, index=False)
                zf.writestr("historial.xlsx", excel_buffer.getvalue())
                
                # Guardar archivos binarios
                for archivo_nombre, archivo_bin in archivos:
                    zf.writestr(archivo_nombre, archivo_bin)

            messagebox.showinfo("Exportar", f"Exportación completa exitosa:\n{file_path}\n\nRegistros: {len(historial)}\nArchivos: {len(archivos)}")
            
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo exportar: {e}")

    def importar_excel(self):
        """Método para importar datos desde ZIP"""
        try:
            file_path = filedialog.askopenfilename(
                title="Seleccionar archivo ZIP",
                filetypes=[("Archivo ZIP", "*.zip")]
            )
            if not file_path:
                return

            if not messagebox.askyesno("Importar", "¿Estás seguro de que deseas importar estos datos?\nEsto puede sobrescribir registros existentes."):
                return

            with zipfile.ZipFile(file_path, "r") as zf:
                # Leer el Excel
                excel_data = zf.read("historial.xlsx")
                df = pd.read_excel(io.BytesIO(excel_data))
                
                registros_importados = 0
                archivos_importados = 0
                
                for _, row in df.iterrows():
                    try:
                        # Leer archivo binario si existe
                        archivo_bin = None
                        if row["ArchivoNombre"] and row["ArchivoNombre"] != "":
                            try:
                                archivo_bin = zf.read(row["ArchivoNombre"])
                                archivos_importados += 1
                            except KeyError:
                                pass  # El archivo no existe en el ZIP
                        
                        # Importar registro
                        importar_registro(
                            row["Nombre"], 
                            row["Descripcion"], 
                            row["Fecha"], 
                            row["Hora"], 
                            row["UsuarioId"], 
                            archivo_bin
                        )
                        registros_importados += 1
                        
                    except Exception as e:
                        print(f"Error importando registro {row['Id']}: {e}")

            messagebox.showinfo("Importar", f"Importación exitosa:\n\nRegistros importados: {registros_importados}\nArchivos importados: {archivos_importados}")
            
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo importar: {e}")

    def add_user_popup(self):
        popup = tk.Toplevel(self)
        popup.title("Agregar nuevo usuario")
        popup.geometry("350x350")
        popup.configure(bg="white")
        popup.resizable(False, False)
        popup.grab_set()

        tk.Label(popup, text="Usuario:", font=("Segoe UI", 11), bg="white").pack(pady=(20, 5))
        username_entry = tk.Entry(popup, font=("Segoe UI", 11), width=25)
        username_entry.pack()

        tk.Label(popup, text="Email:", font=("Segoe UI", 11), bg="white").pack(pady=(10, 5))
        email_entry = tk.Entry(popup, font=("Segoe UI", 11), width=25)
        email_entry.pack()

        tk.Label(popup, text="Contraseña:", font=("Segoe UI", 11), bg="white").pack(pady=(10, 5))
        password_entry = tk.Entry(popup, font=("Segoe UI", 11), width=25, show="*")
        password_entry.pack()

        tk.Label(popup, text="Rol:", font=("Segoe UI", 11), bg="white").pack(pady=(10, 5))
        rol_var = tk.StringVar(value="usuario")
        rol_frame = tk.Frame(popup, bg="white")
        rol_frame.pack()
        tk.Radiobutton(rol_frame, text="usuario", variable=rol_var, value="usuario", font=("Segoe UI", 10), bg="white").pack(side="left", padx=10)
        tk.Radiobutton(rol_frame, text="admin", variable=rol_var, value="admin", font=("Segoe UI", 10), bg="white").pack(side="left", padx=10)

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
                self.show_users_table()  # Actualizar la tabla
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo crear el usuario: {e}", parent=popup)

        tk.Button(
            popup,
            text="Crear usuario",
            font=("Segoe UI", 11, "bold"),
            bg="#0B5394",
            fg="white",
            activebackground="#073763",
            activeforeground="white",
            relief="flat",
            command=create_user
        ).pack(fill="x", padx=40, pady=20, ipady=8)

    def delete_historial_record(self, record_id):
        if messagebox.askyesno("Eliminar registro", "¿Estás seguro de que deseas eliminar este registro?"):
            try:
                eliminar_registro_historial(record_id)
                messagebox.showinfo("Éxito", "Registro eliminado correctamente.")
                self._actualizar_tabla_historial_filtrada()  # Actualizar la tabla
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo eliminar el registro: {e}")
