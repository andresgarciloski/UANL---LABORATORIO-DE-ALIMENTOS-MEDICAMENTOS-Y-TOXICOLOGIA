import tkinter as tk
from tkinter import messagebox, filedialog, ttk
from PIL import Image, ImageTk
try:
    from tkcalendar import DateEntry
except Exception:
    DateEntry = None
import os
import tempfile
from io import BytesIO
from ui.base_interface import bind_mousewheel, _BG, _PRIMARY, _PRIMARY_DARK, _TEXT
from datetime import datetime, date  # NUEVO
import re  # NUEVO

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
        outer = tk.Frame(self.parent.content_frame, bg=_BG)
        outer.pack(expand=True, fill="both", padx=24, pady=24)

        center_container = tk.Frame(outer, bg=_BG)
        center_container.place(relx=0.5, rely=0.02, relwidth=0.96, relheight=0.96, anchor="n")

        # Título centrado
        title = tk.Label(
            center_container,
            text="Historial",
            font=("Segoe UI", 18, "bold"),
            fg=_PRIMARY,
            bg=_BG
        )
        title.pack(pady=(6, 12))

        # Canvas para scroll
        main_canvas = tk.Canvas(center_container, bg=_BG, highlightthickness=0)
        main_scrollbar = tk.Scrollbar(center_container, orient="vertical", command=main_canvas.yview)
        content_frame = tk.Frame(main_canvas, bg=_BG)

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
        filtro_frame = tk.Frame(self.historial_table_frame, bg=_BG)
        filtro_frame.pack(fill="x", pady=(8, 14), padx=12)

        # Encabezado y descripción breve
        if hasattr(self.parent, 'rol') and self.parent.rol == "admin":
            subtitle = "Historial general (administrador)"
        else:
            subtitle = f"Mi historial: {self.parent.username}" if getattr(self.parent, "username", None) else "Mi historial"

        lbl_sub = tk.Label(filtro_frame, text=subtitle, bg=_BG, fg=_PRIMARY, font=("Segoe UI", 12, "bold"))
        lbl_sub.pack(anchor="w", pady=(0,8))

        controls = tk.Frame(filtro_frame, bg=_BG)
        controls.pack(fill="x")

        # --- Orden cambiado: Fecha primero, luego Nombre ---
        # Fecha (DateEntry si está)
        tk.Label(controls, text="Fecha:", bg=_BG, fg=_TEXT, font=("Segoe UI", 10)).grid(row=0, column=0, sticky="w", padx=4, pady=6)
        self.fecha_var = getattr(self, "fecha_var", tk.StringVar())
        if DateEntry is not None:
            self.fecha_entry = DateEntry(controls, textvariable=self.fecha_var, width=16, date_pattern="yyyy-mm-dd")
            # Normaliza al seleccionar en calendario y al salir del control
            self.fecha_entry.bind("<<DateEntrySelected>>", lambda e: self.fecha_var.set(self._normalize_date_input(self.fecha_entry.get_date()) or ""))
            self.fecha_entry.bind("<FocusOut>", lambda e: self._sync_date_string())
        else:
            self.fecha_entry = tk.Entry(controls, textvariable=self.fecha_var, width=16)
            # También normaliza si el usuario escribe manualmente
            self.fecha_entry.bind("<FocusOut>", lambda e: self._sync_date_string())
        self.fecha_entry.grid(row=0, column=1, sticky="w", padx=4, pady=6)

        # Nombre (ahora a la derecha, con más espacio para expandirse)
        tk.Label(controls, text="Nombre:", bg=_BG, fg=_TEXT, font=("Segoe UI", 10)).grid(row=0, column=2, sticky="w", padx=12, pady=6)
        self.nombre_var = getattr(self, "nombre_var", tk.StringVar())
        tk.Entry(controls, textvariable=self.nombre_var, width=32, font=("Segoe UI", 10)).grid(row=0, column=3, sticky="we", padx=4, pady=6)

        # Usuario (solo admin) - mantener en la fila siguiente para claridad
        if hasattr(self.parent, 'rol') and self.parent.rol == "admin":
            tk.Label(controls, text="Usuario ID:", bg=_BG, fg=_TEXT, font=("Segoe UI", 10)).grid(row=1, column=0, sticky="w", padx=4, pady=6)
            self.usuario_filtro_var = getattr(self, "usuario_filtro_var", tk.StringVar())
            tk.Entry(controls, textvariable=self.usuario_filtro_var, width=18, font=("Segoe UI", 10)).grid(row=1, column=1, sticky="w", padx=4, pady=6)

        # Botones de acción
        btn_frame = tk.Frame(filtro_frame, bg=_BG)
        btn_frame.pack(anchor="e", pady=(8,0))

        style_btn = {"font": ("Segoe UI", 10, "bold"), "bd": 0, "cursor": "hand2", "padx": 12, "pady": 6}
        btn_filtrar = tk.Button(btn_frame, text="Filtrar", bg=_PRIMARY, fg="white", activebackground=_PRIMARY_DARK, command=self._actualizar_tabla_historial_filtrada, **style_btn)
        btn_filtrar.pack(side="left", padx=6)
        btn_limpiar = tk.Button(btn_frame, text="Limpiar", bg=_PRIMARY_DARK, fg="white", activebackground=_PRIMARY, command=self._limpiar_filtros, **style_btn)
        btn_limpiar.pack(side="left", padx=6)

        # ajustar pesos: hacer que la columna del nombre (3) sea la que se expanda
        controls.grid_columnconfigure(1, weight=0)   # fecha no se expande
        controls.grid_columnconfigure(3, weight=1)   # nombre expande
        controls.grid_columnconfigure(2, weight=0)

    # ------------------ Fecha: helpers robustos ------------------ #
    def _normalize_date_input(self, value):
        """Devuelve fecha 'YYYY-MM-DD' o None si es inválida."""
        if value in (None, "", "-", "--"):
            return ""
        # Si viene como date (tkcalendar.get_date)
        if isinstance(value, date):
            return value.strftime("%Y-%m-%d")
        s = str(value).strip()
        if not s:
            return ""
        # Reemplaza separadores comunes
        s = re.sub(r"[\\\.]", "-", s)
        s = s.replace("/", "-")
        # Prueba varios formatos
        fmts = ("%Y-%m-%d", "%d-%m-%Y", "%m-%d-%Y", "%Y/%m/%d", "%d/%m/%Y", "%m/%d/%Y")
        for f in fmts:
            try:
                dt = datetime.strptime(s, f)
                return dt.strftime("%Y-%m-%d")
            except Exception:
                continue
        return None

    def _sync_date_string(self):
        """Valida/normaliza lo escrito en el control de fecha."""
        raw = None
        try:
            if DateEntry is not None and isinstance(self.fecha_entry, DateEntry):
                # Preferir el texto mostrado para respetar edición manual
                raw = self.fecha_var.get() or self.fecha_entry.get()
            else:
                raw = self.fecha_var.get()
        except Exception:
            raw = ""
        norm = self._normalize_date_input(raw)
        if norm is None:
            # Valor inválido: limpiar pero no romper
            self.parent.bell()
            messagebox.showwarning("Fecha inválida", "Usa un formato válido (YYYY-MM-DD).")
            self.fecha_var.set("")
        else:
            self.fecha_var.set(norm or "")

    def _create_table(self):
        self.tabla_historial_frame = tk.Frame(self.historial_table_frame, bg=_BG)
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
        # Toma la fecha normalizada; si inválida, no filtra por fecha
        self._sync_date_string()
        fecha = self.fecha_var.get() if hasattr(self, 'fecha_var') else ""
        usuario_filtro = getattr(self, 'usuario_filtro_var', tk.StringVar()).get() if hasattr(self, 'usuario_filtro_var') else ""

        try:
            historial = fetch_historial(role=getattr(self.parent, 'rol', 'usuario'), get_usuario_id=getattr(self.parent, 'get_usuario_id', None))
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar el historial: {e}")
            historial = []

        filtrado = filter_historial(historial, nombre=nombre, fecha=fecha, usuario_filter=usuario_filtro)

        # Encabezados según rol
        admin = getattr(self.parent, 'rol', '') == "admin"
        if admin:
            headers = ["ID", "Nombre", "Descripción", "Fecha", "Hora", "Usuario ID", "Usuario", "Acciones"]
            #             0      1         2             3        4        5            6          7
            weights =  [0,     1,        3,            0,       0,       0,           1,         0]
            minsizes = [70,   220,      520,          110,      90,      90,         160,       220]
        else:
            headers = ["ID", "Nombre", "Descripción", "Fecha", "Hora", "Acciones"]
            #             0      1         2             3        4        5
            weights =  [0,     1,        3,            0,       0,       0]
            minsizes = [70,   240,      560,          110,      90,     220]

        # Contenedor de la tabla (un solo grid para cabecera y filas)
        table = tk.Frame(self.tabla_historial_frame, bg=_BG)
        table.pack(fill="both", expand=True, padx=2, pady=(2, 10))

        # Configurar columnas del grid
        for col, (w, m) in enumerate(zip(weights, minsizes)):
            table.grid_columnconfigure(col, weight=w, minsize=m)

        # Fila encabezado
        for col, h in enumerate(headers):
            lbl = tk.Label(table, text=h, bg=_PRIMARY, fg="white", font=("Segoe UI", 10, "bold"), padx=8, pady=8)
            lbl.grid(row=0, column=col, sticky="nsew", padx=1, pady=(0, 1))

        if not filtrado:
            no_data_label = tk.Label(
                table,
                text="No se encontraron registros.",
                font=("Segoe UI", 11),
                fg=_TEXT,
                bg=_BG,
                pady=20
            )
            # Colocar ocupando todas las columnas
            no_data_label.grid(row=1, column=0, columnspan=len(headers), sticky="nsew")
            return

        # Crear filas (una por registro)
        desc_labels = []  # para ajustar wraplength después
        for r, item in enumerate(filtrado, start=1):
            try:
                Id, Nombre, Descripcion, Fecha, Hora, UsuarioId, Archivo = item[:7]
            except Exception:
                continue

            # celdas comunes
            tk.Label(table, text=str(Id), bg=_BG, fg=_TEXT, font=("Segoe UI", 10), anchor="w").grid(row=r, column=0, sticky="nsew", padx=8, pady=6)
            tk.Label(table, text=str(Nombre), bg=_BG, fg=_TEXT, font=("Segoe UI", 10), anchor="w").grid(row=r, column=1, sticky="nsew", padx=8, pady=6)

            lbl_desc = tk.Label(table, text=str(Descripcion), bg=_BG, fg=_TEXT, font=("Segoe UI", 10),
                                anchor="w", justify="left", wraplength=minsizes[2]-24)
            lbl_desc.grid(row=r, column=2, sticky="nsew", padx=8, pady=6)
            desc_labels.append(lbl_desc)

            tk.Label(table, text=str(Fecha), bg=_BG, fg=_TEXT, font=("Segoe UI", 10), anchor="w").grid(row=r, column=3, sticky="nsew", padx=8, pady=6)
            tk.Label(table, text=str(Hora),  bg=_BG, fg=_TEXT, font=("Segoe UI", 10), anchor="w").grid(row=r, column=4, sticky="nsew", padx=8, pady=6)

            col_idx = 5
            if admin:
                tk.Label(table, text=str(UsuarioId), bg=_BG, fg=_TEXT, font=("Segoe UI", 10), anchor="w").grid(row=r, column=5, sticky="nsew", padx=8, pady=6)
                try:
                    username = get_username_by_id(UsuarioId)
                except Exception:
                    username = "-"
                tk.Label(table, text=username, bg=_BG, fg=_TEXT, font=("Segoe UI", 10), anchor="w").grid(row=r, column=6, sticky="nsew", padx=8, pady=6)
                col_idx = 7

            # Acciones
            actions = tk.Frame(table, bg=_BG)
            actions.grid(row=r, column=col_idx, sticky="e", padx=8, pady=6)

            eye_icon = self._load_icon('eye.jpg')
            if Archivo:
                btn_prev = tk.Button(
                    actions,
                    image=eye_icon if eye_icon else None,
                    text="Preview" if not eye_icon else "",
                    compound="left",
                    bg=_PRIMARY, fg="white", activebackground=_PRIMARY_DARK,
                    bd=0, cursor="hand2",
                    command=lambda archivo=Archivo, nombre=Nombre: self._preview_archivo(archivo, nombre)
                )
            else:
                btn_prev = tk.Button(actions, text="Preview", state="disabled", bg="#cccccc", fg="#666666", bd=0)
            btn_prev.pack(side="left", padx=4)

            tk.Button(actions, text="Descargar", bg=_PRIMARY_DARK, fg="white", activebackground=_PRIMARY,
                      bd=0, cursor="hand2",
                      command=lambda archivo=Archivo, nombre=Nombre: self._descargar_archivo(archivo, nombre)).pack(side="left", padx=4)

            can_delete = False
            if admin:
                can_delete = True
            else:
                current_user_id = self.parent.get_usuario_id() if hasattr(self.parent, 'get_usuario_id') else None
                can_delete = (current_user_id == UsuarioId)

            if can_delete:
                tk.Button(actions, text="Eliminar", bg=_PRIMARY, fg="white", activebackground=_PRIMARY_DARK,
                          bd=0, cursor="hand2",
                          command=lambda id_hist=Id: self._eliminar_registro(id_hist)).pack(side="left", padx=6)
            else:
                tk.Button(actions, text="Eliminar", bg="#cccccc", fg="#666666", bd=0, state="disabled").pack(side="left", padx=6)

        # Ajustar el wraplength de la descripción al ancho real de su celda
        def _adjust_wrap(_=None):
            for lbl in desc_labels:
                try:
                    lbl.configure(wraplength=max(200, lbl.winfo_width()-16))
                except Exception:
                    pass
        table.bind("<Configure>", _adjust_wrap)

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

    def _preview_archivo(self, archivo_bin, nombre):
        """Muestra una ventana emergente con la vista previa del PDF dentro de la aplicación.

        Requiere PyMuPDF (fitz). Si no está instalado, muestra instrucción.
        Sólo lectura; convierte cada página a imagen y permite navegar.
        """
        if not archivo_bin:
            messagebox.showwarning("Advertencia", "No hay archivo para previsualizar.")
            return
        # Crear ventana emergente
        preview_win = tk.Toplevel(self.parent)
        preview_win.title(f"Preview PDF - {nombre}")
        preview_win.configure(bg=_BG)
        preview_win.geometry("800x600")
        preview_win.transient(self.parent.winfo_toplevel())
        preview_win.grab_set()

        header = tk.Frame(preview_win, bg=_BG)
        header.pack(fill="x", pady=4)
        tk.Label(header, text=f"Vista previa: {nombre}", font=("Segoe UI", 12, "bold"), bg=_BG, fg=_PRIMARY).pack(side="left", padx=10)
        status_var = tk.StringVar(value="Cargando PDF...")
        status_lbl = tk.Label(header, textvariable=status_var, bg=_BG, fg=_TEXT, font=("Segoe UI", 9))
        status_lbl.pack(side="right", padx=10)

        nav_frame = tk.Frame(preview_win, bg=_BG)
        nav_frame.pack(fill="x", pady=(0,4))
        btn_prev = tk.Button(nav_frame, text="◀", width=4, state="disabled")
        btn_next = tk.Button(nav_frame, text="▶", width=4, state="disabled")
        page_info_var = tk.StringVar(value="Página 0 / 0")
        page_info_lbl = tk.Label(nav_frame, textvariable=page_info_var, bg=_BG, fg=_TEXT, font=("Segoe UI", 9))
        btn_prev.pack(side="left", padx=6)
        btn_next.pack(side="left")
        page_info_lbl.pack(side="left", padx=12)

        # Contenedor scroll
        canvas_frame = tk.Frame(preview_win, bg=_BG)
        canvas_frame.pack(fill="both", expand=True)
        canvas = tk.Canvas(canvas_frame, bg=_BG, highlightthickness=0)
        vbar = tk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)
        hbar = tk.Scrollbar(canvas_frame, orient="horizontal", command=canvas.xview)
        canvas.configure(yscrollcommand=vbar.set, xscrollcommand=hbar.set)
        vbar.pack(side="right", fill="y")
        hbar.pack(side="bottom", fill="x")
        canvas.pack(side="left", fill="both", expand=True)

        inner = tk.Frame(canvas, bg=_BG)
        win_id = canvas.create_window((0,0), window=inner, anchor="nw")
        def _sync_scroll(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
        inner.bind("<Configure>", _sync_scroll)
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(win_id, width=max(e.width, inner.winfo_reqwidth())))

        img_label = tk.Label(inner, bg=_BG)
        img_label.pack(padx=10, pady=10)

        # Botón para guardar directamente desde preview
        action_frame = tk.Frame(preview_win, bg=_BG)
        action_frame.pack(fill="x", pady=(4,8))
        def _guardar_desde_preview():
            suggested = get_suggested_filename(nombre, archivo_bin)
            desktop = os.path.join(os.path.expanduser("~"), "Desktop")
            if not os.path.exists(desktop):
                desktop = os.path.expanduser("~")
            file_path = filedialog.asksaveasfilename(
                title="Guardar PDF",
                initialfile=suggested,
                initialdir=desktop,
                defaultextension=".pdf",
                filetypes=[("PDF","*.pdf")]
            )
            if file_path:
                try:
                    save_binary_to_path(archivo_bin, file_path)
                    messagebox.showinfo("Éxito", f"Archivo guardado:\n{file_path}")
                except Exception as e:
                    messagebox.showerror("Error", f"No se pudo guardar: {e}")
        tk.Button(action_frame, text="Guardar PDF...", bg=_PRIMARY, fg="white", activebackground=_PRIMARY_DARK, bd=0, cursor="hand2", command=_guardar_desde_preview).pack(side="left", padx=10)
        tk.Button(action_frame, text="Cerrar", bg=_PRIMARY_DARK, fg="white", activebackground=_PRIMARY, bd=0, cursor="hand2", command=preview_win.destroy).pack(side="right", padx=10)

        # Lógica de renderizado
        pil_pages = []          # PIL Images de todas las páginas
        photos_cache = {}       # cache por (idx, width) para evitar GC y reprocesos
        current_page = {"index": 0}

        def _render_page(idx):
            if not pil_pages:
                return
            idx = max(0, min(idx, len(pil_pages)-1))
            current_page["index"] = idx
            pil_img = pil_pages[idx]
            max_width = max(200, canvas.winfo_width() - 40)
            key = (idx, max_width)
            if key not in photos_cache:
                ratio = min(1.0, max_width / pil_img.width)
                disp = pil_img if ratio >= 1.0 else pil_img.resize(
                    (int(pil_img.width*ratio), int(pil_img.height*ratio)), Image.LANCZOS)
                photos_cache[key] = ImageTk.PhotoImage(disp)
            photo = photos_cache[key]
            img_label.configure(image=photo)
            img_label.image = photo
            page_info_var.set(f"Página {idx+1} / {len(pil_pages)}")
            btn_prev.configure(state=("normal" if idx > 0 else "disabled"))
            btn_next.configure(state=("normal" if idx < len(pil_pages)-1 else "disabled"))
            status_var.set("Listo")

        def _go_prev():
            _render_page(current_page["index"] - 1)
        def _go_next():
            _render_page(current_page["index"] + 1)
        btn_prev.configure(command=_go_prev)
        btn_next.configure(command=_go_next)
        preview_win.bind("<Left>", lambda e: _go_prev())
        preview_win.bind("<Right>", lambda e: _go_next())

        def _load_pdf():
            try:
                import fitz  # PyMuPDF
            except ImportError:
                status_var.set("PyMuPDF no instalado")
                info = tk.Label(inner, text="PyMuPDF (fitz) no está instalado.\nInstale: pip install PyMuPDF", bg=_BG, fg=_TEXT, font=("Segoe UI", 10), justify="left")
                info.pack(pady=20)
                return
            try:
                doc = fitz.open(stream=bytes(archivo_bin), filetype="pdf")
                pages = getattr(doc, "page_count", 0)
                if pages == 0:
                    status_var.set("PDF vacío")
                    return
                zoom = 1.25
                mat = fitz.Matrix(zoom, zoom)
                for i in range(pages):
                    pg = doc.load_page(i)
                    pix = pg.get_pixmap(matrix=mat, alpha=False)
                    pil = Image.open(BytesIO(pix.tobytes("ppm")))
                    pil.load()
                    pil_pages.append(pil)
                doc.close()
                status_var.set("Renderizando...")
                _render_page(0)
            except Exception as e:
                status_var.set("Error")
                messagebox.showerror("Error", f"No se pudo renderizar el PDF: {e}")

        # Redibujar a nuevo tamaño de canvas
        def _on_resize(_e=None):
            photos_cache.clear()
            _render_page(current_page["index"])
        canvas.bind("<Configure>", lambda e: (_on_resize()))

        # Cargar PDF después de que la ventana se muestre (dimensiones correctas)
        preview_win.after(100, _load_pdf)