import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageDraw, ImageTk

class MainInterface(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("UANL FoodLab")
        self.geometry("1000x600")
        self.configure(bg="white")

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

        # Ícono de usuario (imagen generada)
        self.user_icon = self.generate_generic_user_icon()
        self.user_btn = tk.Button(
            header,
            image=self.user_icon,
            bg="#0B5394",
            bd=0,
            activebackground="#0B5394",
            cursor="hand2",
            command=self.show_user_menu
        )
        self.user_btn.pack(side="right", padx=20)

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

        sections = ["Inicio", "Cálculos", "Exportar Excel", "Resultados"]
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

    def generate_generic_user_icon(self):
        """Genera una imagen genérica de usuario (círculo y cabeza)"""
        size = (40, 40)
        img = Image.new("RGBA", size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Cabeza
        draw.ellipse((10, 5, 30, 25), fill="#CCCCCC")

        # Cuerpo
        draw.rectangle((10, 25, 30, 38), fill="#CCCCCC")

        return ImageTk.PhotoImage(img)

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
