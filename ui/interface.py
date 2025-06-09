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

        self.menu_visible = True  # Estado del menú lateral

        self.create_widgets()

    def create_widgets(self):
        # Header
        header = tk.Frame(self, bg="#0B5394", height=60)
        header.pack(side="top", fill="x")

        # Botón del menú lateral
        self.menu_toggle_btn = tk.Button(
            header,
            text="☰",
            font=("Segoe UI", 16, "bold"),
            bg="#0B5394",
            fg="white",
            bd=0,
            activebackground="#073763",
            activeforeground="white",
            cursor="hand2",
            command=self.toggle_menu
        )
        self.menu_toggle_btn.pack(side="left", padx=(20, 10), pady=10)

        # Título clickable
        title = tk.Label(
            header,
            text="UANL FoodLab",
            bg="#0B5394",
            fg="white",
            font=("Segoe UI", 16, "bold"),
            padx=10,
            cursor="hand2"
        )
        title.pack(side="left", pady=10)
        title.bind("<Button-1>", lambda e: self.show_section("Inicio"))

        # --- Usuario y foto circular ---
        user_frame = tk.Frame(header, bg="#0B5394")
        user_frame.pack(side="right", padx=20)

        user_label = tk.Label(
            user_frame,
            text=self.username if self.username else "Usuario",
            bg="#0B5394",
            fg="white",
            font=("Segoe UI", 12, "bold"),
            padx=10
        )
        user_label.pack(side="left")

        # Imagen circular (ahora user.png)
        img_path = os.path.join(os.path.dirname(__file__), "..", "img", "user.png")
        img_path = os.path.abspath(img_path)
        user_img = Image.open(img_path).resize((40, 40), Image.LANCZOS)  # Tamaño reducido
        mask = Image.new('L', (40, 40), 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0, 40, 40), fill=255)
        user_img.putalpha(mask)
        self.user_icon = ImageTk.PhotoImage(user_img)
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

        # Menú lateral (Frame) - ahora será un Toplevel para transparencia y overlay
        self.menu_frame = None
        self.create_side_menu()

        # Zona de contenido
        self.content_frame = tk.Frame(self, bg="white")
        self.content_frame.pack(expand=True, fill="both")

        self.show_section("Inicio")

    def create_side_menu(self):
        # Si ya existe, destrúyelo para evitar duplicados
        if hasattr(self, "menu_frame") and self.menu_frame is not None:
            self.menu_frame.destroy()

        # Crear menú lateral como Toplevel SIN transparencia
        self.menu_frame = tk.Toplevel(self)
        self.menu_frame.overrideredirect(True)
        self.menu_frame.attributes('-topmost', True)
        # Elimina la línea de transparencia:
        # self.menu_frame.attributes('-alpha', 0.93)
        self.menu_frame.configure(bg="#0B5394")  # Mismo color que el header

        self.update_side_menu_geometry()

        # Contenido del menú
        menu_label = tk.Label(
            self.menu_frame,
            text="Menú",
            bg="#0B5394",
            fg="white",
            font=("Segoe UI", 15, "bold")
        )
        menu_label.pack(pady=(25, 15), anchor="w", padx=30)

        sections = ["Inicio", "Cálculos", "Exportar Excel", "Historial"]
        self.menu_buttons = []
        for section in sections:
            btn = tk.Button(
                self.menu_frame,
                text=section,
                relief="flat",
                bg="#0B5394",
                fg="white",
                font=("Segoe UI", 13),
                anchor="w",
                padx=30,
                pady=12,
                activebackground="#073763",
                activeforeground="white",
                command=lambda s=section: [self.show_section(s), self.toggle_menu()]
            )
            btn.pack(fill="x", pady=2)
            self.menu_buttons.append(btn)

        # Línea separadora
        sep = tk.Frame(self.menu_frame, bg="#073763", height=2)
        sep.pack(fill="x", padx=20, pady=10)

        # Botón para cerrar el menú
        close_btn = tk.Button(
            self.menu_frame,
            text="⨉",
            font=("Segoe UI", 16, "bold"),
            bg="#0B5394",
            fg="white",
            bd=0,
            activebackground="#073763",
            activeforeground="white",
            command=self.toggle_menu,
            cursor="hand2"
        )
        close_btn.place(x=220, y=10, width=30, height=30)

        # Mantener menú alineado al cambiar tamaño/mover ventana
        self.bind("<Configure>", lambda e: self.update_side_menu_geometry() if self.menu_visible else None)

    def update_side_menu_geometry(self):
        # Calcula posición y tamaño para cubrir todo el lateral izquierdo, justo debajo del header
        self.update_idletasks()
        x = self.winfo_rootx()
        y = self.winfo_rooty()
        h = self.winfo_height()
        header_height = 60  # Altura del banner superior
        self.menu_frame.geometry(f"260x{h-header_height}+{x}+{y+header_height}")

    def toggle_menu(self):
        if hasattr(self, "menu_frame") and self.menu_frame is not None and self.menu_visible:
            self.menu_frame.withdraw()
            self.menu_visible = False
        else:
            self.create_side_menu()
            self.menu_frame.deiconify()
            self.menu_visible = True

    def show_user_menu(self):
        # Crear ventana tipo popup personalizada dentro de la ventana principal
        popup = tk.Toplevel(self)
        popup.overrideredirect(True)
        popup.configure(bg="white", bd=2, highlightthickness=2, highlightbackground="#0B5394")

        # Calcular posición centrada respecto a la ventana principal
        main_x = self.winfo_rootx()
        main_y = self.winfo_rooty()
        main_w = self.winfo_width()
        popup_w, popup_h = 200, 90
        x = main_x + main_w - popup_w - 40  # 40px de margen a la derecha
        y = main_y + 70  # Debajo del header

        popup.geometry(f"{popup_w}x{popup_h}+{x}+{y}")

        # Nombre de usuario en negritas
        tk.Label(
            popup,
            text=self.username if self.username else "Usuario",
            bg="white",
            fg="#0B5394",
            font=("Segoe UI", 11, "bold")
        ).pack(pady=(10, 2), padx=10)

        # Línea separadora
        tk.Frame(popup, bg="#0B5394", height=2).pack(fill="x", padx=10, pady=2)

        # Botón cerrar sesión
        tk.Button(
            popup,
            text="Cerrar sesión",
            font=("Segoe UI", 11),
            bg="#0B5394",
            fg="white",
            activebackground="#073763",
            activeforeground="white",
            relief="flat",
            command=lambda: [popup.destroy(), self.logout()]
        ).pack(fill="x", padx=20, pady=10)

        # Cerrar el popup si pierde foco
        popup.focus_force()
        popup.bind("<FocusOut>", lambda e: popup.destroy())

    def logout(self):
        if messagebox.askyesno("Cerrar sesión", "¿Deseas cerrar sesión?"):
            self.destroy()

    def show_section(self, section_name):
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        if section_name == "Inicio":
            # Ventana informativa de bienvenida
            frame = tk.Frame(self.content_frame, bg="white")
            frame.pack(expand=True, fill="both")

            # Imagen de Bruni centrada (más grande)
            img_path = os.path.join(os.path.dirname(__file__), "..", "img", "bruni.png")
            img_path = os.path.abspath(img_path)
            bruni_img = Image.open(img_path).resize((200, 200), Image.LANCZOS)
            mask = Image.new('L', (200, 200), 0)
            draw = ImageDraw.Draw(mask)
            draw.ellipse((0, 0, 200, 200), fill=255)
            bruni_img.putalpha(mask)
            bruni_photo = ImageTk.PhotoImage(bruni_img)
            img_label = tk.Label(frame, image=bruni_photo, bg="white")
            img_label.image = bruni_photo  # Referencia para evitar garbage collection
            img_label.pack(pady=(30, 20))

            # Texto de bienvenida
            welcome = tk.Label(
                frame,
                text=f"¡Bienvenido, {self.username if self.username else 'Usuario'}!",
                font=("Segoe UI", 22, "bold"),
                fg="#0B5394",
                bg="white"
            )
            welcome.pack(pady=(0, 10))

            info = tk.Label(
                frame,
                text=(
                    "Este sistema es parte del Laboratorio de Alimentos de la\n"
                    "Facultad de Ciencias Químicas - UANL.\n\n"
                    "Aquí podrás realizar cálculos, exportar reportes y consultar tu historial.\n"
                    "¡Gracias por formar parte de la comunidad científica de la FCQ-UANL!\n\n"
                    "Facultad de Ciencias Químicas\n"
                    "Universidad Autónoma de Nuevo León\n"
                    "www.fcq.uanl.mx\n"
                    "Av. Universidad S/N, Cd. Universitaria, San Nicolás de los Garza, N.L."
                ),
                font=("Segoe UI", 13),
                fg="#333333",
                bg="white",
                justify="center"
            )
            info.pack(pady=(0, 20))
        else:
            label = tk.Label(
                self.content_frame,
                text=f"Sección: {section_name}",
                font=("Segoe UI", 14),
                bg="white"
            )
            label.pack(pady=20)
