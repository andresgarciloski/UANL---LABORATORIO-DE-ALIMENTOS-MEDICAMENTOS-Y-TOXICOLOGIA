import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageDraw, ImageTk
import os
from core.auth import agregar_historial  # Debes tener esta función en tu backend
import datetime
from tkcalendar import DateEntry  # Asegúrate de tener esta importación al inicio del archivo

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

        # CAMBIO: Renombrar "Exportar Excel" a "Tabla Nutrimental"
        sections = ["Cálculos", "Tabla Nutrimental", "Historial"]
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

            # CAMBIO: Imagen de Bruni centrada
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

            # CAMBIO: Información centrada
            info = tk.Label(
                content_frame,
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

        elif section_name == "Historial":
            self.show_user_historial_table()
        elif section_name == "Tabla Nutrimental":  # CAMBIO: Nuevo nombre de sección
            self.show_export_excel_section()
        else:
            label = tk.Label(
                self.content_frame,
                text=f"Sección: {section_name}",
                font=("Segoe UI", 14),
                bg="white"
            )
            label.pack(pady=20)

    def show_exportar_excel(self):
        # Limpiar el frame de contenido
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        # CAMBIO: Agregar Canvas y Scrollbar
        main_canvas = tk.Canvas(self.content_frame, bg="white")
        main_scrollbar = tk.Scrollbar(self.content_frame, orient="vertical", command=main_canvas.yview)
        frame = tk.Frame(main_canvas, bg="white")

        frame.bind(
            "<Configure>",
            lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all"))
        )

        main_canvas.create_window((0, 0), window=frame, anchor="nw")
        main_canvas.configure(yscrollcommand=main_scrollbar.set)

        # Información
        info = tk.Label(
            frame,
            text="Desde aquí puedes exportar o importar la base de datos a Excel.\n\n"
                 "Utiliza el botón '+' para agregar un nuevo registro al historial.",
            font=("Segoe UI", 13),
            fg="#0B5394",
            bg="white",
            justify="left"
        )
        info.pack(anchor="nw", pady=(30, 20), padx=30)

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
            command=lambda: self.show_exportar_excel_form()
        )
        plus_btn.place(relx=1.0, rely=1.0, anchor="se", x=-10, y=-10)

        main_canvas.pack(side="left", fill="both", expand=True)
        main_scrollbar.pack(side="right", fill="y")
    
        # NUEVO: Enlazar scroll del mouse
        bind_mousewheel(main_canvas, main_canvas)

    def show_exportar_excel_form(self):
        # Limpiar el frame de contenido
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        frame = tk.Frame(self.content_frame, bg="white")
        frame.pack(expand=True, fill="both", padx=30, pady=20)

        # --- Fase 1 ---
        fase1_label = tk.Label(frame, text="Fase 1", font=("Segoe UI", 15, "bold"), fg="#0B5394", bg="white")
        fase1_label.pack(anchor="w", pady=(10, 5))

        fase1_frame = tk.Frame(frame, bg="white")
        fase1_frame.pack(fill="x", padx=10, pady=(0, 20))

        tk.Label(fase1_frame, text="Nombre:", font=("Segoe UI", 11), bg="white").grid(row=0, column=0, sticky="e", pady=5, padx=5)
        nombre_entry = tk.Entry(fase1_frame, font=("Segoe UI", 11), width=30)
        nombre_entry.grid(row=0, column=1, sticky="w", pady=5, padx=5)

        tk.Label(fase1_frame, text="Descripción:", font=("Segoe UI", 11), bg="white").grid(row=1, column=0, sticky="ne", pady=5, padx=5)
        descripcion_entry = tk.Text(fase1_frame, font=("Segoe UI", 11), width=30, height=4)
        descripcion_entry.grid(row=1, column=1, sticky="w", pady=5, padx=5)

        fecha_actual = datetime.datetime.now().strftime("%Y-%m-%d")
        hora_actual = datetime.datetime.now().strftime("%H:%M:%S")

        tk.Label(fase1_frame, text="Fecha (YYYY-MM-DD):", font=("Segoe UI", 11), bg="white").grid(row=2, column=0, sticky="e", pady=5, padx=5)
        fecha_entry = tk.Entry(fase1_frame, font=("Segoe UI", 11), width=30)
        fecha_entry.grid(row=2, column=1, sticky="w", pady=5, padx=5)
        fecha_entry.insert(0, fecha_actual)
        fecha_entry.config(state="readonly")

        tk.Label(fase1_frame, text="Hora (HH:MM:SS):", font=("Segoe UI", 11), bg="white").grid(row=3, column=0, sticky="e", pady=5, padx=5)
        hora_entry = tk.Entry(fase1_frame, font=("Segoe UI", 11), width=30)
        hora_entry.grid(row=3, column=1, sticky="w", pady=5, padx=5)
        hora_entry.insert(0, hora_actual)
        hora_entry.config(state="readonly")

        tk.Label(fase1_frame, text="Archivo adjunto:", font=("Segoe UI", 11), bg="white").grid(row=4, column=0, sticky="e", pady=5, padx=5)
        archivo_var = tk.StringVar()
        archivo_entry = tk.Entry(fase1_frame, font=("Segoe UI", 11), width=24, textvariable=archivo_var, state="readonly")
        archivo_entry.grid(row=4, column=1, sticky="w", pady=5, padx=5)
        def seleccionar_archivo():
            archivo = filedialog.askopenfilename(title="Seleccionar archivo")
            if archivo:
                archivo_var.set(archivo)
        tk.Button(fase1_frame, text="Seleccionar", command=seleccionar_archivo, font=("Segoe UI", 10)).grid(row=4, column=2, padx=5, pady=5)

        # --- Fase 2 ---
        fase2_label = tk.Label(frame, text="Fase 2", font=("Segoe UI", 15, "bold"), fg="#0B5394", bg="white")
        fase2_label.pack(anchor="w", pady=(20, 5))
        fase2_frame = tk.Frame(frame, bg="white", height=60)
        fase2_frame.pack(fill="x", padx=10, pady=(0, 20))
        # (En blanco por ahora)

        # --- Fase 3 ---
        fase3_label = tk.Label(frame, text="Fase 3", font=("Segoe UI", 15, "bold"), fg="#0B5394", bg="white")
        fase3_label.pack(anchor="w", pady=(20, 5))
        fase3_frame = tk.Frame(frame, bg="white", height=60)
        fase3_frame.pack(fill="x", padx=10, pady=(0, 20))
        # (En blanco por ahora)

        # --- Botones Guardar y Cancelar en la esquina inferior derecha ---
        btn_frame = tk.Frame(frame, bg="white")
        btn_frame.pack(side="bottom", anchor="se", pady=10, padx=10, fill="x")

        def guardar():
            nombre = nombre_entry.get()
            descripcion = descripcion_entry.get("1.0", "end").strip()
            fecha = fecha_entry.get()
            hora = hora_entry.get()
            archivo_path = archivo_var.get()
            usuario_id = self.get_usuario_id()  # Debes tener este método para obtener el id del usuario actual

            if not (nombre and fecha and hora):
                messagebox.showerror("Error", "Nombre, fecha y hora son obligatorios.", parent=frame)
                return

            archivo_bin = b""
            if archivo_path:
                try:
                    with open(archivo_path, "rb") as f:
                        archivo_bin = f.read()
                except Exception as e:
                    messagebox.showerror("Error", f"No se pudo leer el archivo: {e}", parent=frame)
                    return

            try:
                agregar_historial(nombre, descripcion, fecha, hora, usuario_id, archivo_bin)
                messagebox.showinfo("Éxito", "Registro agregado correctamente.", parent=frame)
                self.show_exportar_excel()  # Regresar a la vista original
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo agregar el registro: {e}", parent=frame)

        tk.Button(
            btn_frame,
            text="Guardar",
            font=("Segoe UI", 11, "bold"),
            bg="#0B5394",
            fg="white",
            activebackground="#073763",
            activeforeground="white",
            relief="flat",
            command=guardar
        ).pack(side="right", padx=10, ipadx=10, ipady=6)

        tk.Button(
            btn_frame,
            text="Cancelar",
            font=("Segoe UI", 11, "bold"),
            bg="#bdbdbd",
            fg="white",
            activebackground="#888",
            activeforeground="white",
            relief="flat",
            command=self.show_exportar_excel
        ).pack(side="right", padx=10, ipadx=10, ipady=6)

    def show_user_historial_table(self):
        # Si ya existe el frame de la tabla, destrúyelo para evitar duplicados
        if hasattr(self, "historial_table_frame") and self.historial_table_frame is not None:
            self.historial_table_frame.destroy()

        # CAMBIO: Agregar Canvas y Scrollbar para toda la sección
        main_canvas = tk.Canvas(self.content_frame, bg="white")
        main_scrollbar = tk.Scrollbar(self.content_frame, orient="vertical", command=main_canvas.yview)
        self.historial_table_frame = tk.Frame(main_canvas, bg="white")

        self.historial_table_frame.bind(
            "<Configure>",
            lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all"))
        )

        main_canvas.create_window((0, 0), window=self.historial_table_frame, anchor="nw")
        main_canvas.configure(yscrollcommand=main_scrollbar.set)

        # --- FILTROS ---
        filtro_frame = tk.Frame(self.historial_table_frame, bg="white")
        filtro_frame.grid(row=0, column=0, columnspan=8, sticky="ew", pady=(20, 10), padx=30)
        self.historial_table_frame.grid_rowconfigure(0, weight=0)
        self.historial_table_frame.grid_columnconfigure(0, weight=1)

        self.nombre_var = tk.StringVar()
        self.fecha_var = tk.StringVar()

        tk.Label(filtro_frame, text="Nombre:", bg="white", font=("Segoe UI", 10)).pack(side="left", padx=(0, 5))
        nombre_entry = tk.Entry(filtro_frame, textvariable=self.nombre_var, width=15, font=("Segoe UI", 10))
        nombre_entry.pack(side="left", padx=(0, 10))

        tk.Label(filtro_frame, text="Fecha:", bg="white", font=("Segoe UI", 10)).pack(side="left", padx=(0, 5))
        self.fecha_entry = DateEntry(filtro_frame, textvariable=self.fecha_var, width=12, date_pattern="yyyy-mm-dd", background="#0B5394", foreground="white", font=("Segoe UI", 10))
        self.fecha_entry.pack(side="left", padx=(0, 10))

        def aplicar_filtro():
            self._actualizar_tabla_historial_usuario_filtrada()

        def limpiar_filtro():
            self.nombre_var.set("")
            self.fecha_var.set("")
            self._actualizar_tabla_historial_usuario_filtrada()

        tk.Button(filtro_frame, text="Filtrar", command=aplicar_filtro, bg="#0B5394", fg="white", font=("Segoe UI", 10, "bold"), relief="flat", padx=12, pady=2, cursor="hand2").pack(side="left", padx=10)
        tk.Button(filtro_frame, text="Limpiar", command=limpiar_filtro, bg="#888", fg="white", font=("Segoe UI", 10), relief="flat", padx=10, pady=2, cursor="hand2").pack(side="left", padx=5)

        # --- Tabla ---
        self.tabla_historial_frame = tk.Frame(self.historial_table_frame, bg="white")
        self.tabla_historial_frame.grid(row=1, column=0, columnspan=8, sticky="nsew", padx=30, pady=20)
        self.historial_table_frame.grid_rowconfigure(1, weight=1)
        self.historial_table_frame.grid_columnconfigure(0, weight=1)

        # Empaquetar canvas y scrollbar
        main_canvas.pack(side="left", fill="both", expand=True)
        main_scrollbar.pack(side="right", fill="y")
        
        # NUEVO: Enlazar scroll del mouse
        bind_mousewheel(main_canvas, main_canvas)

        self._actualizar_tabla_historial_usuario_filtrada()

    def _actualizar_tabla_historial_usuario_filtrada(self):
        # Borra la tabla anterior si existe
        for widget in self.tabla_historial_frame.winfo_children():
            widget.destroy()

        nombre = self.nombre_var.get()
        fecha = self.fecha_var.get()

        from core.auth import obtener_historial_usuario
        usuario_id = self.get_usuario_id()
        historial = obtener_historial_usuario(usuario_id)  # Lista de tuplas

        filtrado = []
        for item in historial:
            Id, Nombre, Descripcion, Fecha, Hora, UsuarioId, Archivo = item
            if nombre and nombre.lower() not in str(Nombre).lower():
                continue
            if fecha and str(Fecha) != fecha:
                continue
            filtrado.append(item)

        # Encabezados (sin UsuarioId)
        headers = ["ID", "Nombre", "Descripción", "Fecha", "Hora", "Archivo", "Descargar", "Eliminar"]
        header_bg = "#0B5394"
        header_fg = "white"
        for col, h in enumerate(headers):
            tk.Label(
                self.tabla_historial_frame, text=h, font=("Segoe UI", 11, "bold"),
                bg=header_bg, fg=header_fg, padx=10, pady=8, borderwidth=0, relief="flat"
            ).grid(row=0, column=col, sticky="nsew", padx=(0 if col == 0 else 2, 2), pady=(0, 2))

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

        row_bg1 = "#e6f0fa"
        row_bg2 = "#f7fbff"
        for row, item in enumerate(filtrado, start=1):
            Id, Nombre, Descripcion, Fecha, Hora, UsuarioId, Archivo = item
            bg = row_bg1 if row % 2 == 1 else row_bg2

            tk.Label(self.tabla_historial_frame, text=Id, bg=bg, font=("Segoe UI", 10), borderwidth=0, relief="flat", padx=8, pady=4).grid(row=row, column=0, sticky="nsew", padx=2, pady=1)
            tk.Label(self.tabla_historial_frame, text=Nombre, bg=bg, font=("Segoe UI", 10), borderwidth=0, relief="flat", padx=8, pady=4).grid(row=row, column=1, sticky="nsew", padx=2, pady=1)
            tk.Label(self.tabla_historial_frame, text=Descripcion, bg=bg, font=("Segoe UI", 10), borderwidth=0, relief="flat", padx=8, pady=4, wraplength=200, justify="left").grid(row=row, column=2, sticky="nsew", padx=2, pady=1)
            tk.Label(self.tabla_historial_frame, text=str(Fecha), bg=bg, font=("Segoe UI", 10), borderwidth=0, relief="flat", padx=8, pady=4).grid(row=row, column=3, sticky="nsew", padx=2, pady=1)
            tk.Label(self.tabla_historial_frame, text=str(Hora), bg=bg, font=("Segoe UI", 10), borderwidth=0, relief="flat", padx=8, pady=4).grid(row=row, column=4, sticky="nsew", padx=2, pady=1)
            archivo_text = "Sí" if Archivo else "No"
            tk.Label(self.tabla_historial_frame, text=archivo_text, bg=bg, font=("Segoe UI", 10), borderwidth=0, relief="flat", padx=8, pady=4).grid(row=row, column=5, sticky="nsew", padx=2, pady=1)

            # Botón para descargar archivo
            download_btn = tk.Button(
                self.tabla_historial_frame,
                image=self.download_icon,
                bg=bg,
                bd=0,
                activebackground="#b3d1f7",
                cursor="hand2",
                command=lambda archivo=Archivo, nombre=Nombre: self.descargar_archivo_historial(archivo, nombre)
            )
            download_btn.grid(row=row, column=6, padx=4, pady=1)

            # Botón para eliminar registro
            delete_btn = tk.Button(
                self.tabla_historial_frame,
                image=self.trash_icon,
                bg=bg,
                bd=0,
                activebackground="#f7bdbd",
                cursor="hand2",
                command=lambda id_hist=Id: self.delete_user_historial_record(id_hist)
            )
            delete_btn.grid(row=row, column=7, padx=4, pady=1)

        # Hacer columnas expandibles
        for col in range(len(headers)):
            self.tabla_historial_frame.grid_columnconfigure(col, weight=1)

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

    def delete_user_historial_record(self, id_hist):
        from core.auth import eliminar_historial  # Debes tener esta función en tu backend
        if messagebox.askyesno("Eliminar registro", "¿Estás seguro de que deseas eliminar este registro del historial?"):
            try:
                eliminar_historial(id_hist)
                messagebox.showinfo("Éxito", "Registro eliminado correctamente.")
                self.show_user_historial_table()
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo eliminar el registro: {e}")

    def show_export_excel_section(self):
        # Limpiar el contenido anterior
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        # CAMBIO: Nuevo título
        title = tk.Label(
            self.content_frame,
            text="Tabla Nutrimental Mexicana",
            font=("Segoe UI", 20, "bold"),
            bg="white",
            fg="#0B5394"
        )
        title.pack(pady=(30, 20))

        # Frame principal con scroll
        main_frame = tk.Frame(self.content_frame, bg="white")
        main_frame.pack(expand=True, fill="both", padx=30, pady=20)

        # Canvas para scroll
        canvas = tk.Canvas(main_frame, bg="white")
        scrollbar = tk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="white")

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # --- CAMPOS BÁSICOS ---
        basic_frame = tk.LabelFrame(scrollable_frame, text="Información Básica", font=("Segoe UI", 12, "bold"), bg="white", fg="#0B5394")
        basic_frame.pack(fill="x", pady=(0, 20), padx=10)

        tk.Label(basic_frame, text="Nombre del producto:", bg="white", font=("Segoe UI", 10)).grid(row=0, column=0, sticky="w", padx=10, pady=5)
        self.nombre_entry = tk.Entry(basic_frame, font=("Segoe UI", 10), width=40)
        self.nombre_entry.grid(row=0, column=1, padx=10, pady=5, sticky="ew")

        tk.Label(basic_frame, text="Descripción:", bg="white", font=("Segoe UI", 10)).grid(row=1, column=0, sticky="w", padx=10, pady=5)
        self.descripcion_entry = tk.Text(basic_frame, font=("Segoe UI", 10), width=40, height=3)
        self.descripcion_entry.grid(row=1, column=1, padx=10, pady=5, sticky="ew")

        # CAMBIO: Fecha automática y no editable
        tk.Label(basic_frame, text="Fecha:", bg="white", font=("Segoe UI", 10)).grid(row=2, column=0, sticky="w", padx=10, pady=5)
        self.fecha_entry = tk.Entry(basic_frame, font=("Segoe UI", 10), width=20, state="readonly", bg="#f0f0f0")
        fecha_actual = datetime.datetime.now().strftime("%Y-%m-%d")
        self.fecha_entry.config(state="normal")
        self.fecha_entry.insert(0, fecha_actual)
        self.fecha_entry.config(state="readonly")
        self.fecha_entry.grid(row=2, column=1, padx=10, pady=5, sticky="w")

        # CAMBIO: Hora automática y no editable
        tk.Label(basic_frame, text="Hora:", bg="white", font=("Segoe UI", 10)).grid(row=3, column=0, sticky="w", padx=10, pady=5)
        self.hora_entry = tk.Entry(basic_frame, font=("Segoe UI", 10), width=20, state="readonly", bg="#f0f0f0")
        hora_actual = datetime.datetime.now().strftime("%H:%M:%S")
        self.hora_entry.config(state="normal")
        self.hora_entry.insert(0, hora_actual)
        self.hora_entry.config(state="readonly")
        self.hora_entry.grid(row=3, column=1, padx=10, pady=5, sticky="w")

        basic_frame.grid_columnconfigure(1, weight=1)

        # --- DATOS NUTRICIONALES ---
        nutri_frame = tk.LabelFrame(scrollable_frame, text="Datos Nutricionales", font=("Segoe UI", 12, "bold"), bg="white", fg="#0B5394")
        nutri_frame.pack(fill="x", pady=(0, 20), padx=10)

        # Variables para los campos nutricionales
        self.nutri_vars = {}
        # CAMBIO: Sin valores predeterminados (placeholder vacío)
        nutri_fields = [
            ("humedad", "Humedad (%)", ""),
            ("cenizas", "Cenizas (%)", ""),
            ("proteina", "Proteína (%)", ""),
            ("grasa_total", "Grasa total (%)", ""),
            ("fibra_dietetica", "Fibra dietética (%)", ""),
            ("azucares", "Azúcares totales (%)", ""),
            ("sodio", "Sodio (mg/100g)", ""),
            ("acidos_grasos_saturados", "Ácidos grasos saturados (%)", ""),
            ("porcion", "Tamaño de porción (g o mL)", ""),
            ("contenido_neto", "Contenido neto del envase (opcional)", "")
        ]

        row = 0
        col = 0
        for key, label, placeholder in nutri_fields:
            tk.Label(nutri_frame, text=label + ":", bg="white", font=("Segoe UI", 10)).grid(row=row, column=col*2, sticky="w", padx=10, pady=5)
            entry = tk.Entry(nutri_frame, font=("Segoe UI", 10), width=15)
            # CAMBIO: No insertar valores predeterminados
            if placeholder:  # Solo si hay placeholder (en este caso, todos están vacíos)
                entry.insert(0, placeholder)
            entry.grid(row=row, column=col*2+1, padx=10, pady=5, sticky="ew")
            self.nutri_vars[key] = entry
            
            col += 1
            if col >= 2:  # 2 columnas
                col = 0
                row += 1

        nutri_frame.grid_columnconfigure(1, weight=1)
        nutri_frame.grid_columnconfigure(3, weight=1)

        # --- BOTONES ---
        buttons_frame = tk.Frame(scrollable_frame, bg="white")
        buttons_frame.pack(fill="x", pady=20, padx=10)

        tk.Button(
            buttons_frame,
            text="Calcular Tabla Nutrimental",
            command=self.calcular_tabla_nutrimental,
            bg="#0B5394",
            fg="white",
            font=("Segoe UI", 12, "bold"),
            relief="flat",
            padx=20,
            pady=10,
            cursor="hand2"
        ).pack(side="left", padx=(0, 10))

        tk.Button(
            buttons_frame,
            text="Exportar a Excel",
            command=self.exportar_nutrimental_excel,
            bg="#28a745",
            fg="white",
            font=("Segoe UI", 12, "bold"),
            relief="flat",
            padx=20,
            pady=10,
            cursor="hand2"
        ).pack(side="left", padx=10)

        # --- ÁREA DE RESULTADOS ---
        self.resultados_frame = tk.LabelFrame(scrollable_frame, text="Resultados", font=("Segoe UI", 12, "bold"), bg="white", fg="#0B5394")
        self.resultados_frame.pack(fill="both", expand=True, pady=(20, 0), padx=10)

        self.resultados_text = tk.Text(self.resultados_frame, font=("Courier New", 10), bg="#f8f9fa", state="disabled")
        resultados_scroll = tk.Scrollbar(self.resultados_frame, orient="vertical", command=self.resultados_text.yview)
        self.resultados_text.configure(yscrollcommand=resultados_scroll.set)

        self.resultados_text.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        resultados_scroll.pack(side="right", fill="y", pady=10)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
        # NUEVO: Enlazar scroll del mouse
        bind_mousewheel(canvas, canvas)

    def calcular_tabla_nutrimental(self):
        try:
            # Obtener valores de los campos
            data = {}
            for key, entry in self.nutri_vars.items():
                value = entry.get().strip()
                if value and key != "contenido_neto":
                    data[key] = float(value)
                elif value and key == "contenido_neto":
                    data[key] = float(value) if value else None

            # Validaciones básicas
            required_fields = ["humedad", "cenizas", "proteina", "grasa_total", "fibra_dietetica", "azucares", "sodio", "acidos_grasos_saturados", "porcion"]
            for field in required_fields:
                if field not in data:
                    messagebox.showerror("Error", f"El campo {field} es requerido")
                    return

            # Cálculos
            resultados = self._calcular_nutrimental(data)
            
            # Mostrar resultados
            self._mostrar_resultados(resultados)
            
            # Guardar para exportar
            self.ultimo_calculo = {
                "datos_basicos": {
                    "nombre": self.nombre_entry.get(),
                    "descripcion": self.descripcion_entry.get("1.0", "end-1c"),
                    "fecha": self.fecha_entry.get(),
                    "hora": self.hora_entry.get()
                },
                "datos_entrada": data,
                "resultados": resultados
            }

        except ValueError as e:
            messagebox.showerror("Error", "Por favor ingrese valores numéricos válidos")
        except Exception as e:
            messagebox.showerror("Error", f"Error en el cálculo: {str(e)}")

    def _calcular_nutrimental(self, data):
        # Redondear a enteros según especificación
        proteina = round(data["proteina"])
        grasa_total = round(data["grasa_total"])
        azucares = round(data["azucares"])
        fibra_dietetica = round(data["fibra_dietetica"])
        
        # Cálculos derivados
        grasa_saturada = round(grasa_total * (data["acidos_grasos_saturados"] / 100))
        hidratos_carbono_totales = 100 - (data["humedad"] + data["cenizas"] + proteina + grasa_total)
        carbohidratos_disponibles = round(hidratos_carbono_totales - fibra_dietetica)
        
        # Energía por 100g
        energia_kcal = round((proteina + carbohidratos_disponibles) * 4 + grasa_total * 9)
        energia_kj = round((proteina + carbohidratos_disponibles) * 17 + grasa_total * 37)
        
        # Por 100g
        por_100g = {
            "proteina": proteina,
            "grasa_total": grasa_total,
            "grasa_saturada": grasa_saturada,
            "carbohidratos_disponibles": carbohidratos_disponibles,
            "azucares": azucares,
            "fibra_dietetica": fibra_dietetica,
            "sodio": round(data["sodio"]),
            "energia_kcal": energia_kcal,
            "energia_kj": energia_kj
        }
        
        # Por porción
        factor_porcion = data["porcion"] / 100
        por_porcion = {}
        for key, value in por_100g.items():
            if key == "sodio":
                sodio_porcion = value * factor_porcion
                if sodio_porcion < 5:
                    por_porcion[key] = 0
                elif sodio_porcion <= 140:
                    por_porcion[key] = round(sodio_porcion / 5) * 5
                else:
                    por_porcion[key] = round(sodio_porcion / 10) * 10
            else:
                por_porcion[key] = round(value * factor_porcion)
        
        resultados = {
            "por_100g": por_100g,
            "por_porcion": por_porcion
        }
        
        # Por envase (si se especifica)
        if "contenido_neto" in data and data["contenido_neto"]:
            factor_envase = data["contenido_neto"] / 100
            resultados["por_envase"] = {
                "energia_kcal": round(energia_kcal * factor_envase),
                "energia_kj": round(energia_kj * factor_envase)
            }
        
        return resultados

    def _mostrar_resultados(self, resultados):
        self.resultados_text.config(state="normal")
        self.resultados_text.delete("1.0", "end")
        
        texto = "TABLA NUTRIMENTAL MEXICANA\n"
        texto += "=" * 50 + "\n\n"
        
        # Por 100g
        texto += "POR 100g/mL:\n"
        texto += "-" * 20 + "\n"
        for key, value in resultados["por_100g"].items():
            texto += f"{key.replace('_', ' ').title()}: {value}\n"
        texto += "\n"
        
        # Por porción
        texto += "POR PORCIÓN:\n"
        texto += "-" * 20 + "\n"
        for key, value in resultados["por_porcion"].items():
            texto += f"{key.replace('_', ' ').title()}: {value}\n"
        texto += "\n"
        
        # Por envase
        if "por_envase" in resultados:
            texto += "POR ENVASE:\n"
            texto += "-" * 20 + "\n"
            for key, value in resultados["por_envase"].items():
                texto += f"{key.replace('_', ' ').title()}: {value}\n"
    
        self.resultados_text.insert("1.0", texto)
        self.resultados_text.config(state="disabled")

    def exportar_nutrimental_excel(self):
        if not hasattr(self, "ultimo_calculo"):
            messagebox.showwarning("Advertencia", "Primero debe calcular la tabla nutrimental")
            return
        
        try:
            import pandas as pd
            from tkinter import filedialog
            import datetime
            import os
            
            # OBTENER VALORES ACTUALES DE LOS CAMPOS
            nombre_actual = self.nombre_entry.get().strip()
            descripcion_actual = self.descripcion_entry.get("1.0", "end-1c").strip()
            
            # CAMBIO: Obtener fecha y hora actuales automáticamente
            fecha_actual_widget = datetime.datetime.now().strftime("%Y-%m-%d")
            hora_actual_widget = datetime.datetime.now().strftime("%H:%M:%S")
            
            # Validar que el nombre no esté vacío
            if not nombre_actual:
                messagebox.showerror("Error", "El campo 'Nombre' es obligatorio")
                return
            
            # Generar nombre predeterminado con fecha y hora
            fecha_actual = datetime.datetime.now()
            nombre_base = nombre_actual or "Tabla_Nutrimental"
            # Limpiar caracteres especiales del nombre
            nombre_limpio = "".join(c for c in nombre_base if c.isalnum() or c in (' ', '-', '_')).rstrip()
            nombre_limpio = nombre_limpio.replace(' ', '_')
            
            # Formato: NombreProducto_YYYY-MM-DD_HHMMSS.xlsx
            timestamp = fecha_actual.strftime("%Y-%m-%d_%H%M%S")
            nombre_predeterminado = f"{nombre_limpio}_{timestamp}.xlsx"
            
            # Preparar datos para Excel
            datos_excel = []
            
            # Información básica (USAR VALORES ACTUALES)
            datos_excel.append(["INFORMACIÓN BÁSICA", "", ""])
            datos_excel.append(["Nombre", nombre_actual, ""])
            datos_excel.append(["Descripción", descripcion_actual, ""])
            datos_excel.append(["Fecha", fecha_actual_widget, ""])
            datos_excel.append(["Hora", hora_actual_widget, ""])
            datos_excel.append(["Usuario", self.username, ""])
            datos_excel.append(["Fecha de exportación", fecha_actual.strftime("%Y-%m-%d %H:%M:%S"), ""])
            datos_excel.append(["", "", ""])
            
            # Datos de entrada
            datos_excel.append(["DATOS DE ENTRADA", "", ""])
            for key, value in self.ultimo_calculo["datos_entrada"].items():
                nombre_campo = key.replace('_', ' ').title()
                datos_excel.append([nombre_campo, value, ""])
            datos_excel.append(["", "", ""])
            
            # Tabla nutrimental
            datos_excel.append(["TABLA NUTRIMENTAL", "Por 100g", "Por Porción"])
            resultados = self.ultimo_calculo["resultados"]
            
            for key in resultados["por_100g"].keys():
                nombre = key.replace('_', ' ').title()
                valor_100g = resultados["por_100g"][key]
                valor_porcion = resultados["por_porcion"][key]
                datos_excel.append([nombre, valor_100g, valor_porcion])
            
            # Por envase si existe
            if "por_envase" in resultados:
                datos_excel.append(["", "", ""])
                datos_excel.append(["POR ENVASE", "", ""])
                for key, value in resultados["por_envase"].items():
                    nombre = key.replace('_', ' ').title()
                    datos_excel.append([nombre, value, ""])
            
            # Crear DataFrame
            df = pd.DataFrame(datos_excel, columns=["Componente", "Valor 100g", "Valor Porción"])
            
            # Sugerir ubicación de descarga (Escritorio del usuario)
            desktop = os.path.join(os.path.expanduser("~"), "Desktop")
            
            # Guardar archivo con nombre predeterminado
            filename = filedialog.asksaveasfilename(
                initialfile=nombre_predeterminado,
                initialdir=desktop,
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
                title="Guardar tabla nutrimental"
            )
            
            if filename:
                # Crear el archivo Excel
                df.to_excel(filename, index=False, sheet_name="Tabla Nutrimental")
                
                # Leer el archivo para guardarlo en la base de datos
                with open(filename, "rb") as f:
                    archivo_binario = f.read()
                
                # Guardar en la base de datos
                from core.auth import agregar_historial
                usuario_id = self.get_usuario_id()
                
                # Crear descripción más detallada (USAR DESCRIPCIÓN ACTUAL + DATOS NUTRICIONALES)
                descripcion_completa = f"{descripcion_actual}\n\n"
                descripcion_completa += "DATOS NUTRICIONALES:\n"
                descripcion_completa += f"- Proteína: {resultados['por_100g']['proteina']}g/100g\n"
                descripcion_completa += f"- Grasa total: {resultados['por_100g']['grasa_total']}g/100g\n"
                descripcion_completa += f"- Carbohidratos disponibles: {resultados['por_100g']['carbohidratos_disponibles']}g/100g\n"
                descripcion_completa += f"- Energía: {resultados['por_100g']['energia_kcal']} kcal/100g\n"
                descripcion_completa += f"- Tamaño de porción: {self.ultimo_calculo['datos_entrada']['porcion']}g\n"
                descripcion_completa += f"Archivo generado automáticamente: {os.path.basename(filename)}"
                
                # USAR VALORES ACTUALES DE LOS CAMPOS DE LA INTERFAZ
                agregar_historial(
                    nombre_actual,              # Nombre del campo de la interfaz
                    descripcion_completa,       # Descripción del campo + datos nutricionales
                    fecha_actual_widget,        # Fecha automática actual
                    hora_actual_widget,         # Hora automática actual
                    usuario_id,                 # usuario_id
                    archivo_binario             # archivo_bin
                )
                
                messagebox.showinfo(
                    "Éxito", 
                    f"Tabla nutrimental exportada exitosamente:\n\n"
                    f"📁 Archivo: {os.path.basename(filename)}\n"
                    f"📂 Ubicación: {filename}\n"
                    f"💾 Guardado en base de datos: ✓\n"
                    f"👤 Usuario: {self.username}\n"
                    f"📝 Nombre en BD: {nombre_actual}"
                )
                
            else:
                messagebox.showinfo("Cancelado", "Exportación cancelada por el usuario.")
        
        except Exception as e:
            messagebox.showerror("Error", f"Error al exportar: {str(e)}")
            import traceback
            print(f"Error completo: {traceback.format_exc()}")

    def get_usuario_id(self):
        # Función auxiliar para obtener el ID del usuario actual
        # Implementa según tu sistema de autenticación
        from core.auth import obtener_usuario_por_username
        usuario = obtener_usuario_por_username(self.username)
        return usuario[0] if usuario else None

    def show_agregar_registro_simple(self):
        # Limpiar el frame de contenido
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        # CAMBIO: Agregar Canvas y Scrollbar
        main_canvas = tk.Canvas(self.content_frame, bg="white")
        main_scrollbar = tk.Scrollbar(self.content_frame, orient="vertical", command=main_canvas.yview)
        frame = tk.Frame(main_canvas, bg="white")

        frame.bind(
            "<Configure>",
            lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all"))
        )

        main_canvas.create_window((0, 0), window=frame, anchor="nw")
        main_canvas.configure(yscrollcommand=main_scrollbar.set)

        # Título
        title = tk.Label(
            frame,
            text="Agregar Registro Simple",
            font=("Segoe UI", 18, "bold"),
            bg="white",
            fg="#0B5394"
        )
        title.pack(pady=(30, 20), padx=30)

        # Información
        info = tk.Label(
            frame,
            text="Agrega un registro básico al historial con archivo adjunto opcional.",
            font=("Segoe UI", 12),
            fg="#666",
            bg="white",
            justify="left"
        )
        info.pack(anchor="nw", pady=(0, 20), padx=10)

        # Formulario básico
        form_frame = tk.Frame(frame, bg="white")
        form_frame.pack(fill="x", padx=10, pady=(0, 20))

        tk.Label(form_frame, text="Nombre:", font=("Segoe UI", 11), bg="white").grid(row=0, column=0, sticky="e", pady=5, padx=5)
        nombre_entry = tk.Entry(form_frame, font=("Segoe UI", 11), width=30)
        nombre_entry.grid(row=0, column=1, sticky="w", pady=5, padx=5)

        tk.Label(form_frame, text="Descripción:", font=("Segoe UI", 11), bg="white").grid(row=1, column=0, sticky="ne", pady=5, padx=5)
        descripcion_entry = tk.Text(form_frame, font=("Segoe UI", 11), width=30, height=4)
        descripcion_entry.grid(row=1, column=1, sticky="w", pady=5, padx=5)

        fecha_actual = datetime.datetime.now().strftime("%Y-%m-%d")
        hora_actual = datetime.datetime.now().strftime("%H:%M:%S")

        tk.Label(form_frame, text="Fecha:", font=("Segoe UI", 11), bg="white").grid(row=2, column=0, sticky="e", pady=5, padx=5)
        fecha_entry = tk.Entry(form_frame, font=("Segoe UI", 11), width=30)
        fecha_entry.grid(row=2, column=1, sticky="w", pady=5, padx=5)
        fecha_entry.insert(0, fecha_actual)

        tk.Label(form_frame, text="Hora:", font=("Segoe UI", 11), bg="white").grid(row=3, column=0, sticky="e", pady=5, padx=5)
        hora_entry = tk.Entry(form_frame, font=("Segoe UI", 11), width=30)
        hora_entry.grid(row=3, column=1, sticky="w", pady=5, padx=5)
        hora_entry.insert(0, hora_actual)

        tk.Label(form_frame, text="Archivo adjunto:", font=("Segoe UI", 11), bg="white").grid(row=4, column=0, sticky="e", pady=5, padx=5)
        archivo_var = tk.StringVar()
        archivo_entry = tk.Entry(form_frame, font=("Segoe UI", 11), width=24, textvariable=archivo_var, state="readonly")
        archivo_entry.grid(row=4, column=1, sticky="w", pady=5, padx=5)
        
        def seleccionar_archivo():
            archivo = filedialog.askopenfilename(title="Seleccionar archivo")
            if archivo:
                archivo_var.set(archivo)
        
        tk.Button(form_frame, text="Seleccionar", command=seleccionar_archivo, font=("Segoe UI", 10)).grid(row=4, column=2, padx=5, pady=5)

        # Botones
        btn_frame = tk.Frame(frame, bg="white")
        btn_frame.pack(side="bottom", anchor="se", pady=20, padx=10)

        def guardar():
            nombre = nombre_entry.get()
            descripcion = descripcion_entry.get("1.0", "end").strip()
            fecha = fecha_entry.get()
            hora = hora_entry.get()
            archivo_path = archivo_var.get()
            usuario_id = self.get_usuario_id()

            if not (nombre and fecha and hora):
                messagebox.showerror("Error", "Nombre, fecha y hora son obligatorios.")
                return

            archivo_bin = b""
            if archivo_path:
                try:
                    with open(archivo_path, "rb") as f:
                        archivo_bin = f.read()
                except Exception as e:
                    messagebox.showerror("Error", f"No se pudo leer el archivo: {e}")
                    return

            try:
                agregar_historial(nombre, descripcion, fecha, hora, usuario_id, archivo_bin)
                messagebox.showinfo("Éxito", "Registro agregado correctamente.")
                self.show_export_excel_section()  # Regresar a la vista principal
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo agregar el registro: {e}")

        tk.Button(
            btn_frame,
            text="Guardar",
            font=("Segoe UI", 11, "bold"),
            bg="#0B5394",
            fg="white",
            activebackground="#073763",
            activeforeground="white",
            relief="flat",
            command=guardar
        ).pack(side="right", padx=(0, 10), ipadx=10, ipady=6)

        tk.Button(
            btn_frame,
            text="Cancelar",
            font=("Segoe UI", 11, "bold"),
            bg="#bdbdbd",
            fg="white",
            activebackground="#888",
            activeforeground="white",
            relief="flat",
            command=self.show_export_excel_section  # CAMBIO: Mantener la referencia correcta
        ).pack(side="right", padx=10, ipadx=10, ipady=6)

        main_canvas.pack(side="left", fill="both", expand=True)
        main_scrollbar.pack(side="right", fill="y")
    
        # NUEVO: Enlazar scroll del mouse
        bind_mousewheel(main_canvas, main_canvas)
