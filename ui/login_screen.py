import tkinter as tk
from tkinter import messagebox, simpledialog
from ui.interface import MainInterface
from ui.interface_admin import MainInterfaceAdmin  # Agrega este import al inicio
from PIL import Image, ImageTk, ImageDraw
import os

from core.auth import verificar_login
from ui.base_interface import _BG, _PRIMARY, _PRIMARY_DARK, _TEXT

class LoginWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        # Configuración ventana principal
        self.title("UANL FoodLab")
        self.geometry("540x600")
        self.configure(bg=_BG)
        self.resizable(False, False)
        self.build_login_ui()

    def clear_ui(self):
        for widget in self.winfo_children():
            widget.destroy()

    def build_login_ui(self):
        self.clear_ui()
        # Encabezado azul
        header = tk.Frame(self, bg=_PRIMARY, height=60)
        header.pack(fill="x")
        title = tk.Label(header, text="", bg=_PRIMARY, fg="white", font=("Segoe UI", 16, "bold"))
        title.pack(pady=15, side="left")
        # Botón admin
        try:
            admin_img_path = os.path.join(os.path.dirname(__file__), "..", "img", "admin.png")
            admin_img_path = os.path.abspath(admin_img_path)
            admin_img = Image.open(admin_img_path).resize((28, 28), Image.LANCZOS)
            self.admin_icon = ImageTk.PhotoImage(admin_img)
            admin_btn = tk.Button(header, image=self.admin_icon, bg=_PRIMARY, bd=0, activebackground=_PRIMARY_DARK, cursor="hand2", command=self.build_admin_ui)
            admin_btn.pack(side="right", padx=18, pady=10)
        except Exception:
            admin_btn = tk.Button(header, text="Admin", bg=_PRIMARY, fg="white", bd=0, activebackground=_PRIMARY_DARK, cursor="hand2", command=self.build_admin_ui)
            admin_btn.pack(side="right", padx=18, pady=10)

        # Imagen de Bruni
        try:
            img_path = os.path.join(os.path.dirname(__file__), "..", "img", "bruni.png")
            img_path = os.path.abspath(img_path)
            bruni_img = Image.open(img_path).resize((130, 130), Image.LANCZOS)
            mask = Image.new('L', (130, 130), 0)
            draw = ImageDraw.Draw(mask)
            draw.ellipse((0, 0, 130, 130), fill=255)
            bruni_img.putalpha(mask)
            bruni_photo = ImageTk.PhotoImage(bruni_img)
            img_label = tk.Label(self, image=bruni_photo, bg=_BG)
            img_label.image = bruni_photo
            img_label.pack(pady=(25, 10))
        except Exception:
            img_label = tk.Label(self, text="🧪", font=("Segoe UI", 48), bg=_BG, fg=_PRIMARY)
            img_label.pack(pady=(25, 10))

        # Formulario login
        form_frame = tk.Frame(self, bg=_BG)
        form_frame.pack(pady=10)
        tk.Label(form_frame, text="Usuario:", font=("Segoe UI", 12), bg=_BG, fg=_TEXT).grid(row=0, column=0, sticky="e", padx=10, pady=10)
        self.username_entry = tk.Entry(form_frame, font=("Segoe UI", 12), width=25)
        self.username_entry.grid(row=0, column=1, padx=10, pady=10)
        tk.Label(form_frame, text="Contraseña:", font=("Segoe UI", 12), bg=_BG, fg=_TEXT).grid(row=1, column=0, sticky="e", padx=10, pady=10)
        self.password_entry = tk.Entry(form_frame, show="*", font=("Segoe UI", 12), width=25)
        self.password_entry.grid(row=1, column=1, padx=10, pady=10)

        # Botones login
        btn_frame = tk.Frame(self, bg=_BG)
        btn_frame.pack(pady=15)
        login_btn = tk.Button(btn_frame, text="Iniciar Sesión", font=("Segoe UI", 12, "bold"), bg=_PRIMARY, fg="white", activebackground=_PRIMARY_DARK, activeforeground="white", relief="flat", width=20, command=self.authenticate)
        login_btn.pack(pady=(5, 12), fill="x")
        # Funcionalidad de registro eliminada (solicitado)

        self.username_entry.bind('<Return>', lambda e: self.password_entry.focus())
        self.password_entry.bind('<Return>', lambda e: self.authenticate())
        self.username_entry.focus()

    def build_admin_ui(self):
        self.clear_ui()
        header = tk.Frame(self, bg=_PRIMARY, height=60)
        header.pack(fill="x")
        # Botón regresar con imagen
        try:
            arrow_img_path = os.path.join(os.path.dirname(__file__), "..", "img", "flecha-derecha.png")
            arrow_img_path = os.path.abspath(arrow_img_path)
            arrow_img = Image.open(arrow_img_path).resize((24, 24), Image.LANCZOS)
            self.arrow_icon = ImageTk.PhotoImage(arrow_img)
            back_btn = tk.Button(header, image=self.arrow_icon, text=" Usuario", compound="left",
                                 bg=_PRIMARY, fg="white", bd=0, activebackground=_PRIMARY_DARK,
                                 cursor="hand2", font=("Segoe UI", 11, "bold"),
                                 command=self.build_login_ui)
        except Exception:
            back_btn = tk.Button(header, text="← Usuario", bg=_PRIMARY, fg="white", bd=0,
                                 activebackground=_PRIMARY_DARK, cursor="hand2",
                                 font=("Segoe UI", 11, "bold"), command=self.build_login_ui)
        back_btn.pack(side="left", padx=18, pady=10)
        title = tk.Label(header, text="", bg=_PRIMARY, fg="white", font=("Segoe UI", 16, "bold"))
        title.pack(pady=15)
        # Imagen admin
        try:
            img_path = os.path.join(os.path.dirname(__file__), "..", "img", "admin.png")
            img_path = os.path.abspath(img_path)
            admin_img = Image.open(img_path).resize((110, 110), Image.LANCZOS)
            mask = Image.new('L', (110, 110), 0)
            draw = ImageDraw.Draw(mask)
            draw.ellipse((0, 0, 110, 110), fill=255)
            admin_img.putalpha(mask)
            admin_photo = ImageTk.PhotoImage(admin_img)
            img_label = tk.Label(self, image=admin_photo, bg=_BG)
            img_label.image = admin_photo
            img_label.pack(pady=(25, 10))
        except Exception:
            img_label = tk.Label(self, text="👤", font=("Segoe UI", 48), bg=_BG, fg=_PRIMARY)
            img_label.pack(pady=(25, 10))
        # Formulario admin
        form_frame = tk.Frame(self, bg=_BG)
        form_frame.pack(pady=10)
        tk.Label(form_frame, text="Usuario Admin:", font=("Segoe UI", 12), bg=_BG, fg=_TEXT).grid(row=0, column=0, sticky="e", padx=10, pady=10)
        self.admin_username_entry = tk.Entry(form_frame, font=("Segoe UI", 12), width=25)
        self.admin_username_entry.grid(row=0, column=1, padx=10, pady=10)
        tk.Label(form_frame, text="Contraseña:", font=("Segoe UI", 12), bg=_BG, fg=_TEXT).grid(row=1, column=0, sticky="e", padx=10, pady=10)
        self.admin_password_entry = tk.Entry(form_frame, show="*", font=("Segoe UI", 12), width=25)
        self.admin_password_entry.grid(row=1, column=1, padx=10, pady=10)
        btn_frame = tk.Frame(self, bg=_BG)
        btn_frame.pack(pady=15)
        login_btn = tk.Button(btn_frame, text="Entrar", font=("Segoe UI", 12, "bold"), bg=_PRIMARY, fg="white", activebackground=_PRIMARY_DARK, activeforeground="white", relief="flat", width=20, command=self.authenticate_admin)
        login_btn.pack(pady=(5, 12), fill="x")
        self.admin_username_entry.bind('<Return>', lambda e: self.admin_password_entry.focus())
        self.admin_password_entry.bind('<Return>', lambda e: self.authenticate_admin())
        self.admin_username_entry.focus()

    def authenticate(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        result = verificar_login(username, password)
        if isinstance(result, tuple) and result[0] is True:
            rol = result[1]
            if rol == "usuario":
                # Guardar resultado y salir del mainloop para que main.py abra la app principal
                self.login_info = {"username": username, "rol": rol}
                self.quit()
            else:
                messagebox.showerror("Acceso denegado", "Solo los usuarios pueden acceder desde este login.")
        else:
            messagebox.showerror("Error", "Usuario o contraseña incorrectos")

    def authenticate_admin(self):
        username = self.admin_username_entry.get()
        password = self.admin_password_entry.get()
        result = verificar_login(username, password)
        if isinstance(result, tuple) and result[0] is True and result[1] == "admin":
            # Guardar resultado y salir del mainloop para que main.py abra la interfaz admin
            self.login_info = {"username": username, "rol": "admin"}
            self.quit()
        else:
            messagebox.showerror("Acceso denegado", "Solo los administradores pueden acceder aquí.")

    def submit_registration(self):
        # Registro deshabilitado deliberadamente
        messagebox.showwarning("Registro deshabilitado", "La creación de usuarios está deshabilitada.")