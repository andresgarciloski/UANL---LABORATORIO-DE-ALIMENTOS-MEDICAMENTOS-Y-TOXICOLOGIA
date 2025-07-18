import tkinter as tk
from tkinter import messagebox, simpledialog
from ui.interface import MainInterface
from ui.interface_admin import MainInterfaceAdmin  # Agrega este import al inicio
from PIL import Image, ImageTk, ImageDraw
import os

from core.auth import verificar_login


try:
    from core.auth import crear_usuario
except ImportError:
    crear_usuario = None 

class LoginWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("UANL FoodLab")
        self.geometry("540x600")
        self.configure(bg="white")
        self.resizable(False, False)
        self.build_ui()

    def build_ui(self):
        # Encabezado azul
        header = tk.Frame(self, bg="#0B5394", height=60)
        header.pack(fill="x")

        title = tk.Label(
            header,
            text="Laboratorio de Alimentos - UANL",
            bg="#0B5394",
            fg="white",
            font=("Segoe UI", 16, "bold")
        )
        title.pack(pady=15, side="left")

        # Botón admin con tooltip
        try:
            admin_img_path = os.path.join(os.path.dirname(__file__), "..", "img", "admin.png")
            admin_img_path = os.path.abspath(admin_img_path)
            admin_img = Image.open(admin_img_path).resize((28, 28), Image.LANCZOS)
            self.admin_icon = ImageTk.PhotoImage(admin_img)
            admin_btn = tk.Button(
                header,
                image=self.admin_icon,
                bg="#0B5394",
                bd=0,
                activebackground="#073763",
                cursor="hand2",
                command=self.open_admin_login
            )
            admin_btn.pack(side="right", padx=18, pady=10)

            # Tooltip
            def show_tooltip(event):
                self.tooltip = tk.Toplevel(self)
                self.tooltip.overrideredirect(True)
                self.tooltip.geometry(f"+{event.x_root+10}+{event.y_root+10}")
                label = tk.Label(self.tooltip, text="Acceso administrador", bg="#0B5394", fg="white", font=("Segoe UI", 9), padx=8, pady=3)
                label.pack()
            def hide_tooltip(event):
                if hasattr(self, 'tooltip') and self.tooltip:
                    self.tooltip.destroy()
                    self.tooltip = None
            admin_btn.bind("<Enter>", show_tooltip)
            admin_btn.bind("<Leave>", hide_tooltip)
        except Exception:
            admin_btn = tk.Button(
                header,
                text="Admin",
                bg="#0B5394",
                fg="white",
                bd=0,
                activebackground="#073763",
                cursor="hand2",
                command=self.open_admin_login
            )
            admin_btn.pack(side="right", padx=18, pady=10)

        # Imagen de Bruni circular y centrada
        try:
            img_path = os.path.join(os.path.dirname(__file__), "..", "img", "bruni.png")
            img_path = os.path.abspath(img_path)
            bruni_img = Image.open(img_path).resize((130, 130), Image.LANCZOS)
            mask = Image.new('L', (130, 130), 0)
            draw = ImageDraw.Draw(mask)
            draw.ellipse((0, 0, 130, 130), fill=255)
            bruni_img.putalpha(mask)
            bruni_photo = ImageTk.PhotoImage(bruni_img)
            img_label = tk.Label(self, image=bruni_photo, bg="white")
            img_label.image = bruni_photo
            img_label.pack(pady=(25, 10))
        except Exception:
            img_label = tk.Label(self, text="🧪", font=("Segoe UI", 48), bg="white")
            img_label.pack(pady=(25, 10))

        # Formulario
        form_frame = tk.Frame(self, bg="white")
        form_frame.pack(pady=10)

        tk.Label(form_frame, text="Usuario:", font=("Segoe UI", 12), bg="white").grid(row=0, column=0, sticky="e", padx=10, pady=10)
        self.username_entry = tk.Entry(form_frame, font=("Segoe UI", 12), width=25)
        self.username_entry.grid(row=0, column=1, padx=10, pady=10)

        tk.Label(form_frame, text="Contraseña:", font=("Segoe UI", 12), bg="white").grid(row=1, column=0, sticky="e", padx=10, pady=10)
        self.password_entry = tk.Entry(form_frame, show="*", font=("Segoe UI", 12), width=25)
        self.password_entry.grid(row=1, column=1, padx=10, pady=10)

        # Botones
        btn_frame = tk.Frame(self, bg="white")
        btn_frame.pack(pady=15)

        login_btn = tk.Button(
            btn_frame,
            text="Iniciar Sesión",
            font=("Segoe UI", 12, "bold"),
            bg="#0B5394",
            fg="white",
            activebackground="#073763",
            activeforeground="white",
            relief="flat",
            width=20,
            command=self.authenticate
        )
        login_btn.pack(pady=(5, 12), fill="x")

        register_btn = tk.Button(
            btn_frame,
            text="Registrarse",
            font=("Segoe UI", 11),
            bg="white",
            fg="#0B5394",
            activebackground="#e6f0fa",
            activeforeground="#0B5394",
            relief="flat",
            width=20,
            command=self.register_user
        )
        register_btn.pack(pady=5, fill="x")

        # Navegación por teclado
        self.username_entry.bind('<Return>', lambda e: self.password_entry.focus())
        self.password_entry.bind('<Return>', lambda e: self.authenticate())
        self.username_entry.focus()

    def authenticate(self):
        username = self.username_entry.get()
        password = self.password_entry.get()

        result = verificar_login(username, password)
        if isinstance(result, tuple) and result[0] is True:
            rol = result[1]
            if rol == "usuario":
                self.destroy()
                app = MainInterface(username=username, rol=rol)
                app.mainloop()
            else:
                messagebox.showerror("Acceso denegado", "Solo los usuarios pueden acceder desde este login.")
        else:
            messagebox.showerror("Error", "Usuario o contraseña incorrectos")

    def open_admin_login(self):
        admin_win = tk.Toplevel(self)
        admin_win.title("Acceso Administrador")
        admin_win.geometry("350x220")
        admin_win.configure(bg="white")
        admin_win.resizable(False, False)
        admin_win.grab_set()

        tk.Label(admin_win, text="Usuario Admin:", font=("Segoe UI", 11), bg="white").pack(pady=(20, 5))
        username_entry = tk.Entry(admin_win, font=("Segoe UI", 11), width=25)
        username_entry.pack()

        tk.Label(admin_win, text="Contraseña:", font=("Segoe UI", 11), bg="white").pack(pady=(10, 5))
        password_entry = tk.Entry(admin_win, show="*", font=("Segoe UI", 11), width=25)
        password_entry.pack()

        def admin_login():
            username = username_entry.get()
            password = password_entry.get()
            result = verificar_login(username, password)
            if isinstance(result, tuple) and result[0] is True and result[1] == "admin":
                admin_win.destroy()
                self.destroy()
                app = MainInterfaceAdmin(username=username, rol="admin")
                app.mainloop()
            else:
                messagebox.showerror("Acceso denegado", "Solo los administradores pueden acceder aquí.", parent=admin_win)

        tk.Button(
            admin_win,
            text="Entrar",
            font=("Segoe UI", 11, "bold"),
            bg="#0B5394",
            fg="white",
            activebackground="#073763",
            activeforeground="white",
            relief="flat",
            command=admin_login
        ).pack(fill="x", padx=40, pady=20, ipady=8)

    def register_user(self):
        if crear_usuario is None:
            messagebox.showinfo("No disponible", "Función de registro no implementada.")
            return

        reg_win = tk.Toplevel(self)
        reg_win.title("Registro de nuevo usuario")
        reg_win.geometry("350x300")
        reg_win.configure(bg="white")
        reg_win.resizable(False, False)
        reg_win.grab_set()

        tk.Label(reg_win, text="Usuario:", font=("Segoe UI", 11), bg="white").pack(pady=(20, 5))
        username_entry = tk.Entry(reg_win, font=("Segoe UI", 11), width=25)
        username_entry.pack()

        tk.Label(reg_win, text="Contraseña:", font=("Segoe UI", 11), bg="white").pack(pady=(10, 5))
        password_entry = tk.Entry(reg_win, show="*", font=("Segoe UI", 11), width=25)
        password_entry.pack()

        tk.Label(reg_win, text="Correo electrónico (opcional):", font=("Segoe UI", 11), bg="white").pack(pady=(10, 5))
        email_entry = tk.Entry(reg_win, font=("Segoe UI", 11), width=25)
        email_entry.pack()

        def submit_registration():
            username = username_entry.get()
            password = password_entry.get()
            email = email_entry.get()

            if not username or not password:
                messagebox.showerror("Error", "Usuario y contraseña son obligatorios.", parent=reg_win)
                return

            try:
                crear_usuario(username, password, email)
                messagebox.showinfo("Registro exitoso", "Usuario registrado correctamente. Ahora puedes iniciar sesión.", parent=reg_win)
                reg_win.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo registrar el usuario: {e}", parent=reg_win)

        tk.Button(
            reg_win,
            text="Registrar",
            font=("Segoe UI", 11, "bold"),
            bg="#0B5394",
            fg="white",
            activebackground="#073763",
            activeforeground="white",
            relief="flat",
            command=submit_registration
        ).pack(fill="x", padx=40, pady=20, ipady=8)