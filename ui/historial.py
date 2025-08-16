import tkinter as tk
from tkinter import messagebox, filedialog, ttk
from PIL import Image, ImageTk
try:
    from tkcalendar import DateEntry
except Exception:
    DateEntry = None
import os
from ui.base_interface import bind_mousewheel

# importar solo funciones del backend
from core.function_report import (
    fetch_historial,
    filter_historial,
    get_suggested_filename,
    save_binary_to_path,
    delete_historial_record,
    get_username_by_id,
)

class HistorialModule:
    def __init__(self, parent_window):
        self.parent = parent_window
        self._icons = {}

    def show_historial_section(self):
        """Mostrar sección de historial (UI only)"""
        for widget in self.parent.content_frame.winfo_children():
            try:
                widget.destroy()
            except:
                pass

        # contenedor centrado con padding y margen lateral reducido para usar más ancho
        outer = tk.Frame(self.parent.content_frame, bg="white")
        outer.pack(expand=True, fill="both", padx=24, pady=24)

        center_container = tk.Frame(outer, bg="white")
        # usar relwidth alto para ocupar casi todo el ancho manteniendo espacios laterales
        center_container.place(relx=0.5, rely=0.02, relwidth=0.96, relheight=0.96, anchor="n")

        # Título centrado
        title = tk.Label(
            center_container,
            text="Historial",
            font=("Segoe UI", 18, "bold"),
            fg="#0B5394",
            bg="white"
        )
        title.pack(pady=(6, 12))

        # Canvas para scroll
        main_canvas = tk.Canvas(center_container, bg="white", highlightthickness=0)
        main_scrollbar = tk.Scrollbar(center_container, orient="vertical", command=main_canvas.yview)
        content_frame = tk.Frame(main_canvas, bg="white")

        content_frame.bind(
            "<Configure>",
            lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all"))
        )

        window_id = main_canvas.create_window((0, 0), window=content_frame, anchor="nw")
        main_canvas.configure(yscrollcommand=main_scrollbar.set)

        # Cuando el canvas cambie de tamaño, ajustar el width de la ventana interna para que los widgets ocupen todo el ancho
        main_canvas.bind("<Configure>", lambda e: main_canvas.itemconfig(window_id, width=e.width))

        main_canvas.pack(side="left", fill="both", expand=True)
        main_scrollbar.pack(side="right", fill="y")

        bind_mousewheel(main_canvas, main_canvas)

        # Guardar referencia para métodos
        self.historial_table_frame = content_frame
        self.main_canvas = main_canvas
        self.window_id = window_id

        # Controles y tabla
        self._create_filters()
        self._create_table()

        # actualizar inicialmente
        self._actualizar_tabla_historial_filtrada()

    def _create_filters(self):
        """Crear controles de filtro (UI only)"""
        filtro_frame = tk.Frame(self.historial_table_frame, bg="white")
        filtro_frame.pack(fill="x", pady=(8, 14), padx=12)

        # Encabezado y descripción breve
        if hasattr(self.parent, 'rol') and self.parent.rol == "admin":
            subtitle = "Historial general (administrador)"
        else:
            subtitle = f"Mi historial: {self.parent.username}" if getattr(self.parent, "username", None) else "Mi historial"

        lbl_sub = tk.Label(filtro_frame, text=subtitle, bg="white", fg="#0B5394", font=("Segoe UI", 12, "bold"))
        lbl_sub.pack(anchor="w", pady=(0,8))

        controls = tk.Frame(filtro_frame, bg="white")
        controls.pack(fill="x")

        # --- Orden cambiado: Fecha primero, luego Nombre ---
        # Fecha (DateEntry si está)
        tk.Label(controls, text="Fecha:", bg="white", font=("Segoe UI", 10)).grid(row=0, column=0, sticky="w", padx=4, pady=6)
        self.fecha_var = getattr(self, "fecha_var", tk.StringVar())
        if DateEntry is not None:
            self.fecha_entry = DateEntry(controls, textvariable=self.fecha_var, width=16, date_pattern="yyyy-mm-dd")
        else:
            self.fecha_entry = tk.Entry(controls, textvariable=self.fecha_var, width=16)
        self.fecha_entry.grid(row=0, column=1, sticky="w", padx=4, pady=6)

        # Nombre (ahora a la derecha, con más espacio para expandirse)
        tk.Label(controls, text="Nombre:", bg="white", font=("Segoe UI", 10)).grid(row=0, column=2, sticky="w", padx=12, pady=6)
        self.nombre_var = getattr(self, "nombre_var", tk.StringVar())
        tk.Entry(controls, textvariable=self.nombre_var, width=32, font=("Segoe UI", 10)).grid(row=0, column=3, sticky="we", padx=4, pady=6)

        # Usuario (solo admin) - mantener en la fila siguiente para claridad
        if hasattr(self.parent, 'rol') and self.parent.rol == "admin":
            tk.Label(controls, text="Usuario ID:", bg="white", font=("Segoe UI", 10)).grid(row=1, column=0, sticky="w", padx=4, pady=6)
            self.usuario_filtro_var = getattr(self, "usuario_filtro_var", tk.StringVar())
            tk.Entry(controls, textvariable=self.usuario_filtro_var, width=18, font=("Segoe UI", 10)).grid(row=1, column=1, sticky="w", padx=4, pady=6)

        # Botones de acción
        btn_frame = tk.Frame(filtro_frame, bg="white")
        btn_frame.pack(anchor="e", pady=(8,0))

        style_btn = {"font": ("Segoe UI", 10, "bold"), "bd": 0, "cursor": "hand2", "padx": 12, "pady": 6}
        btn_filtrar = tk.Button(btn_frame, text="Filtrar", bg="#0B5394", fg="white", command=self._actualizar_tabla_historial_filtrada, **style_btn)
        btn_filtrar.pack(side="left", padx=6)
        btn_limpiar = tk.Button(btn_frame, text="Limpiar", bg="#888888", fg="white", command=self._limpiar_filtros, **style_btn)
        btn_limpiar.pack(side="left", padx=6)

        # ajustar pesos: hacer que la columna del nombre (3) sea la que se expanda
        controls.grid_columnconfigure(1, weight=0)   # fecha no se expande
        controls.grid_columnconfigure(3, weight=1)   # nombre expande
        controls.grid_columnconfigure(2, weight=0)

    def _create_table(self):
        self.tabla_historial_frame = tk.Frame(self.historial_table_frame, bg="white")
        self.tabla_historial_frame.pack(fill="both", expand=True, padx=12, pady=(6,18))

    def _limpiar_filtros(self):
        self.nombre_var.set("")
        self.fecha_var.set("")
        if hasattr(self, 'usuario_filtro_var'):
            self.usuario_filtro_var.set("")
        self._actualizar_tabla_historial_filtrada()

    def _actualizar_tabla_historial_filtrada(self):
        """Renderiza la tabla usando funciones del backend (core.function_report)"""
        for widget in self.tabla_historial_frame.winfo_children():
            try:
                widget.destroy()
            except:
                pass

        nombre = self.nombre_var.get() if hasattr(self, 'nombre_var') else ""
        fecha = self.fecha_var.get() if hasattr(self, 'fecha_var') else ""
        usuario_filtro = getattr(self, 'usuario_filtro_var', tk.StringVar()).get() if hasattr(self, 'usuario_filtro_var') else ""

        try:
            historial = fetch_historial(role=getattr(self.parent, 'rol', 'usuario'), get_usuario_id=getattr(self.parent, 'get_usuario_id', None))
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar el historial: {e}")
            historial = []

        filtrado = filter_historial(historial, nombre=nombre, fecha=fecha, usuario_filter=usuario_filtro)

        # Encabezados según rol
        if getattr(self.parent, 'rol', '') == "admin":
            headers = ["ID", "Nombre", "Descripción", "Fecha", "Hora", "Usuario ID", "Usuario", "Archivo", "Acciones"]
        else:
            headers = ["ID", "Nombre", "Descripción", "Fecha", "Hora", "Archivo", "Acciones"]

        # Encabezados estilizados
        header_frame = tk.Frame(self.tabla_historial_frame, bg="#0B5394")
        header_frame.pack(fill="x", padx=2)
        for col, h in enumerate(headers):
            lbl = tk.Label(header_frame, text=h, bg="#0B5394", fg="white", font=("Segoe UI", 10, "bold"), padx=8, pady=8)
            lbl.grid(row=0, column=col, sticky="nsew", padx=1)
            header_frame.grid_columnconfigure(col, weight=1, minsize=100)

        body_frame = tk.Frame(self.tabla_historial_frame, bg="white")
        body_frame.pack(fill="both", expand=True)

        if not filtrado:
            no_data_label = tk.Label(
                body_frame,
                text="No se encontraron registros.",
                font=("Segoe UI", 11),
                fg="#666666",
                bg="white",
                pady=20
            )
            no_data_label.pack()
            return

        # filas
        for item in filtrado:
            try:
                Id, Nombre, Descripcion, Fecha, Hora, UsuarioId, Archivo = item[:7]
            except Exception:
                continue

            row_frame = tk.Frame(body_frame, bg="#f7fbff", bd=0, relief="flat")
            row_frame.pack(fill="x", padx=2, pady=6)

            # Column labels (use grid inside row_frame)
            col0 = tk.Label(row_frame, text=str(Id), bg="#f7fbff", font=("Segoe UI", 10), anchor="w")
            col0.grid(row=0, column=0, sticky="nsew", padx=8)
            col1 = tk.Label(row_frame, text=str(Nombre), bg="#f7fbff", font=("Segoe UI", 10), anchor="w")
            col1.grid(row=0, column=1, sticky="nsew", padx=8)
            col2 = tk.Label(row_frame, text=str(Descripcion), bg="#f7fbff", font=("Segoe UI", 10), anchor="w", wraplength=600, justify="left")
            col2.grid(row=0, column=2, sticky="nsew", padx=8)
            col3 = tk.Label(row_frame, text=str(Fecha), bg="#f7fbff", font=("Segoe UI", 10), anchor="w")
            col3.grid(row=0, column=3, sticky="nsew", padx=8)
            col4 = tk.Label(row_frame, text=str(Hora), bg="#f7fbff", font=("Segoe UI", 10), anchor="w")
            col4.grid(row=0, column=4, sticky="nsew", padx=8)

            col_idx = 5
            if getattr(self.parent, 'rol', '') == "admin":
                col_user = tk.Label(row_frame, text=str(UsuarioId), bg="#f7fbff", font=("Segoe UI", 10), anchor="w")
                col_user.grid(row=0, column=col_idx, sticky="nsew", padx=8); col_idx += 1
                username = get_username_by_id(UsuarioId)
                col_username = tk.Label(row_frame, text=username, bg="#f7fbff", font=("Segoe UI", 10), anchor="w")
                col_username.grid(row=0, column=col_idx, sticky="nsew", padx=8); col_idx += 1

            archivo_text = "Sí" if Archivo else "No"
            col_archivo = tk.Label(row_frame, text=archivo_text, bg="#f7fbff", font=("Segoe UI", 10), anchor="w")
            col_archivo.grid(row=0, column=col_idx, sticky="nsew", padx=8); col_idx += 1

            # acciones (descargar/eliminar) en el extremo derecho
            actions = tk.Frame(row_frame, bg="#f7fbff")
            actions.grid(row=0, column=col_idx, sticky="e", padx=8)

            btn_desc = tk.Button(actions, text="Descargar", bg="#2d89ef", fg="white", bd=0, cursor="hand2",
                                 command=lambda archivo=Archivo, nombre=Nombre: self._descargar_archivo(archivo, nombre))
            btn_desc.pack(side="left", padx=6)

            # determinar permiso para eliminar
            can_delete = False
            if getattr(self.parent, 'rol', '') == "admin":
                can_delete = True
            else:
                current_user_id = self.parent.get_usuario_id() if hasattr(self.parent, 'get_usuario_id') else None
                can_delete = (current_user_id == UsuarioId)

            if can_delete:
                btn_del = tk.Button(actions, text="Eliminar", bg="#d9534f", fg="white", bd=0, cursor="hand2",
                                    command=lambda id_hist=Id: self._eliminar_registro(id_hist))
            else:
                btn_del = tk.Button(actions, text="Eliminar", bg="#cccccc", fg="#666666", bd=0, state="disabled")
            btn_del.pack(side="left", padx=6)

            # configure columns weights inside row_frame
            for c in range(col_idx + 1):
                row_frame.grid_columnconfigure(c, weight=1)

    def _load_icon(self, filename):
        if filename in self._icons:
            return self._icons[filename]
        try:
            icon_path = os.path.join(os.path.dirname(__file__), "..", "img", filename)
            icon_path = os.path.abspath(icon_path)
            icon_img = Image.open(icon_path).resize((18, 18), Image.LANCZOS)
            icon = ImageTk.PhotoImage(icon_img)
            self._icons[filename] = icon
            return icon
        except Exception:
            return None

    def _descargar_archivo(self, archivo_bin, nombre):
        """UI: pide ruta al usuario y guarda usando helper del backend para sugerir nombre."""
        if not archivo_bin:
            messagebox.showwarning("Advertencia", "No hay archivo para descargar.")
            return

        try:
            suggested = get_suggested_filename(nombre, archivo_bin)
            desktop = os.path.join(os.path.expanduser("~"), "Desktop")
            if not os.path.exists(desktop):
                desktop = os.path.expanduser("~")

            file_path = filedialog.asksaveasfilename(
                title="Guardar archivo",
                initialfile=suggested,
                initialdir=desktop,
                defaultextension=os.path.splitext(suggested)[1],
                filetypes=[("Archivos", "*.*")]
            )
            if not file_path:
                messagebox.showinfo("Cancelado", "Descarga cancelada por el usuario.")
                return

            # Guardar
            save_binary_to_path(archivo_bin, file_path)
            messagebox.showinfo("Éxito", f"Archivo guardado:\n{file_path}")

        except PermissionError:
            messagebox.showerror("Error", "No tienes permisos para escribir en esa ubicación.\nIntenta con otra carpeta.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar el archivo: {e}")

    def _eliminar_registro(self, id_hist):
        """UI: confirma y elimina vía backend"""
        if not messagebox.askyesno("Eliminar registro", "¿Deseas eliminar este registro?"):
            return
        try:
            delete_historial_record(id_hist)
            messagebox.showinfo("Éxito", "Registro eliminado correctamente.")
            self._actualizar_tabla_historial_filtrada()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo eliminar el registro: {e}")