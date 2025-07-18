import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import os
from core.auth import obtener_usuarios, crear_usuario, actualizar_usuario, eliminar_usuario, eliminar_historial_por_usuario
from ui.base_interface import bind_mousewheel

class UsersManagement:
    def __init__(self, parent):
        self.parent = parent
        
    def show_users_table(self):
        """Mostrar tabla de usuarios"""
        # Limpiar contenido anterior de manera segura
        for widget in self.parent.content_frame.winfo_children():
            try:
                widget.destroy()
            except:
                pass

        # Canvas y Scrollbar
        main_canvas = tk.Canvas(self.parent.content_frame, bg="white")
        main_scrollbar = tk.Scrollbar(self.parent.content_frame, orient="vertical", command=main_canvas.yview)
        self.users_table_frame = tk.Frame(main_canvas, bg="white")

        self.users_table_frame.bind(
            "<Configure>",
            lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all"))
        )

        main_canvas.create_window((0, 0), window=self.users_table_frame, anchor="nw")
        main_canvas.configure(yscrollcommand=main_scrollbar.set)

        # Botón agregar usuario
        plus_path = os.path.join(os.path.dirname(__file__), "..", "..", "img", "+.png")
        plus_path = os.path.abspath(plus_path)
        
        try:
            plus_img = Image.open(plus_path).resize((24, 24), Image.LANCZOS)
            plus_icon = ImageTk.PhotoImage(plus_img)
            self.plus_icon = plus_icon
        except Exception:
            plus_icon = None

        # Padding superior
        padding_frame = tk.Frame(self.users_table_frame, bg="white", height=30)
        padding_frame.pack(fill="x")

        add_btn = tk.Button(
            self.users_table_frame,
            text="+" if plus_icon is None else "",
            image=plus_icon if plus_icon else None,
            bg="white",
            bd=0,
            activebackground="#b3d1f7",
            cursor="hand2",
            command=self.add_user_popup,
            font=("Segoe UI", 16, "bold") if plus_icon is None else None
        )
        add_btn.pack(anchor="w", padx=30, pady=(0, 8))

        # Frame contenedor para la tabla
        table_frame = tk.Frame(self.users_table_frame, bg="white")
        table_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        # Encabezados
        headers = ["ID", "Usuario", "Email", "Rol", "Editar", "Eliminar"]
        header_bg = "#0B5394"
        header_fg = "white"
        for col, h in enumerate(headers):
            header_label = tk.Label(
                table_frame, text=h, font=("Segoe UI", 11, "bold"),
                bg=header_bg, fg=header_fg, padx=15, pady=12, borderwidth=0, relief="flat"
            )
            header_label.grid(row=0, column=col, sticky="nsew", padx=1, pady=1)

        # Cargar imágenes con manejo de errores
        try:
            lapiz_path = os.path.join(os.path.dirname(__file__), "..", "..", "img", "lapiz.png")
            lapiz_path = os.path.abspath(lapiz_path)
            lapiz_img = Image.open(lapiz_path).resize((20, 20), Image.LANCZOS)
            lapiz_icon = ImageTk.PhotoImage(lapiz_img)
            self.lapiz_icon = lapiz_icon
        except Exception:
            lapiz_icon = None

        try:
            basura_path = os.path.join(os.path.dirname(__file__), "..", "..", "img", "basura.png")
            basura_path = os.path.abspath(basura_path)
            basura_img = Image.open(basura_path).resize((20, 20), Image.LANCZOS)
            basura_icon = ImageTk.PhotoImage(basura_img)
            self.basura_icon = basura_icon
        except Exception:
            basura_icon = None

        # Obtener usuarios
        try:
            usuarios = obtener_usuarios()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron cargar los usuarios: {e}")
            usuarios = []

        row_bg1 = "#e6f0fa"
        row_bg2 = "#f7fbff"
        for row, user in enumerate(usuarios, start=1):
            user_id, username, email, rol = user
            bg = row_bg1 if row % 2 == 1 else row_bg2

            tk.Label(table_frame, text=user_id, bg=bg, font=("Segoe UI", 10), borderwidth=0, relief="flat", padx=15, pady=8).grid(row=row, column=0, sticky="nsew", padx=1, pady=1)
            tk.Label(table_frame, text=username, bg=bg, font=("Segoe UI", 10), borderwidth=0, relief="flat", padx=15, pady=8).grid(row=row, column=1, sticky="nsew", padx=1, pady=1)
            tk.Label(table_frame, text=email, bg=bg, font=("Segoe UI", 10), borderwidth=0, relief="flat", padx=15, pady=8).grid(row=row, column=2, sticky="nsew", padx=1, pady=1)
            tk.Label(table_frame, text=rol, bg=bg, font=("Segoe UI", 10), borderwidth=0, relief="flat", padx=15, pady=8).grid(row=row, column=3, sticky="nsew", padx=1, pady=1)

            edit_btn = tk.Button(
                table_frame,
                text="✏" if lapiz_icon is None else "",
                image=lapiz_icon if lapiz_icon else None,
                bg=bg,
                bd=0,
                activebackground="#b3d1f7",
                cursor="hand2",
                command=lambda u=user: self.edit_user_popup(u)
            )
            edit_btn.grid(row=row, column=4, padx=8, pady=4, sticky="nsew")

            delete_btn = tk.Button(
                table_frame,
                text="🗑" if basura_icon is None else "",
                image=basura_icon if basura_icon else None,
                bg=bg,
                bd=0,
                activebackground="#f7bdbd",
                cursor="hand2",
                command=lambda uid=user_id: self.delete_user(uid)
            )
            delete_btn.grid(row=row, column=5, padx=8, pady=4, sticky="nsew")

        # Configurar columnas expandibles
        table_frame.grid_columnconfigure(0, weight=1, minsize=60)
        table_frame.grid_columnconfigure(1, weight=3, minsize=120)
        table_frame.grid_columnconfigure(2, weight=4, minsize=180)
        table_frame.grid_columnconfigure(3, weight=2, minsize=80)
        table_frame.grid_columnconfigure(4, weight=1, minsize=60)
        table_frame.grid_columnconfigure(5, weight=1, minsize=60)

        main_canvas.pack(side="left", fill="both", expand=True)
        main_scrollbar.pack(side="right", fill="y")
        
        bind_mousewheel(main_canvas, main_canvas)

    def add_user_popup(self):
        """Popup para agregar usuario"""
        popup = tk.Toplevel(self.parent)
        popup.title("Agregar nuevo usuario")
        popup.geometry("350x350")
        popup.configure(bg="white")
        popup.resizable(False, False)
        popup.grab_set()
        
        # Centrar popup
        popup.transient(self.parent)
        popup.update_idletasks()
        x = (popup.winfo_screenwidth() // 2) - (350 // 2)
        y = (popup.winfo_screenheight() // 2) - (350 // 2)
        popup.geometry(f"350x350+{x}+{y}")

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
            command=create_user
        ).pack(fill="x", padx=40, pady=20, ipady=8)

    def edit_user_popup(self, user):
        """Popup para editar usuario"""
        user_id, username, email, rol = user
        popup = tk.Toplevel(self.parent)
        popup.title(f"Editar usuario: {username}")
        popup.geometry("350x370")
        popup.configure(bg="white")
        popup.resizable(False, False)
        popup.grab_set()
        
        # Centrar popup
        popup.transient(self.parent)
        popup.update_idletasks()
        x = (popup.winfo_screenwidth() // 2) - (350 // 2)
        y = (popup.winfo_screenheight() // 2) - (370 // 2)
        popup.geometry(f"350x370+{x}+{y}")

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
                if nueva_contra:
                    actualizar_usuario(user_id, nuevo_username, nuevo_email, nuevo_rol, nueva_contra)
                else:
                    actualizar_usuario(user_id, nuevo_username, nuevo_email, nuevo_rol)
                messagebox.showinfo("Éxito", "Usuario actualizado correctamente.", parent=popup)
                popup.destroy()
                self.show_users_table()
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

    def delete_user(self, user_id):
        """Eliminar usuario"""
        if messagebox.askyesno("Eliminar usuario", "¿Estás seguro de que deseas eliminar este usuario?\nEsto también eliminará su historial asociado."):
            try:
                eliminar_historial_por_usuario(user_id)
                eliminar_usuario(user_id)
                messagebox.showinfo("Éxito", "Usuario eliminado correctamente.")
                self.show_users_table()
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo eliminar el usuario: {e}")