import tkinter as tk
from tkinter import messagebox, filedialog
from PIL import Image, ImageDraw, ImageTk
import os
import pandas as pd
import zipfile
import io
import datetime
from tkcalendar import DateEntry  # Agrega esto al inicio del archivo

from core.auth import obtener_usuarios, actualizar_usuario, eliminar_usuario, obtener_historial, agregar_historial, crear_usuario  # Agrega obtener_historial y agregar_historial a tu backend

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
            # Ventana informativa de bienvenida
            frame = tk.Frame(self.content_frame, bg="white")
            frame.pack(expand=True, fill="both")

            # Imagen de Bruni centrada (más grande)
            img_path = os.path.join(os.path.dirname(__file__), "..", "img", "bruni.png")
            img_path = os.path.abspath(img_path)
            bruni_img = Image.open(img_path).resize((200, 200), Image.LANCZOS)
            mask = Image.new('L', (200, 200), 0)
            draw = ImageDraw.Draw(mask)
            draw.ellipse((0, 0, 200, 200), fill=255)
            bruni_img.putalpha(mask)
            bruni_photo = ImageTk.PhotoImage(bruni_img)
            img_label = tk.Label(frame, image=bruni_photo, bg="white")
            img_label.image = bruni_photo  # Referencia para evitar garbage collection
            img_label.pack(pady=(30, 20))

            # Texto de bienvenida
            welcome = tk.Label(
                frame,
                text=f"¡Bienvenido, {self.username if self.username else 'Usuario'}!",
                font=("Segoe UI", 22, "bold"),
                fg="#0B5394",
                bg="white"
            )
            welcome.pack(pady=(0, 10))

            # NUEVO TEXTO INFORMATIVO
            info = tk.Label(
                frame,
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

        self.users_table_frame = tk.Frame(self.content_frame, bg="white")
        self.users_table_frame.pack(expand=True, fill="both", padx=30, pady=20)

        # --- Botón agregar usuario (+) ---
        plus_path = os.path.join(os.path.dirname(__file__), "..", "img", "+.png")
        plus_path = os.path.abspath(plus_path)
        plus_img = Image.open(plus_path).resize((24, 24), Image.LANCZOS)
        plus_icon = ImageTk.PhotoImage(plus_img)
        self.plus_icon = plus_icon  # Mantener referencia

        add_btn = tk.Button(
            self.users_table_frame,
            image=self.plus_icon,
            bg="white",
            bd=0,
            activebackground="#b3d1f7",
            cursor="hand2",
            command=self.add_user_popup
        )
        add_btn.grid(row=0, column=0, sticky="w", padx=(0, 8), pady=(0, 8))

        # Encabezados con diseño azul
        headers = ["ID", "Usuario", "Email", "Rol", "Editar", "Eliminar"]
        header_bg = "#0B5394"
        header_fg = "white"
        for col, h in enumerate(headers):
            tk.Label(
                self.users_table_frame, text=h, font=("Segoe UI", 11, "bold"),
                bg=header_bg, fg=header_fg, padx=10, pady=8, borderwidth=0, relief="flat"
            ).grid(row=1, column=col, sticky="nsew", padx=(0 if col == 0 else 2, 2), pady=(0, 2))

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
        for row, user in enumerate(usuarios, start=2):
            user_id, username, email, rol = user
            bg = row_bg1 if row % 2 == 1 else row_bg2

            tk.Label(self.users_table_frame, text=user_id, bg=bg, font=("Segoe UI", 10), borderwidth=0, relief="flat", padx=8, pady=4).grid(row=row, column=0, sticky="nsew", padx=2, pady=1)
            tk.Label(self.users_table_frame, text=username, bg=bg, font=("Segoe UI", 10), borderwidth=0, relief="flat", padx=8, pady=4).grid(row=row, column=1, sticky="nsew", padx=2, pady=1)
            tk.Label(self.users_table_frame, text=email, bg=bg, font=("Segoe UI", 10), borderwidth=0, relief="flat", padx=8, pady=4).grid(row=row, column=2, sticky="nsew", padx=2, pady=1)
            tk.Label(self.users_table_frame, text=rol, bg=bg, font=("Segoe UI", 10), borderwidth=0, relief="flat", padx=8, pady=4).grid(row=row, column=3, sticky="nsew", padx=2, pady=1)

            edit_btn = tk.Button(
                self.users_table_frame,
                image=self.lapiz_icon,
                bg=bg,
                bd=0,
                activebackground="#b3d1f7",
                cursor="hand2",
                command=lambda u=user: self.edit_user_popup(u)
            )
            edit_btn.grid(row=row, column=4, padx=4, pady=1)

            delete_btn = tk.Button(
                self.users_table_frame,
                image=self.basura_icon,
                bg=bg,
                bd=0,
                activebackground="#f7bdbd",
                cursor="hand2",
                command=lambda uid=user_id: self.delete_user(uid)
            )
            delete_btn.grid(row=row, column=5, padx=4, pady=1)

        # Hacer columnas expandibles
        for col in range(len(headers)):
            self.users_table_frame.grid_columnconfigure(col, weight=1)

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
            nuevo_username = username_entry.get()
            nuevo_email = email_entry.get()
            nuevo_rol = rol_var.get()
            nueva_contra = password_entry.get()
            try:
                # Si la contraseña está vacía, no la cambies
                if nueva_contra.strip():
                    actualizar_usuario(user_id, nuevo_username, nuevo_email, nuevo_rol, nueva_contra)
                else:
                    actualizar_usuario(user_id, nuevo_username, nuevo_email, nuevo_rol, None)
                messagebox.showinfo("Éxito", "Usuario actualizado correctamente.", parent=popup)
                popup.destroy()
                self.update_user_row(user_id, nuevo_username, nuevo_email, nuevo_rol)
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
        if messagebox.askyesno("Eliminar usuario", "¿Estás seguro de que deseas eliminar este usuario? Se eliminará también su historial."):
            try:
                from core.auth import eliminar_historial_por_usuario  # Debes crear esta función en tu backend
                eliminar_historial_por_usuario(user_id)  # Elimina historial primero
                eliminar_usuario(user_id)                # Luego elimina el usuario
                messagebox.showinfo("Éxito", "Usuario eliminado correctamente.")
                self.show_users_table()
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

        self.usuario_id_var = tk.StringVar()
        self.nombre_var = tk.StringVar()
        self.fecha_var = tk.StringVar()

        tk.Label(filtro_frame, text="Usuario ID:", bg="white", font=("Segoe UI", 10)).pack(side="left", padx=(0, 5))
        usuario_id_entry = tk.Entry(filtro_frame, textvariable=self.usuario_id_var, width=8, font=("Segoe UI", 10))
        usuario_id_entry.pack(side="left", padx=(0, 10))

        tk.Label(filtro_frame, text="Nombre:", bg="white", font=("Segoe UI", 10)).pack(side="left", padx=(0, 5))
        nombre_entry = tk.Entry(filtro_frame, textvariable=self.nombre_var, width=15, font=("Segoe UI", 10))
        nombre_entry.pack(side="left", padx=(0, 10))

        tk.Label(filtro_frame, text="Fecha:", bg="white", font=("Segoe UI", 10)).pack(side="left", padx=(0, 5))
        self.fecha_entry = DateEntry(filtro_frame, textvariable=self.fecha_var, width=12, date_pattern="yyyy-mm-dd", background="#0B5394", foreground="white", font=("Segoe UI", 10))
        self.fecha_entry.pack(side="left", padx=(0, 10))

        def aplicar_filtro():
            self._actualizar_tabla_historial_filtrada()

        def limpiar_filtro():
            self.usuario_id_var.set("")
            self.nombre_var.set("")
            self.fecha_var.set("")
            self._actualizar_tabla_historial_filtrada()

        tk.Button(filtro_frame, text="Filtrar", command=aplicar_filtro, bg="#0B5394", fg="white", font=("Segoe UI", 10, "bold"), relief="flat", padx=12, pady=2, cursor="hand2").pack(side="left", padx=10)
        tk.Button(filtro_frame, text="Limpiar", command=limpiar_filtro, bg="#888", fg="white", font=("Segoe UI", 10), relief="flat", padx=10, pady=2, cursor="hand2").pack(side="left", padx=5)

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

        self._actualizar_tabla_historial_filtrada()

    def _actualizar_tabla_historial_filtrada(self):
        # Borra la tabla anterior si existe
        for widget in self.tabla_historial_frame.winfo_children():
            widget.destroy()

        usuario_id = self.usuario_id_var.get()
        nombre = self.nombre_var.get()
        fecha = self.fecha_var.get()

        historial = obtener_historial()
        filtrado = []
        for item in historial:
            Id, Nombre, Descripcion, Fecha, Hora, UsuarioId, Archivo = item
            if usuario_id and str(UsuarioId) != usuario_id:
                continue
            if nombre and nombre.lower() not in str(Nombre).lower():
                continue
            if fecha and str(Fecha) != fecha:
                continue
            filtrado.append(item)
        self._pintar_historial_tabla(filtrado, start_row=0, parent_frame=self.tabla_historial_frame)

    def _pintar_historial_tabla(self, historial, start_row=0, parent_frame=None):
        if parent_frame is None:
            parent_frame = self.tabla_historial_frame

        headers = ["ID", "Nombre", "Descripción", "Fecha", "Hora", "UsuarioId", "Archivo", "Descargar", "Eliminar"]
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
        frame = tk.Frame(self.content_frame, bg="white")
        frame.pack(expand=True, fill="both", padx=30, pady=20)

        # Imagen decorativa de Bruni centrada arriba
        bruni_path = os.path.join(os.path.dirname(__file__), "..", "img", "bruni.png")
        bruni_path = os.path.abspath(bruni_path)
        bruni_img = Image.open(bruni_path).resize((120, 120), Image.LANCZOS)
        mask = Image.new('L', (120, 120), 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0, 120, 120), fill=255)
        bruni_img.putalpha(mask)
        bruni_photo = ImageTk.PhotoImage(bruni_img)
        bruni_label = tk.Label(frame, image=bruni_photo, bg="white")
        bruni_label.image = bruni_photo  # Mantener referencia
        bruni_label.pack(pady=(30, 10))

        # Título y texto informativo centrado y estilizado
        title = tk.Label(
            frame,
            text="Exportar / Importar Base de Datos",
            font=("Segoe UI", 20, "bold"),
            fg="#0B5394",
            bg="white"
        )
        title.pack(pady=(0, 10))

        info = tk.Label(
            frame,
            text=(
                "Puedes exportar todos los registros y archivos adjuntos de la base de datos\n"
                "en un solo archivo ZIP. También puedes importar un ZIP previamente exportado\n"
                "para restaurar o migrar los registros y archivos.\n\n"
                "Haz clic en 'Exportar' para descargar la base de datos completa.\n"
                "Haz clic en 'Importar' para cargar registros desde un archivo ZIP."
            ),
            font=("Segoe UI", 13),
            fg="#333333",
            bg="white",
            justify="center"
        )
        info.pack(pady=(0, 30))

        # Cargar imágenes de los botones
        upload_path = os.path.join(os.path.dirname(__file__), "..", "img", "upload.png")
        upload_path = os.path.abspath(upload_path)
        upload_img = Image.open(upload_path).resize((30, 30), Image.LANCZOS)
        upload_icon = ImageTk.PhotoImage(upload_img)
        self.upload_icon = upload_icon  # Mantener referencia

        download_path = os.path.join(os.path.dirname(__file__), "..", "img", "download.png")
        download_path = os.path.abspath(download_path)
        download_img = Image.open(download_path).resize((30, 30), Image.LANCZOS)
        download_icon = ImageTk.PhotoImage(download_img)
        self.download_icon = download_icon  # Mantener referencia

        # Botones centrados y estilizados
        btn_frame = tk.Frame(frame, bg="white")
        btn_frame.pack(pady=10)

        export_btn = tk.Button(
            btn_frame,
            text=" Exportar",
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
            command=self.exportar_excel
        )
        export_btn.pack(side="left", padx=30, pady=10)

        import_btn = tk.Button(
            btn_frame,
            text=" Importar",
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
        import_btn.pack(side="left", padx=30, pady=10)

    def exportar_excel(self):
        try:
            historial = obtener_historial()  # [(Id, Nombre, Descripcion, Fecha, Hora, UsuarioId, Archivo)]
            if not historial:
                messagebox.showinfo("Exportar", "No hay registros para exportar.")
                return

            # Prepara DataFrame y nombres de archivos
            data = []
            archivos = []
            for row in historial:
                Id, Nombre, Descripcion, Fecha, Hora, UsuarioId, Archivo = row
                archivo_nombre = f"{Id}_{Nombre}.bin" if Archivo else ""
                data.append([Id, Nombre, Descripcion, Fecha, Hora, UsuarioId, archivo_nombre])
                if Archivo:
                    archivos.append((archivo_nombre, Archivo))

            df = pd.DataFrame(data, columns=["Id", "Nombre", "Descripcion", "Fecha", "Hora", "UsuarioId", "ArchivoNombre"])

            # Generar nombre de archivo con fecha y hora actual
            now = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            default_filename = f"export_{now}.zip"

            file_path = filedialog.asksaveasfilename(
                defaultextension=".zip",
                filetypes=[("Archivo ZIP", "*.zip")],
                title="Guardar como",
                initialfile=default_filename
            )
            if not file_path:
                return

            with zipfile.ZipFile(file_path, "w") as zf:
                # Guarda el Excel dentro del ZIP
                excel_buffer = io.BytesIO()
                df.to_excel(excel_buffer, index=False)
                zf.writestr("historial.xlsx", excel_buffer.getvalue())
                # Guarda cada archivo binario
                for archivo_nombre, archivo_bin in archivos:
                    zf.writestr(archivo_nombre, archivo_bin)

            messagebox.showinfo("Exportar", f"Archivo ZIP exportado correctamente:\n{file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo exportar: {e}")

    def importar_excel(self):
        from core.auth import agregar_historial
        import zipfile
        import io

        try:
            file_path = filedialog.askopenfilename(
                filetypes=[("Archivo ZIP", "*.zip")],
                title="Seleccionar archivo ZIP"
            )
            if not file_path:
                return

            with zipfile.ZipFile(file_path, "r") as zf:
                # Lee el Excel
                with zf.open("historial.xlsx") as excel_file:
                    df = pd.read_excel(excel_file)
                # Lee los archivos binarios
                archivos_bin = {}
                for name in zf.namelist():
                    if name != "historial.xlsx":
                        archivos_bin[name] = zf.read(name)

            required_cols = {"Nombre", "Descripcion", "Fecha", "Hora", "UsuarioId", "ArchivoNombre"}
            if not required_cols.issubset(df.columns):
                messagebox.showerror("Error", "El archivo no tiene el formato correcto.")
                return

            count = 0
            for _, row in df.iterrows():
                nombre = row["Nombre"]
                descripcion = row["Descripcion"]
                fecha = str(row["Fecha"]).split(" ")[0]
                hora = str(row["Hora"])
                usuario_id = int(row["UsuarioId"])
                archivo_nombre = row["ArchivoNombre"]
                archivo_bin = archivos_bin.get(archivo_nombre, b"") if archivo_nombre else b""
                agregar_historial(nombre, descripcion, fecha, hora, usuario_id, archivo_bin)
                count += 1

            messagebox.showinfo("Importar", f"Se importaron {count} registros correctamente.")
            self.show_historial_table()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo importar: {e}")

    def delete_historial_record(self, id_hist):
        if messagebox.askyesno("Eliminar registro", "¿Estás seguro de que deseas eliminar este registro del historial?"):
            try:
                from core.auth import eliminar_historial  # Debes tener esta función en tu backend
                eliminar_historial(id_hist)
                messagebox.showinfo("Éxito", "Registro eliminado correctamente.")
                self.show_historial_table()
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo eliminar el registro: {e}")

    def add_user_popup(self):
        popup = tk.Toplevel(self)
        popup.title("Agregar nuevo usuario")
        popup.geometry("350x320")
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

        def save_new_user():
            username = username_entry.get().strip()
            email = email_entry.get().strip()
            password = password_entry.get().strip()
            rol = rol_var.get()
            if not username or not password:
                messagebox.showerror("Error", "El usuario y la contraseña son obligatorios.", parent=popup)
                return
            try:
                crear_usuario(username, password, email)
                # Si quieres permitir crear admins desde aquí, agrega un parámetro de rol a tu función crear_usuario
                if rol == "admin":
                    from core.auth import actualizar_usuario
                    # Busca el id del usuario recién creado
                    from core.auth import obtener_id_por_username
                    user_id = obtener_id_por_username(username)
                    if user_id:
                        actualizar_usuario(user_id, username, email, rol)
                messagebox.showinfo("Éxito", "Usuario creado correctamente.", parent=popup)
                popup.destroy()
                self.show_users_table()
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
            command=save_new_user
        ).pack(fill="x", padx=40, pady=20, ipady=8)
