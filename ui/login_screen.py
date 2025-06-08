import tkinter as tk
from tkinter import messagebox, simpledialog
from ui.interface import MainInterface

from core.auth import verificar_login


try:
    from core.auth import crear_usuario
except ImportError:
    crear_usuario = None 

class LoginWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("UANL FoodLab")
        self.geometry("450x320")
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
            font=("Segoe UI", 14, "bold")
        )
        title.pack(pady=15)

        # Contenedor del formulario
        form_frame = tk.Frame(self, bg="white")
        form_frame.pack(pady=20)

        tk.Label(form_frame, text="Usuario:", font=("Segoe UI", 11), bg="white").grid(row=0, column=0, sticky="e", padx=10, pady=10)
        self.username_entry = tk.Entry(form_frame, font=("Segoe UI", 11), width=25)
        self.username_entry.grid(row=0, column=1, padx=10)

        tk.Label(form_frame, text="Contraseña:", font=("Segoe UI", 11), bg="white").grid(row=1, column=0, sticky="e", padx=10, pady=10)
        self.password_entry = tk.Entry(form_frame, show="*", font=("Segoe UI", 11), width=25)
        self.password_entry.grid(row=1, column=1, padx=10)

        # Botón iniciar sesión
        login_btn = tk.Button(
            self,
            text="Iniciar Sesión",
            font=("Segoe UI", 11, "bold"),
            bg="#0B5394",
            fg="white",
            activebackground="#073763",
            activeforeground="white",
            relief="flat",
            width=20,
            command=self.authenticate
        )
        login_btn.pack(pady=10)

        # Botón registrarse
        register_btn = tk.Button(
            self,
            text="Registrarse",
            font=("Segoe UI", 10),
            bg="white",
            fg="#0B5394",
            activebackground="#e6f0fa",
            activeforeground="#0B5394",
            relief="flat",
            width=20,
            command=self.register_user
        )
        register_btn.pack(pady=5)

    def authenticate(self):
        username = self.username_entry.get()
        password = self.password_entry.get()

        if verificar_login(username, password):
            self.destroy()
            app = MainInterface()
            app.mainloop()
        else:
            messagebox.showerror("Error", "Usuario o contraseña incorrectos")

    def register_user(self):
        if crear_usuario is None:
            messagebox.showinfo("No disponible", "Función de registro no implementada.")
            return

        # Crear ventana modal de registro
        reg_win = tk.Toplevel(self)
        reg_win.title("Registro de nuevo usuario")
        reg_win.geometry("350x300")
        reg_win.configure(bg="white")
        reg_win.resizable(False, False)
        reg_win.grab_set()  # Hace modal la ventana

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

                # Botón registrar (mejor alineado y con padding)
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