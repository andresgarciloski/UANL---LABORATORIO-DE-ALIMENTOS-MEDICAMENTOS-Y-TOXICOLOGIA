import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageDraw, ImageTk
import os

class MainInterface(tk.Tk):
    def __init__(self, username=None):
        super().__init__()
        self.title("UANL FoodLab")
        self.geometry("1000x600")
        self.configure(bg="white")
        self.username = username  # Guarda el nombre de usuario

        self.create_widgets()

    def create_widgets(self):
        # Header
        header = tk.Frame(self, bg="#0B5394", height=60)
        header.pack(side="top", fill="x")

        title = tk.Label(
            header,
            text="UANL FoodLab",
            bg="#0B5394",
            fg="white",
            font=("Segoe UI", 16, "bold"),
            padx=20
        )
        title.pack(side="left", pady=10)

        # --- Usuario y foto circular ---
        user_frame = tk.Frame(header, bg="#0B5394")
        user_frame.pack(side="right", padx=20)

        # Nombre de usuario a la izquierda de la imagen
        user_label = tk.Label(
            user_frame,
            text=self.username if self.username else "Usuario",
            bg="#0B5394",
            fg="white",
            font=("Segoe UI", 12, "bold"),
            padx=10
        )
        user_label.pack(side="left")

        # Imagen circular
        img_path = os.path.join(os.path.dirname(__file__), "..", "img", "bruni.png")
        img_path = os.path.abspath(img_path)
        bruni_img = Image.open(img_path).resize((40, 40), Image.LANCZOS)

        # Crear máscara circular
        mask = Image.new('L', (40, 40), 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0, 40, 40), fill=255)
        bruni_img.putalpha(mask)

        self.user_icon = ImageTk.PhotoImage(bruni_img)
        self.user_btn = tk.Button(
            user_frame,
            image=self.user_icon,
            bg="#0B5394",
            bd=0,
            activebackground="#0B5394",
            cursor="hand2",
            command=self.show_user_menu
        )
        self.user_btn.pack(side="left")

        # Menú lateral
        menu_frame = tk.Frame(self, bg="#E6E6E6", width=200)
        menu_frame.pack(side="left", fill="y")

        menu_label = tk.Label(
            menu_frame,
            text="Menú",
            bg="#E6E6E6",
            font=("Segoe UI", 12, "bold")
        )
        menu_label.pack(pady=(20, 10))

        sections = ["Inicio", "Cálculos", "Exportar Excel", "Historial"]
        for section in sections:
            btn = tk.Button(
                menu_frame,
                text=section,
                relief="flat",
                bg="#E6E6E6",
                font=("Segoe UI", 11),
                anchor="w",
                padx=20,
                command=lambda s=section: self.show_section(s)
            )
            btn.pack(fill="x", pady=2)

        # Zona de contenido
        self.content_frame = tk.Frame(self, bg="white")
        self.content_frame.pack(expand=True, fill="both")

        self.show_section("Inicio")

    def show_user_menu(self):
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label="Cerrar sesión", command=self.logout)
        menu.tk_popup(self.winfo_pointerx(), self.winfo_pointery())

    def logout(self):
        if messagebox.askyesno("Cerrar sesión", "¿Deseas cerrar sesión?"):
            self.destroy()

    def show_section(self, section_name):
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        label = tk.Label(
            self.content_frame,
            text=f"Sección: {section_name}",
            font=("Segoe UI", 14),
            bg="white"
        )
        label.pack(pady=20)
