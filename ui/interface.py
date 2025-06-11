import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageDraw, ImageTk
import os
from core.auth import agregar_historial  # Debes tener esta función en tu backend

class MainInterface(tk.Tk):
    def __init__(self, username=None, rol="usuario"):
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
        # Elimina la línea de transparencia:
        # self.menu_frame.attributes('-alpha', 0.93)
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

        sections = ["Inicio", "Cálculos", "Exportar Excel", "Historial"]
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

            info = tk.Label(
                frame,
                text=(
                    "Este sistema es parte del Laboratorio de Alimentos de la\n"
                    "Facultad de Ciencias Químicas - UANL.\n\n"
                    "Aquí podrás realizar cálculos, exportar reportes y consultar tu historial.\n"
                    "¡Gracias por formar parte de la comunidad científica de la FCQ-UANL!\n\n"
                    "Facultad de Ciencias Químicas\n"
                    "Universidad Autónoma de Nuevo León\n"
                    "www.fcq.uanl.mx\n"
                    "Av. Universidad S/N, Cd. Universitaria, San Nicolás de los Garza, N.L."
                ),
                font=("Segoe UI", 13),
                fg="#333333",
                bg="white",
                justify="center"
            )
            info.pack(pady=(0, 20))
        elif section_name == "Historial":
            self.show_user_historial_table()
        elif section_name == "Exportar Excel":
            self.show_exportar_excel()
        else:
            label = tk.Label(
                self.content_frame,
                text=f"Sección: {section_name}",
                font=("Segoe UI", 14),
                bg="white"
            )
            label.pack(pady=20)

    def show_exportar_excel(self):
        frame = tk.Frame(self.content_frame, bg="white")
        frame.pack(expand=True, fill="both", padx=30, pady=20)

        info = tk.Label(
            frame,
            text="Desde aquí puedes exportar o importar la base de datos a Excel.\n\n"
                 "Utiliza el botón '+' para agregar un nuevo registro al historial.",
            font=("Segoe UI", 13),
            fg="#0B5394",
            bg="white",
            justify="left"
        )
        info.pack(anchor="nw", pady=(10, 0), padx=10)

        # Botón "+" en la esquina inferior derecha
        plus_path = os.path.join(os.path.dirname(__file__), "..", "img", "+.png")
        plus_path = os.path.abspath(plus_path)
        plus_img = Image.open(plus_path).resize((40, 40), Image.LANCZOS)
        plus_icon = ImageTk.PhotoImage(plus_img)
        self.plus_icon = plus_icon  # Mantener referencia

        plus_btn = tk.Button(
            frame,
            image=self.plus_icon,
            bg="white",
            bd=0,
            activebackground="#e6f0fa",
            cursor="hand2",
            command=self.add_historial_popup
        )
        plus_btn.place(relx=1.0, rely=1.0, anchor="se", x=-10, y=-10)

    def add_historial_popup(self):
        popup = tk.Toplevel(self)
        popup.title("Agregar nuevo registro al historial")
        popup.geometry("400x500")
        popup.configure(bg="white")
        popup.resizable(False, False)
        popup.grab_set()

        tk.Label(popup, text="Nombre:", font=("Segoe UI", 11), bg="white").pack(pady=(20, 5))
        nombre_entry = tk.Entry(popup, font=("Segoe UI", 11), width=30)
        nombre_entry.pack()

        tk.Label(popup, text="Descripción:", font=("Segoe UI", 11), bg="white").pack(pady=(10, 5))
        descripcion_entry = tk.Text(popup, font=("Segoe UI", 11), width=30, height=4)
        descripcion_entry.pack()

        tk.Label(popup, text="Fecha (YYYY-MM-DD):", font=("Segoe UI", 11), bg="white").pack(pady=(10, 5))
        fecha_entry = tk.Entry(popup, font=("Segoe UI", 11), width=30)
        fecha_entry.pack()

        tk.Label(popup, text="Hora (HH:MM:SS):", font=("Segoe UI", 11), bg="white").pack(pady=(10, 5))
        hora_entry = tk.Entry(popup, font=("Segoe UI", 11), width=30)
        hora_entry.pack()

        tk.Label(popup, text="Archivo adjunto:", font=("Segoe UI", 11), bg="white").pack(pady=(10, 5))
        archivo_var = tk.StringVar()
        archivo_entry = tk.Entry(popup, font=("Segoe UI", 11), width=24, textvariable=archivo_var, state="readonly")
        archivo_entry.pack(padx=(20, 0))
        def seleccionar_archivo():
            archivo = filedialog.askopenfilename(title="Seleccionar archivo")
            if archivo:
                archivo_var.set(archivo)
        tk.Button(popup, text="Seleccionar", command=seleccionar_archivo, font=("Segoe UI", 10)).pack(pady=(0, 10), padx=10)

        def guardar():
            nombre = nombre_entry.get()
            descripcion = descripcion_entry.get("1.0", "end").strip()
            fecha = fecha_entry.get()
            hora = hora_entry.get()
            archivo_path = archivo_var.get()
            usuario_id = self.get_usuario_id()  # Debes tener este método para obtener el id del usuario actual

            if not (nombre and fecha and hora and archivo_path):
                messagebox.showerror("Error", "Todos los campos excepto descripción son obligatorios.", parent=popup)
                return

            # Leer archivo como binario
            try:
                with open(archivo_path, "rb") as f:
                    archivo_bin = f.read()
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo leer el archivo: {e}", parent=popup)
                return

            try:
                agregar_historial(nombre, descripcion, fecha, hora, usuario_id, archivo_bin)
                messagebox.showinfo("Éxito", "Registro agregado correctamente.", parent=popup)
                popup.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo agregar el registro: {e}", parent=popup)

        tk.Button(
            popup,
            text="Guardar",
            font=("Segoe UI", 11, "bold"),
            bg="#0B5394",
            fg="white",
            activebackground="#073763",
            activeforeground="white",
            relief="flat",
            command=guardar
        ).pack(fill="x", padx=40, pady=20, ipady=8)

    def show_user_historial_table(self):
        # Si ya existe el frame de la tabla, destrúyelo para evitar duplicados
        if hasattr(self, "historial_table_frame") and self.historial_table_frame is not None:
            self.historial_table_frame.destroy()

        self.historial_table_frame = tk.Frame(self.content_frame, bg="white")
        self.historial_table_frame.pack(expand=True, fill="both", padx=30, pady=20)

        # Encabezados
        headers = ["ID", "Nombre", "Descripción", "Fecha", "Hora", "UsuarioId", "Archivo", "Descargar"]
        header_bg = "#0B5394"
        header_fg = "white"
        for col, h in enumerate(headers):
            tk.Label(
                self.historial_table_frame, text=h, font=("Segoe UI", 11, "bold"),
                bg=header_bg, fg=header_fg, padx=10, pady=8, borderwidth=0, relief="flat"
            ).grid(row=0, column=col, sticky="nsew", padx=(0 if col == 0 else 2, 2), pady=(0, 2))

        # Cargar imagen de descarga
        download_path = os.path.join(os.path.dirname(__file__), "..", "img", "download.png")
        download_path = os.path.abspath(download_path)
        download_img = Image.open(download_path).resize((20, 20), Image.LANCZOS)
        download_icon = ImageTk.PhotoImage(download_img)
        self.download_icon = download_icon  # Mantener referencia

        # Obtener historial SOLO del usuario actual
        from core.auth import obtener_historial_usuario  # Debes tener esta función en tu backend
        usuario_id = self.get_usuario_id()  # Debes implementar este método para obtener el id del usuario actual
        historial = obtener_historial_usuario(usuario_id)  # Debe regresar una lista de tuplas

        row_bg1 = "#e6f0fa"
        row_bg2 = "#f7fbff"
        for row, item in enumerate(historial, start=1):
            Id, Nombre, Descripcion, Fecha, Hora, UsuarioId, Archivo = item
            bg = row_bg1 if row % 2 == 1 else row_bg2

            tk.Label(self.historial_table_frame, text=Id, bg=bg, font=("Segoe UI", 10), borderwidth=0, relief="flat", padx=8, pady=4).grid(row=row, column=0, sticky="nsew", padx=2, pady=1)
            tk.Label(self.historial_table_frame, text=Nombre, bg=bg, font=("Segoe UI", 10), borderwidth=0, relief="flat", padx=8, pady=4).grid(row=row, column=1, sticky="nsew", padx=2, pady=1)
            tk.Label(self.historial_table_frame, text=Descripcion, bg=bg, font=("Segoe UI", 10), borderwidth=0, relief="flat", padx=8, pady=4, wraplength=200, justify="left").grid(row=row, column=2, sticky="nsew", padx=2, pady=1)
            tk.Label(self.historial_table_frame, text=str(Fecha), bg=bg, font=("Segoe UI", 10), borderwidth=0, relief="flat", padx=8, pady=4).grid(row=row, column=3, sticky="nsew", padx=2, pady=1)
            tk.Label(self.historial_table_frame, text=str(Hora), bg=bg, font=("Segoe UI", 10), borderwidth=0, relief="flat", padx=8, pady=4).grid(row=row, column=4, sticky="nsew", padx=2, pady=1)
            tk.Label(self.historial_table_frame, text=UsuarioId, bg=bg, font=("Segoe UI", 10), borderwidth=0, relief="flat", padx=8, pady=4).grid(row=row, column=5, sticky="nsew", padx=2, pady=1)
            archivo_text = "Sí" if Archivo else "No"
            tk.Label(self.historial_table_frame, text=archivo_text, bg=bg, font=("Segoe UI", 10), borderwidth=0, relief="flat", padx=8, pady=4).grid(row=row, column=6, sticky="nsew", padx=2, pady=1)

            # Botón para descargar archivo
            download_btn = tk.Button(
                self.historial_table_frame,
                image=self.download_icon,
                bg=bg,
                bd=0,
                activebackground="#b3d1f7",
                cursor="hand2",
                command=lambda archivo=Archivo, nombre=Nombre: self.descargar_archivo_historial(archivo, nombre)
            )
            download_btn.grid(row=row, column=7, padx=4, pady=1)

        # Hacer columnas expandibles
        for col in range(len(headers)):
            self.historial_table_frame.grid_columnconfigure(col, weight=1)

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
            filetypes=[("Archivos Excel", "*.xlsx"), ("Todos los archivos", "*")]
        )
        if file_path:
            try:
                with open(file_path, "wb") as f:
                    f.write(archivo_bin)
                messagebox.showinfo("Éxito", f"Archivo guardado en:\n{file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo guardar el archivo: {e}")

    def get_usuario_id(self):
        # Debes implementar la lógica para obtener el id del usuario actual.
        # Por ejemplo, si tienes el username, consulta la base de datos para obtener el id.
        from core.auth import obtener_id_por_username
        return obtener_id_por_username(self.username)
