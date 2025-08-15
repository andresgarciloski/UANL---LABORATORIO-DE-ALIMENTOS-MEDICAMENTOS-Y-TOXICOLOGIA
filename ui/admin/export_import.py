import tkinter as tk
from tkinter import messagebox, filedialog
from ui.base_interface import bind_mousewheel
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
        """Mostrar sección de exportar/importar (UI solamente) — filtros integrados en Exportar."""
        for widget in self.parent.content_frame.winfo_children():
            try:
                widget.destroy()
            except:
                pass

        main_frame = tk.Frame(self.parent.content_frame, bg="white")
        main_frame.pack(fill="both", expand=True, padx=30, pady=20)

        canvas = tk.Canvas(main_frame, bg="white", highlightthickness=0)
        scrollbar = tk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        scrollable_frame = tk.Frame(canvas, bg="white")
        window_id = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

        def resize_inner_frame(event):
            canvas.itemconfig(window_id, width=event.width)
            canvas.configure(scrollregion=canvas.bbox("all"))
        canvas.bind("<Configure>", resize_inner_frame)

        bind_mousewheel(scrollable_frame, canvas)

        title_label = tk.Label(
            scrollable_frame,
            text="Exportar / Importar Base de Datos",
            font=("Segoe UI", 18, "bold"),
            fg="#0B5394",
            bg="white"
        )
        title_label.pack(pady=(0, 20))

        # ----------------- EXPORT FRAME (ahora contiene filtros) -----------------
        export_frame = tk.LabelFrame(
            scrollable_frame,
            text="Exportar Datos (aplica filtros abajo)",
            font=("Segoe UI", 14, "bold"),
            fg="#0B5394",
            bg="white",
            padx=16,
            pady=12
        )
        export_frame.pack(fill="x", pady=(0, 18), padx=4)

        # Row 0: descripción
        export_desc = tk.Label(
            export_frame,
            text="Exporta registros del historial a un archivo ZIP. Usa los filtros para limitar el conjunto.",
            font=("Segoe UI", 11),
            bg="white",
            wraplength=900,
            justify="left"
        )
        export_desc.grid(row=0, column=0, columnspan=4, sticky="w", pady=(0,8))

        # FILTROS (integrados en export_frame)
        lbl_from = tk.Label(export_frame, text="Fecha inicio", bg="white")
        lbl_from.grid(row=1, column=0, sticky="w", padx=(2,6), pady=6)
        if _HAVE_DATEENTRY:
            self.entry_from = DateEntry(export_frame, date_pattern="yyyy-mm-dd")
        else:
            self.entry_from = tk.Entry(export_frame)
        self.entry_from.grid(row=1, column=1, padx=6, pady=6, sticky="we")

        lbl_to = tk.Label(export_frame, text="Fecha fin", bg="white")
        lbl_to.grid(row=1, column=2, sticky="w", padx=(12,6), pady=6)
        if _HAVE_DATEENTRY:
            self.entry_to = DateEntry(export_frame, date_pattern="yyyy-mm-dd")
        else:
            self.entry_to = tk.Entry(export_frame)
        self.entry_to.grid(row=1, column=3, padx=6, pady=6, sticky="we")

        lbl_name = tk.Label(export_frame, text="Nombre contiene", bg="white")
        lbl_name.grid(row=2, column=0, sticky="w", padx=(2,6), pady=6)
        self.entry_name = tk.Entry(export_frame)
        self.entry_name.grid(row=2, column=1, padx=6, pady=6, sticky="we")

        lbl_user = tk.Label(export_frame, text="Usuario ID", bg="white")
        lbl_user.grid(row=2, column=2, sticky="w", padx=(12,6), pady=6)
        self.entry_user = tk.Entry(export_frame)
        self.entry_user.grid(row=2, column=3, padx=6, pady=6, sticky="we")

        # configurar pesos para que las columnas se expandan
        for c in range(4):
            export_frame.grid_columnconfigure(c, weight=1)

        # botones: previsualizar, limpiar, exportar
        btn_frame = tk.Frame(export_frame, bg="white")
        btn_frame.grid(row=3, column=0, columnspan=4, pady=(10,0))

        preview_btn = tk.Button(btn_frame, text="Previsualizar", command=self.previsualizar_export, bg="#f0ad4e")
        preview_btn.pack(side="left", padx=6)

        clear_btn = tk.Button(btn_frame, text="Limpiar filtros", command=self._limpiar_filtros)
        clear_btn.pack(side="left", padx=6)

        export_btn = tk.Button(btn_frame, text="Exportar (filtrada)", command=self.exportar_excel, bg="#0B5394", fg="white")
        export_btn.pack(side="left", padx=12)

        # etiqueta de estado/preview
        self.preview_status_lbl = tk.Label(export_frame, text="", bg="white", fg="#333", anchor="w", justify="left")
        self.preview_status_lbl.grid(row=4, column=0, columnspan=4, sticky="we", pady=(10,0))

        # ----------------- IMPORT FRAME (separado) -----------------
        import_frame = tk.LabelFrame(
            scrollable_frame,
            text="Importar Datos",
            font=("Segoe UI", 14, "bold"),
            fg="#0B5394",
            bg="white",
            padx=16,
            pady=12
        )
        import_frame.pack(fill="x", pady=(0, 10), padx=4)

        import_desc = tk.Label(
            import_frame,
            text="Importa registros desde un archivo ZIP exportado anteriormente.",
            font=("Segoe UI", 11),
            bg="white",
            wraplength=900,
            justify="left"
        )
        import_desc.pack(anchor="w", pady=(0,8))

        import_btn = tk.Button(
            import_frame,
            text="Importar Base de Datos",
            font=("Segoe UI", 12, "bold"),
            bg="#28a745",
            fg="white",
            relief="flat",
            padx=20,
            pady=8,
            cursor="hand2",
            command=self.importar_excel
        )
        import_btn.pack(anchor="w")

    def _limpiar_filtros(self):
        self.entry_from.delete(0, "end")
        self.entry_to.delete(0, "end")
        self.entry_name.delete(0, "end")
        self.entry_user.delete(0, "end")

    def _leer_filtros(self):
        start_date = self.entry_from.get().strip() or None
        end_date = self.entry_to.get().strip() or None
        name_contains = self.entry_name.get().strip() or None
        user_id = self.entry_user.get().strip() or None
        return start_date, end_date, name_contains, user_id

    def previsualizar_export(self):
        """Muestra cuántos registros se exportarían y algunas filas de ejemplo."""
        try:
            start_date, end_date, name_contains, user_id = self._leer_filtros()
            preview = db_exporter.get_export_preview(start_date=start_date, end_date=end_date, name_contains=name_contains, user_id=user_id, sample_rows=10)
            msg = f"Registros que coinciden: {preview['count']}\n\nEjemplo de filas:\n"
            for r in preview["sample"]:
                msg += f"- {r.get('Id')} | {r.get('Nombre')} | {r.get('Fecha')} | Usuario: {r.get('UsuarioId')}\n"
            messagebox.showinfo("Previsualizar exportación", msg)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo previsualizar: {e}")

    def exportar_excel(self):
        """UI handler: pide ruta y llama a core.db_exporter.export_database_to_zip con filtros"""
        try:
            start_date, end_date, name_contains, user_id = self._leer_filtros()
            now = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            default_filename = f"export_filtrado_{now}.zip"
            file_path = filedialog.asksaveasfilename(
                defaultextension=".zip",
                filetypes=[("Archivo ZIP", "*.zip")],
                title="Guardar como",
                initialfile=default_filename
            )
            if not file_path:
                return
            resultado = db_exporter.export_database_to_zip(file_path, start_date=start_date, end_date=end_date, name_contains=name_contains, user_id=user_id)
            messagebox.showinfo("Exportar", f"Exportación completa exitosa:\n{resultado['path']}\n\nRegistros: {resultado['registros']}\nArchivos: {resultado['archivos']}")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo exportar: {e}")

    def importar_excel(self):
        """UI handler: pide ZIP y llama a core.db_exporter.import_database_from_zip"""
        try:
            file_path = filedialog.askopenfilename(
                title="Seleccionar archivo ZIP",
                filetypes=[("Archivo ZIP", "*.zip")]
            )
            if not file_path:
                return
            if not messagebox.askyesno("Importar", "¿Estás seguro de que deseas importar estos datos?\nEsto puede sobrescribir registros existentes."):
                return
            resultado = db_exporter.import_database_from_zip(file_path)
            messagebox.showinfo("Importar", f"Importación exitosa:\n\nRegistros importados: {resultado['registros_importados']}\nArchivos importados: {resultado['archivos_importados']}")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo importar: {e}")