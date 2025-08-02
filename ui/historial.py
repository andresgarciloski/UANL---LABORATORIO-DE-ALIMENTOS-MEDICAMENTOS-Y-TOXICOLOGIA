import tkinter as tk
from tkinter import messagebox, filedialog
from PIL import Image, ImageTk
from tkcalendar import DateEntry
import os
from ui.base_interface import bind_mousewheel

class HistorialModule:
    def __init__(self, parent_window):
        self.parent = parent_window

    def show_historial_section(self):
        """Mostrar sección de historial"""
        # Limpiar contenido anterior
        for widget in self.parent.content_frame.winfo_children():
            try:
                widget.destroy()
            except:
                pass

        # Canvas y Scrollbar
        main_canvas = tk.Canvas(self.parent.content_frame, bg="white")
        main_scrollbar = tk.Scrollbar(self.parent.content_frame, orient="vertical", command=main_canvas.yview)
        self.historial_table_frame = tk.Frame(main_canvas, bg="white")

        self.historial_table_frame.bind(
            "<Configure>",
            lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all"))
        )

        main_canvas.create_window((0, 0), window=self.historial_table_frame, anchor="nw")
        main_canvas.configure(yscrollcommand=main_scrollbar.set)

        # Filtros
        self._create_filters()
        
        # Tabla
        self._create_table()

        # Empaquetar
        main_canvas.pack(side="left", fill="both", expand=True)
        main_scrollbar.pack(side="right", fill="y")
        bind_mousewheel(main_canvas, main_canvas)

        self._actualizar_tabla_historial_filtrada()

    def _create_filters(self):
        """Crear filtros de búsqueda"""
        filtro_frame = tk.Frame(self.historial_table_frame, bg="white")
        filtro_frame.grid(row=0, column=0, columnspan=10, sticky="ew", pady=(20, 10), padx=30)
        self.historial_table_frame.grid_rowconfigure(0, weight=0)
        self.historial_table_frame.grid_columnconfigure(0, weight=1)

        # Título para admin
        if hasattr(self.parent, 'rol') and self.parent.rol == "admin":
            title_label = tk.Label(
                filtro_frame, 
                text="📊 Historial General (Todos los usuarios)", 
                font=("Segoe UI", 14, "bold"), 
                fg="#0B5394", 
                bg="white"
            )
            title_label.pack(pady=(0, 10))
        else:
            title_label = tk.Label(
                filtro_frame, 
                text=f"📊 Mi Historial Personal ({self.parent.username})", 
                font=("Segoe UI", 14, "bold"), 
                fg="#0B5394", 
                bg="white"
            )
            title_label.pack(pady=(0, 10))

        # Frame para controles de filtro
        controls_frame = tk.Frame(filtro_frame, bg="white")
        controls_frame.pack()

        # Inicializar variables si no existen
        if not hasattr(self, 'nombre_var'):
            self.nombre_var = tk.StringVar()
        if not hasattr(self, 'fecha_var'):
            self.fecha_var = tk.StringVar()

        tk.Label(controls_frame, text="Nombre:", bg="white", font=("Segoe UI", 10)).pack(side="left", padx=(0, 5))
        nombre_entry = tk.Entry(controls_frame, textvariable=self.nombre_var, width=15, font=("Segoe UI", 10))
        nombre_entry.pack(side="left", padx=(0, 10))

        tk.Label(controls_frame, text="Fecha:", bg="white", font=("Segoe UI", 10)).pack(side="left", padx=(0, 5))
        self.fecha_entry = DateEntry(controls_frame, textvariable=self.fecha_var, width=12, date_pattern="yyyy-mm-dd", background="#0B5394", foreground="white", font=("Segoe UI", 10))
        self.fecha_entry.pack(side="left", padx=(0, 10))

        # NUEVO: Filtro de usuario solo para admin
        if hasattr(self.parent, 'rol') and self.parent.rol == "admin":
            if not hasattr(self, 'usuario_filtro_var'):
                self.usuario_filtro_var = tk.StringVar()
            
            tk.Label(controls_frame, text="Usuario:", bg="white", font=("Segoe UI", 10)).pack(side="left", padx=(10, 5))
            usuario_entry = tk.Entry(controls_frame, textvariable=self.usuario_filtro_var, width=15, font=("Segoe UI", 10))
            usuario_entry.pack(side="left", padx=(0, 10))

        tk.Button(controls_frame, text="Filtrar", command=self._actualizar_tabla_historial_filtrada, bg="#0B5394", fg="white", font=("Segoe UI", 10, "bold"), relief="flat", padx=12, pady=2, cursor="hand2").pack(side="left", padx=10)
        tk.Button(controls_frame, text="Limpiar", command=self._limpiar_filtros, bg="#888", fg="white", font=("Segoe UI", 10), relief="flat", padx=10, pady=2, cursor="hand2").pack(side="left", padx=5)

    def _create_table(self):
        """Crear tabla de historial"""
        self.tabla_historial_frame = tk.Frame(self.historial_table_frame, bg="white")
        self.tabla_historial_frame.grid(row=1, column=0, columnspan=10, sticky="nsew", padx=30, pady=20)
        self.historial_table_frame.grid_rowconfigure(1, weight=1)
        self.historial_table_frame.grid_columnconfigure(0, weight=1)

    def _limpiar_filtros(self):
        """Limpiar filtros"""
        self.nombre_var.set("")
        self.fecha_var.set("")
        if hasattr(self, 'usuario_filtro_var'):
            self.usuario_filtro_var.set("")
        self._actualizar_tabla_historial_filtrada()

    def _actualizar_tabla_historial_filtrada(self):
        """Actualizar tabla con filtros aplicados"""
        # Limpiar tabla anterior
        for widget in self.tabla_historial_frame.winfo_children():
            try:
                widget.destroy()
            except:
                pass

        nombre = self.nombre_var.get() if hasattr(self, 'nombre_var') else ""
        fecha = self.fecha_var.get() if hasattr(self, 'fecha_var') else ""
        usuario_filtro = self.usuario_filtro_var.get() if hasattr(self, 'usuario_filtro_var') else ""

        try:
            # Verificar si el parent tiene el método
            if not hasattr(self.parent, 'get_usuario_id'):
                messagebox.showerror("Error", "Método get_usuario_id no disponible")
                return

            # CAMBIO: Lógica según el rol del usuario
            if hasattr(self.parent, 'rol') and self.parent.rol == "admin":
                # Si es admin, mostrar TODO el historial de TODOS los usuarios
                from core.auth import obtener_historial_completo_admin
                try:
                    historial = obtener_historial_completo_admin()
                except:
                    # Fallback si no existe la función específica
                    from core.auth import obtener_historial
                    historial = obtener_historial()
            else:
                # Si es usuario normal, mostrar SOLO su historial
                usuario_id = self.parent.get_usuario_id()
                if usuario_id is None:
                    return  # El error ya se mostró en get_usuario_id
                
                from core.auth import obtener_historial_usuario
                historial = obtener_historial_usuario(usuario_id)
                
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar el historial: {e}")
            historial = []

        # Aplicar filtros
        filtrado = []
        for item in historial:
            try:
                if len(item) >= 7:
                    Id, Nombre, Descripcion, Fecha, Hora, UsuarioId, Archivo = item[:7]
                    
                    # Filtro por nombre
                    if nombre and nombre.lower() not in str(Nombre).lower():
                        continue
                    
                    # Filtro por fecha
                    if fecha and str(Fecha) != fecha:
                        continue
                    
                    # NUEVO: Filtro por usuario (solo para admin)
                    if (hasattr(self.parent, 'rol') and self.parent.rol == "admin" and 
                        usuario_filtro and usuario_filtro.lower() not in str(UsuarioId).lower()):
                        continue
                    
                    filtrado.append(item)
                    
            except Exception as e:
                print(f"Error procesando item del historial: {e}")
                continue

        # CAMBIO: Encabezados según rol
        if hasattr(self.parent, 'rol') and self.parent.rol == "admin":
            headers = ["ID", "Nombre", "Descripción", "Fecha", "Hora", "Usuario ID", "Usuario", "Archivo", "Descargar", "Eliminar"]
        else:
            headers = ["ID", "Nombre", "Descripción", "Fecha", "Hora", "Archivo", "Descargar", "Eliminar"]
            
        header_bg = "#0B5394"
        header_fg = "white"
        for col, h in enumerate(headers):
            tk.Label(
                self.tabla_historial_frame, text=h, font=("Segoe UI", 11, "bold"),
                bg=header_bg, fg=header_fg, padx=8, pady=8, borderwidth=0, relief="flat"
            ).grid(row=0, column=col, sticky="nsew", padx=1, pady=1)

        # Cargar iconos
        download_icon = self._load_icon("download.png")
        trash_icon = self._load_icon("basura.png")

        # Filas de datos
        row_bg1 = "#e6f0fa"
        row_bg2 = "#f7fbff"
        
        if not filtrado:
            # Mostrar mensaje si no hay datos
            no_data_label = tk.Label(
                self.tabla_historial_frame,
                text="No se encontraron registros con los filtros aplicados." if (nombre or fecha or usuario_filtro) else 
                      "No hay registros en el historial." if hasattr(self.parent, 'rol') and self.parent.rol != "admin" else
                      "No hay registros en la base de datos.",
                font=("Segoe UI", 12),
                fg="#666666",
                bg="white",
                pady=20
            )
            no_data_label.grid(row=1, column=0, columnspan=len(headers), pady=20)
        
        for row, item in enumerate(filtrado, start=1):
            try:
                if len(item) >= 7:
                    Id, Nombre, Descripcion, Fecha, Hora, UsuarioId, Archivo = item[:7]
                    bg = row_bg1 if row % 2 == 1 else row_bg2

                    col_index = 0
                    
                    # ID
                    tk.Label(self.tabla_historial_frame, text=Id, bg=bg, font=("Segoe UI", 10), borderwidth=0, relief="flat", padx=8, pady=4).grid(row=row, column=col_index, sticky="nsew", padx=1, pady=1)
                    col_index += 1
                    
                    # Nombre
                    tk.Label(self.tabla_historial_frame, text=Nombre, bg=bg, font=("Segoe UI", 10), borderwidth=0, relief="flat", padx=8, pady=4).grid(row=row, column=col_index, sticky="nsew", padx=1, pady=1)
                    col_index += 1
                    
                    # Descripción
                    tk.Label(self.tabla_historial_frame, text=Descripcion, bg=bg, font=("Segoe UI", 10), borderwidth=0, relief="flat", padx=8, pady=4, wraplength=200, justify="left").grid(row=row, column=col_index, sticky="nsew", padx=1, pady=1)
                    col_index += 1
                    
                    # Fecha
                    tk.Label(self.tabla_historial_frame, text=str(Fecha), bg=bg, font=("Segoe UI", 10), borderwidth=0, relief="flat", padx=8, pady=4).grid(row=row, column=col_index, sticky="nsew", padx=1, pady=1)
                    col_index += 1
                    
                    # Hora
                    tk.Label(self.tabla_historial_frame, text=str(Hora), bg=bg, font=("Segoe UI", 10), borderwidth=0, relief="flat", padx=8, pady=4).grid(row=row, column=col_index, sticky="nsew", padx=1, pady=1)
                    col_index += 1

                    # CAMBIO: Mostrar información de usuario solo para admin
                    if hasattr(self.parent, 'rol') and self.parent.rol == "admin":
                        # Usuario ID
                        tk.Label(self.tabla_historial_frame, text=str(UsuarioId), bg=bg, font=("Segoe UI", 10), borderwidth=0, relief="flat", padx=8, pady=4).grid(row=row, column=col_index, sticky="nsew", padx=1, pady=1)
                        col_index += 1
                        
                        # Nombre de usuario (obtener desde la BD)
                        try:
                            from core.auth import obtener_username_por_id
                            username = obtener_username_por_id(UsuarioId)
                        except:
                            username = f"Usuario {UsuarioId}"
                        
                        tk.Label(self.tabla_historial_frame, text=username, bg=bg, font=("Segoe UI", 10), borderwidth=0, relief="flat", padx=8, pady=4).grid(row=row, column=col_index, sticky="nsew", padx=1, pady=1)
                        col_index += 1

                    # Archivo
                    archivo_text = "Sí" if Archivo else "No"
                    tk.Label(self.tabla_historial_frame, text=archivo_text, bg=bg, font=("Segoe UI", 10), borderwidth=0, relief="flat", padx=8, pady=4).grid(row=row, column=col_index, sticky="nsew", padx=1, pady=1)
                    col_index += 1

                    # Botón descargar
                    download_btn = tk.Button(
                        self.tabla_historial_frame,
                        text="📥" if download_icon is None else "",
                        image=download_icon if download_icon else None,
                        bg=bg,
                        bd=0,
                        activebackground="#b3d1f7",
                        cursor="hand2",
                        command=lambda archivo=Archivo, nombre=Nombre: self._descargar_archivo(archivo, nombre)
                    )
                    download_btn.grid(row=row, column=col_index, padx=4, pady=1)
                    col_index += 1

                    # Botón eliminar - CAMBIO: Solo permitir eliminar registros propios (o todo si es admin)
                    can_delete = False
                    if hasattr(self.parent, 'rol') and self.parent.rol == "admin":
                        can_delete = True  # Admin puede eliminar cualquier registro
                    else:
                        # Usuario normal solo puede eliminar sus propios registros
                        current_user_id = self.parent.get_usuario_id()
                        can_delete = (current_user_id == UsuarioId)
                    
                    if can_delete:
                        delete_btn = tk.Button(
                            self.tabla_historial_frame,
                            text="🗑" if trash_icon is None else "",
                            image=trash_icon if trash_icon else None,
                            bg=bg,
                            bd=0,
                            activebackground="#f7bdbd",
                            cursor="hand2",
                            command=lambda id_hist=Id: self._eliminar_registro(id_hist)
                        )
                    else:
                        delete_btn = tk.Button(
                            self.tabla_historial_frame,
                            text="🚫",
                            bg=bg,
                            bd=0,
                            state="disabled",
                            cursor="not-allowed"
                        )
                    
                    delete_btn.grid(row=row, column=col_index, padx=4, pady=1)

            except Exception as e:
                print(f"Error creando fila {row}: {e}")
                continue

        # Hacer columnas expandibles
        for col in range(len(headers)):
            if col == 2:  # Descripción
                self.tabla_historial_frame.grid_columnconfigure(col, weight=3, minsize=200)
            elif col == 6 and hasattr(self.parent, 'rol') and self.parent.rol == "admin":  # Usuario
                self.tabla_historial_frame.grid_columnconfigure(col, weight=2, minsize=100)
            else:
                self.tabla_historial_frame.grid_columnconfigure(col, weight=1, minsize=80)

    def _load_icon(self, filename):
        """Cargar icono con manejo de errores"""
        try:
            icon_path = os.path.join(os.path.dirname(__file__), "..", "img", filename)
            icon_path = os.path.abspath(icon_path)
            icon_img = Image.open(icon_path).resize((20, 20), Image.LANCZOS)
            icon = ImageTk.PhotoImage(icon_img)
            # Guardar referencia para evitar garbage collection
            if not hasattr(self, '_icons'):
                self._icons = {}
            self._icons[filename] = icon
            return icon
        except Exception:
            return None

    def _descargar_archivo(self, archivo_bin, nombre):
        """Descargar archivo del historial"""
        if not archivo_bin:
            messagebox.showwarning("Advertencia", "No hay archivo para descargar.")
            return
        
        try:
            # Detectar tipo de archivo basado en sus primeros bytes
            tipo_archivo = ".xlsx"  # Default
            extension = ".xlsx"
            
            # Detectar si es PDF (inicia con %PDF)
            if archivo_bin[:4] == b'%PDF':
                tipo_archivo = "PDF"
                extension = ".pdf"
            # Detectar si es Excel (XLSX)
            elif archivo_bin[:2] == b'PK':
                tipo_archivo = "Excel"
                extension = ".xlsx"
                
            # Limpiar nombre de archivo
            nombre_limpio = "".join(c for c in str(nombre) if c.isalnum() or c in (' ', '-', '_', '.')).rstrip()
            if not nombre_limpio:
                nombre_limpio = "archivo_descargado"
                
            # Asegurarse de que tenga la extensión correcta
            if not nombre_limpio.lower().endswith(extension):
                nombre_limpio = nombre_limpio + extension
                
            # Ubicación de descarga
            try:
                desktop = os.path.join(os.path.expanduser("~"), "Desktop")
                if not os.path.exists(desktop):
                    desktop = os.path.expanduser("~")
            except:
                desktop = ""
                
            file_path = filedialog.asksaveasfilename(
                title=f"Guardar archivo {tipo_archivo}",
                initialfile=nombre_limpio,
                initialdir=desktop,
                defaultextension=extension,
                filetypes=[
                    ("Archivos PDF", "*.pdf") if tipo_archivo == "PDF" else ("Archivos Excel", "*.xlsx"),
                    ("Todos los archivos", "*.*")
                ]
            )
            
            if file_path:
                with open(file_path, "wb") as f:
                    f.write(archivo_bin)
                messagebox.showinfo("Éxito", f"Archivo {tipo_archivo} guardado exitosamente:\n{file_path}")
            else:
                messagebox.showinfo("Cancelado", "Descarga cancelada por el usuario.")
                
        except PermissionError:
            messagebox.showerror("Error", "No tienes permisos para escribir en esa ubicación.\nIntenta con otra carpeta.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar el archivo: {e}")

    def _eliminar_registro(self, id_hist):
        """Eliminar registro del historial"""
        if not messagebox.askyesno("Eliminar registro", "¿Estás seguro de que deseas eliminar este registro del historial?\n\nEsta acción no se puede deshacer."):
            return
            
        try:
            from core.auth import eliminar_historial
            eliminar_historial(id_hist)
            messagebox.showinfo("Éxito", "Registro eliminado correctamente.")
            self._actualizar_tabla_historial_filtrada()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo eliminar el registro: {e}")