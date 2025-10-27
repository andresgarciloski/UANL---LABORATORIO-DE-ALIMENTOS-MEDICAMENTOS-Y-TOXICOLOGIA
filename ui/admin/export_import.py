import tkinter as tk
from tkinter import messagebox, filedialog
from ui.base_interface import bind_mousewheel, _BG, _PRIMARY, _PRIMARY_DARK, _SURFACE, _TEXT, _TEXT_SECONDARY, _BORDER, _EMPHASIS, _ALERT, _SECONDARY
import core.db_exporter as db_exporter
import datetime

# Intentar usar DateEntry de tkcalendar para selectores de fecha (si está instalado)
try:
    from tkcalendar import DateEntry
    _HAVE_DATEENTRY = True
except Exception:
    DateEntry = None
    _HAVE_DATEENTRY = False

class ExportImportSection:
    def __init__(self, parent):
        self.parent = parent

    def show_export_import_section(self):
        """Mostrar sección de exportar/importar (UI modernizada con filtros y validación)."""
        for widget in self.parent.content_frame.winfo_children():
            try:
                widget.destroy()
            except:
                pass

        # Contenedor principal
        main_frame = tk.Frame(self.parent.content_frame, bg=_BG)
        main_frame.pack(fill="both", expand=True, padx=24, pady=16)

        # Canvas + Scrollbar
        canvas = tk.Canvas(main_frame, bg=_BG, highlightthickness=0)
        scrollbar = tk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)  # FIX: vincular la barra con el canvas
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        scrollable_frame = tk.Frame(canvas, bg=_BG)
        window_id = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

        def resize_inner_frame(event):
            canvas.itemconfig(window_id, width=event.width)
            canvas.configure(scrollregion=canvas.bbox("all"))
        canvas.bind("<Configure>", resize_inner_frame)

        bind_mousewheel(scrollable_frame, canvas)

        # Título
        title_label = tk.Label(
            scrollable_frame,
            text="Exportar / Importar Base de Datos",
            font=("Segoe UI", 18, "bold"),
            fg=_PRIMARY_DARK,
            bg=_BG
        )
        title_label.pack(pady=(0, 16), anchor="w")

        # ----- Tarjeta de Exportación -----
        export_frame = tk.Frame(scrollable_frame, bg=_SURFACE, bd=0, highlightthickness=1, highlightbackground=_BORDER)
        export_frame.pack(fill="x", pady=(0, 16))

        header_export = tk.Label(
            export_frame,
            text="Exportar datos",
            font=("Segoe UI", 14, "bold"),
            fg=_PRIMARY_DARK,
            bg=_SURFACE
        )
        header_export.pack(anchor="w", padx=16, pady=(14, 2))

        export_desc = tk.Label(
            export_frame,
            text="Exporta registros a un archivo ZIP aplicando filtros de fecha, nombre y usuario.",
            font=("Segoe UI", 10),
            fg=_TEXT_SECONDARY,
            bg=_SURFACE,
            wraplength=900,
            justify="left"
        )
        export_desc.pack(anchor="w", padx=16, pady=(0, 8))

        # Zona de filtros
        filters = tk.Frame(export_frame, bg=_SURFACE)
        filters.pack(fill="x", padx=16, pady=(4, 8))

        # Helper: crear label de filtro
        def flabel(parent, text):
            return tk.Label(parent, text=text, bg=_SURFACE, fg=_TEXT, font=("Segoe UI", 10, "bold"))

        # Fila 1
        flabel(filters, "Fecha inicio").grid(row=0, column=0, sticky="w", padx=(0, 6), pady=(4, 2))
        if _HAVE_DATEENTRY:
            self.entry_from = DateEntry(filters, date_pattern="yyyy-mm-dd")
        else:
            self.entry_from = tk.Entry(filters)
            self.entry_from.insert(0, "YYYY-MM-DD")
        self.entry_from.grid(row=1, column=0, sticky="we", padx=(0, 12), pady=(0, 6))

        flabel(filters, "Fecha fin").grid(row=0, column=1, sticky="w", padx=(0, 6), pady=(4, 2))
        if _HAVE_DATEENTRY:
            self.entry_to = DateEntry(filters, date_pattern="yyyy-mm-dd")
        else:
            self.entry_to = tk.Entry(filters)
            self.entry_to.insert(0, "YYYY-MM-DD")
        self.entry_to.grid(row=1, column=1, sticky="we", padx=(0, 12), pady=(0, 6))

        flabel(filters, "Nombre contiene").grid(row=0, column=2, sticky="w", padx=(0, 6), pady=(4, 2))
        self.entry_name = tk.Entry(filters)
        self.entry_name.grid(row=1, column=2, sticky="we", padx=(0, 12), pady=(0, 6))

        flabel(filters, "Usuario ID").grid(row=0, column=3, sticky="w", padx=(0, 6), pady=(4, 2))
        self.entry_user = tk.Entry(filters)
        self.entry_user.grid(row=1, column=3, sticky="we", padx=(0, 0), pady=(0, 6))

        for c in range(4):
            filters.grid_columnconfigure(c, weight=1)

        # Botones
        btn_frame = tk.Frame(export_frame, bg=_SURFACE)
        btn_frame.pack(anchor="w", padx=16, pady=(6, 8))

        def make_btn(parent, text, cmd, bg, fg="white"):
            return tk.Button(
                parent, text=text, command=cmd,
                bg=bg, fg=fg, activebackground=bg, activeforeground=fg,
                relief="flat", bd=0, padx=14, pady=8, cursor="hand2",
                font=("Segoe UI", 10, "bold")
            )

        preview_btn = make_btn(btn_frame, "Previsualizar", self.previsualizar_export, _SECONDARY)
        preview_btn.pack(side="left", padx=(0, 8))

        clear_btn = tk.Button(
            btn_frame, text="Limpiar filtros", command=self._limpiar_filtros,
            bg=_EMPHASIS, fg=_PRIMARY_DARK, activebackground=_EMPHASIS, activeforeground=_PRIMARY_DARK,
            relief="flat", bd=0, padx=14, pady=8, cursor="hand2", font=("Segoe UI", 10, "bold")
        )
        clear_btn.pack(side="left", padx=(0, 8))

        export_btn = make_btn(btn_frame, "Exportar", self.exportar_excel, _PRIMARY)
        export_btn.pack(side="left", padx=(4, 0))

        # Estado/preview
        status_wrap = tk.Frame(export_frame, bg=_SURFACE)
        status_wrap.pack(fill="x", padx=16, pady=(4, 14))
        self.preview_status_lbl = tk.Label(
            status_wrap, text="",
            bg=_SURFACE, fg=_TEXT_SECONDARY, anchor="w", justify="left", font=("Segoe UI", 9)
        )
        self.preview_status_lbl.pack(fill="x")

        # ----- Tarjeta de Importación -----
        import_frame = tk.Frame(scrollable_frame, bg=_SURFACE, bd=0, highlightthickness=1, highlightbackground=_BORDER)
        import_frame.pack(fill="x", pady=(0, 8))

        header_import = tk.Label(
            import_frame,
            text="Importar datos",
            font=("Segoe UI", 14, "bold"),
            fg=_PRIMARY_DARK,
            bg=_SURFACE
        )
        header_import.pack(anchor="w", padx=16, pady=(14, 2))

        import_desc = tk.Label(
            import_frame,
            text="Importa registros desde un archivo ZIP exportado anteriormente.",
            font=("Segoe UI", 10),
            fg=_TEXT_SECONDARY,
            bg=_SURFACE,
            wraplength=900,
            justify="left"
        )
        import_desc.pack(anchor="w", padx=16, pady=(0, 8))

        import_btn = tk.Button(
            import_frame,
            text="Importar base de datos",
            font=("Segoe UI", 10, "bold"),
            bg=_PRIMARY, fg="white",
            relief="flat", bd=0, padx=16, pady=10,
            activebackground=_PRIMARY, activeforeground="white",
            cursor="hand2",
            command=self.importar_excel
        )
        import_btn.pack(anchor="w", padx=16, pady=(0, 16))

    def _limpiar_filtros(self):
        self.entry_from.delete(0, "end")
        self.entry_to.delete(0, "end")
        self.entry_name.delete(0, "end")
        self.entry_user.delete(0, "end")
        self.preview_status_lbl.configure(text="")

    # --- Utilidades de validación y lectura ---
    def _parse_date(self, s):
        """Acepta 'YYYY-MM-DD', 'DD/MM/YYYY' o 'DD-MM-YYYY'. Devuelve 'YYYY-MM-DD' o None."""
        if not s:
            return None
        s = s.strip()
        if not s or s.upper() == "YYYY-MM-DD":
            return None
        fmts = ["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"]
        for f in fmts:
            try:
                return datetime.datetime.strptime(s, f).strftime("%Y-%m-%d")
            except Exception:
                continue
        raise ValueError(f"Fecha inválida: {s}. Usa formato YYYY-MM-DD.")

    def _leer_filtros(self):
        start_raw = self.entry_from.get().strip() if self.entry_from else ""
        end_raw = self.entry_to.get().strip() if self.entry_to else ""
        name_contains = self.entry_name.get().strip() or None
        user_raw = self.entry_user.get().strip()

        start_date = self._parse_date(start_raw)
        end_date = self._parse_date(end_raw)

        if start_date and end_date:
            if start_date > end_date:
                raise ValueError("La fecha inicio no puede ser mayor que la fecha fin.")

        user_id = None
        if user_raw:
            if not user_raw.isdigit():
                raise ValueError("Usuario ID debe ser numérico.")
            user_id = int(user_raw)

        return start_date, end_date, name_contains, user_id

    # --- Acciones ---
    def previsualizar_export(self):
        """Muestra cuántos registros coinciden y un muestreo en la etiqueta de estado."""
        try:
            # Validar disponibilidad de funciones
            for fn in ("get_export_preview",):
                if not hasattr(db_exporter, fn):
                    raise RuntimeError("Falta implementación en core.db_exporter: " + fn)

            start_date, end_date, name_contains, user_id = self._leer_filtros()
            preview = db_exporter.get_export_preview(
                start_date=start_date,
                end_date=end_date,
                name_contains=name_contains,
                user_id=user_id,
                sample_rows=8
            )

            count = preview.get("count", 0)
            sample = preview.get("sample", [])
            if not isinstance(sample, (list, tuple)):
                sample = []

            lines = [f"Registros que coinciden: {count}"]
            if sample:
                lines.append("")
                lines.append("Ejemplos:")
                for r in sample:
                    # tolerante a variantes de claves
                    rid = r.get("Id") or r.get("id") or r.get("ID")
                    nombre = r.get("Nombre") or r.get("nombre") or r.get("Name")
                    fecha = r.get("Fecha") or r.get("fecha") or r.get("date")
                    usr = r.get("UsuarioId") or r.get("usuario_id") or r.get("user_id")
                    lines.append(f"• {rid} | {nombre} | {fecha} | Usuario: {usr}")
            text = "\n".join(lines)
            self.preview_status_lbl.configure(text=text, fg=_TEXT_SECONDARY)
            if count == 0:
                messagebox.showinfo("Previsualizar", "No hay registros que coincidan con los filtros.")
        except Exception as e:
            self.preview_status_lbl.configure(text=f"Error: {e}", fg=_ALERT)
            messagebox.showerror("Error", f"No se pudo previsualizar: {e}")

    def exportar_excel(self):
        """Pide ruta y llama a export_database_to_zip con filtros (ZIP)."""
        try:
            if not hasattr(db_exporter, "export_database_to_zip"):
                raise RuntimeError("Falta implementación en core.db_exporter: export_database_to_zip")

            start_date, end_date, name_contains, user_id = self._leer_filtros()

            now = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            default_filename = f"export_filtrado_{now}.zip"

            # Sugerir escritorio del usuario en Windows
            try:
                import os
                initialdir = os.path.join(os.path.expanduser("~"), "Desktop")
            except Exception:
                initialdir = ""

            file_path = filedialog.asksaveasfilename(
                defaultextension=".zip",
                filetypes=[("Archivo ZIP", "*.zip")],
                title="Guardar exportación como",
                initialfile=default_filename,
                initialdir=initialdir
            )
            if not file_path:
                return

            resultado = db_exporter.export_database_to_zip(
                file_path,
                start_date=start_date,
                end_date=end_date,
                name_contains=name_contains,
                user_id=user_id
            )

            reg = resultado.get("registros", 0)
            arc = resultado.get("archivos", 0)
            path = resultado.get("path", file_path)
            self.preview_status_lbl.configure(
                text=f"Exportación realizada.\nRuta: {path}\nRegistros: {reg} | Archivos: {arc}",
                fg=_TEXT
            )
            messagebox.showinfo("Exportar", f"Exportación exitosa:\n\nRuta: {path}\nRegistros: {reg}\nArchivos: {arc}")
        except Exception as e:
            self.preview_status_lbl.configure(text=f"Error: {e}", fg=_ALERT)
            messagebox.showerror("Error", f"No se pudo exportar: {e}")

    def importar_excel(self):
        """Pide ZIP y llama a import_database_from_zip."""
        try:
            if not hasattr(db_exporter, "import_database_from_zip"):
                raise RuntimeError("Falta implementación en core.db_exporter: import_database_from_zip")

            file_path = filedialog.askopenfilename(
                title="Seleccionar archivo ZIP",
                filetypes=[("Archivo ZIP", "*.zip")]
            )
            if not file_path:
                return
            if not messagebox.askyesno("Importar", "¿Deseas importar estos datos?\nEsto puede sobrescribir registros existentes."):
                return

            resultado = db_exporter.import_database_from_zip(file_path)
            reg = resultado.get("registros_importados", 0)
            arc = resultado.get("archivos_importados", 0)

            messagebox.showinfo("Importar", f"Importación exitosa:\n\nRegistros importados: {reg}\nArchivos importados: {arc}")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo importar: {e}")