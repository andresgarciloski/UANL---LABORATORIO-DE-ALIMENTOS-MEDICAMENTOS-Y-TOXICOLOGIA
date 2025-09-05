import tkinter as tk
from PIL import Image, ImageDraw, ImageTk
import os
from ui.base_interface import bind_mousewheel, _BG, _PRIMARY, _PRIMARY_DARK, _TEXT

class HomeSection:
    def __init__(self, parent):
        self.parent = parent
        
    def show_home_section(self):
        """Mostrar sección de inicio"""
        # Frame principal que ocupa todo el espacio
        main_frame = tk.Frame(self.parent.content_frame, bg=_BG)
        main_frame.pack(fill="both", expand=True)

        # Canvas y Scrollbar para scroll
        canvas = tk.Canvas(main_frame, bg=_BG)
        scrollbar = tk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        content_frame = tk.Frame(canvas, bg=_BG)

        def center_content(event=None):
            canvas.update_idletasks()
            canvas_width = canvas.winfo_width()
            canvas_height = canvas.winfo_height()
            content_width = content_frame.winfo_reqwidth()
            content_height = content_frame.winfo_reqheight()

            x = max(0, (canvas_width - content_width) // 2)
            y = max(0, (canvas_height - content_height) // 2)

            canvas.configure(scrollregion=(0, 0, content_width, content_height))
            canvas.coords(canvas_window_id, x, y)

        canvas_window_id = canvas.create_window(0, 0, window=content_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Imagen de Bruni centrada
        try:
            img_path = os.path.join(os.path.dirname(__file__), "..", "img", "bruni.png")
            img_path = os.path.abspath(img_path)
            bruni_img = Image.open(img_path).resize((200, 200), Image.LANCZOS)
            mask = Image.new('L', (200, 200), 0)
            draw = ImageDraw.Draw(mask)
            draw.ellipse((0, 0, 200, 200), fill=255)
            bruni_img.putalpha(mask)
            bruni_photo = ImageTk.PhotoImage(bruni_img)
            img_label = tk.Label(content_frame, image=bruni_photo, bg=_BG)
            img_label.image = bruni_photo
            img_label.pack(pady=(20, 20))
        except Exception:
            # Fallback si no encuentra la imagen
            img_label = tk.Label(content_frame, text="🧪", font=("Segoe UI", 48), bg=_BG)
            img_label.pack(pady=(20, 20))

        # Texto de bienvenida
        welcome = tk.Label(
            content_frame,
            text=f"¡Bienvenido, {self.parent.username if self.parent.username else 'Usuario'}!",
            font=("Segoe UI", 22, "bold"),
            fg=_PRIMARY,
            bg=_BG
        )
        welcome.pack(pady=(0, 15))

        # Información centrada
        info = tk.Label(
            content_frame,
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
            fg=_TEXT,
            bg=_BG,
            justify="center"
        )
        info.pack(pady=(0, 20))

        # Enlazar eventos para centrar
        content_frame.bind("<Configure>", center_content)
        canvas.bind("<Configure>", center_content)
        
        # Configurar el layout
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Enlazar scroll del mouse SOLO cuando el mouse está sobre el área de contenido
        bind_mousewheel(content_frame, canvas)
        
        # Llamar center_content después de un breve delay
        self.parent.after(100, center_content)