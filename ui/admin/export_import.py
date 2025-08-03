import tkinter as tk
from tkinter import messagebox, filedialog
import pandas as pd
import datetime
import zipfile
import io
from core.auth import obtener_historial, importar_registro
from ui.base_interface import bind_mousewheel

class ExportImportSection:
    def __init__(self, parent):
        self.parent = parent
        
    def show_export_import_section(self):
        """Mostrar sección de exportar/importar"""
        # Limpiar contenido anterior
        for widget in self.parent.content_frame.winfo_children():
            try:
                widget.destroy()
            except:
                pass

        # Frame principal con canvas y scroll
        main_frame = tk.Frame(self.parent.content_frame, bg="white")
        main_frame.pack(fill="both", expand=True, padx=40, pady=30)

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

        # Scroll solo cuando el mouse está sobre el área desplazable
        bind_mousewheel(scrollable_frame, canvas)

        # --- Pon los widgets dentro de scrollable_frame ---
        title_label = tk.Label(
            scrollable_frame,
            text="Exportar/Importar Base de Datos",
            font=("Segoe UI", 18, "bold"),
            fg="#0B5394",
            bg="white"
        )
        title_label.pack(pady=(0, 30))

        # Sección de Exportar
        export_frame = tk.LabelFrame(
            scrollable_frame,
            text="Exportar Datos",
            font=("Segoe UI", 14, "bold"),
            fg="#0B5394",
            bg="white",
            padx=20,
            pady=20
        )
        export_frame.pack(fill="x", pady=(0, 20))

        export_desc = tk.Label(
            export_frame,
            text="Exporta todos los registros del historial a un archivo ZIP",
            font=("Segoe UI", 11),
            bg="white"
        )
        export_desc.pack(pady=(0, 15))

        export_btn = tk.Button(
            export_frame,
            text="Exportar Base de Datos",
            font=("Segoe UI", 12, "bold"),
            bg="#0B5394",
            fg="white",
            relief="flat",
            padx=30,
            pady=10,
            cursor="hand2",
            command=self.exportar_excel
        )
        export_btn.pack()

        # Sección de Importar
        import_frame = tk.LabelFrame(
            scrollable_frame,
            text="Importar Datos",
            font=("Segoe UI", 14, "bold"),
            fg="#0B5394",
            bg="white",
            padx=20,
            pady=20
        )
        import_frame.pack(fill="x")

        import_desc = tk.Label(
            import_frame,
            text="Importa registros desde un archivo ZIP exportado anteriormente",
            font=("Segoe UI", 11),
            bg="white"
        )
        import_desc.pack(pady=(0, 15))

        import_btn = tk.Button(
            import_frame,
            text="Importar Base de Datos",
            font=("Segoe UI", 12, "bold"),
            bg="#28a745",
            fg="white",
            relief="flat",
            padx=30,
            pady=10,
            cursor="hand2",
            command=self.importar_excel
        )
        import_btn.pack()

    def exportar_excel(self):
        """Exportar datos completos"""
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
        """Importar datos desde ZIP"""
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
                        if pd.notna(row["ArchivoNombre"]) and row["ArchivoNombre"] != "":
                            try:
                                archivo_bin = zf.read(row["ArchivoNombre"])
                                archivos_importados += 1
                            except KeyError:
                                pass
                        
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
                        print(f"Error importando registro {row.get('Id', 'N/A')}: {e}")

            messagebox.showinfo("Importar", f"Importación exitosa:\n\nRegistros importados: {registros_importados}\nArchivos importados: {archivos_importados}")
            
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo importar: {e}")