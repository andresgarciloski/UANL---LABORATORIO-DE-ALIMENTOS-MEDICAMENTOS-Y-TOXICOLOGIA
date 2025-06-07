import tkinter as tk
from tkinter import messagebox
from ui.interface import MainInterface

from core.auth import verificar_login

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

    def authenticate(self):
        username = self.username_entry.get()
        password = self.password_entry.get()

        if verificar_login(username, password):
            self.destroy()
            app = MainInterface()
            app.mainloop()
        else:
            messagebox.showerror("Error", "Usuario o contraseña incorrectos")