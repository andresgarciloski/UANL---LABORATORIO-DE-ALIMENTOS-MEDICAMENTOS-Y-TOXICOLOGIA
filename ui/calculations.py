import tkinter as tk
# NUEVO: paleta y helper de scroll
from ui.base_interface import (
    _BG, _PRIMARY, _PRIMARY_DARK, _TEXT, _TEXT_SECONDARY, _SECONDARY, _EMPHASIS, bind_mousewheel
)

class CalculationsSection:
    def __init__(self, parent):
        self.parent = parent
        
    def show_calculations_section(self):
        """Mostrar sección de cálculos"""
        # Frame principal (usa paleta)
        main_frame = tk.Frame(self.parent.content_frame, bg=_BG)
        main_frame.pack(fill="both", expand=True)

        # Header de sección (sub-encabezado)
        header = tk.Frame(main_frame, bg=_PRIMARY, height=70, highlightthickness=0)
        header.pack(fill="x", side="top")
        header.grid_propagate(False)
        tk.Label(header, text="Módulo de Cálculos", bg=_PRIMARY, fg="white",
                 font=("Segoe UI", 18, "bold")).pack(anchor="w", padx=18, pady=(10, 0))
        tk.Label(header, text="Herramientas auxiliares para cálculos químicos y nutricionales.",
                 bg=_PRIMARY, fg="white", font=("Segoe UI", 10)).pack(anchor="w", padx=18, pady=(0, 8))

        # Canvas y scrollbar para scroll (usa paleta)
        canvas = tk.Canvas(main_frame, bg=_BG, highlightthickness=0, bd=0)
        scrollbar = tk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        scrollable_frame = tk.Frame(canvas, bg=_BG)
        window_id = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

        def resize_inner_frame(event):
            canvas.itemconfig(window_id, width=event.width)
            canvas.configure(scrollregion=canvas.bbox("all"))
        canvas.bind("<Configure>", resize_inner_frame)

        # Scroll con mouse (usa helper común)
        bind_mousewheel(canvas, canvas)

        # --------- Card principal ---------
        card = tk.Frame(scrollable_frame, bg="white", highlightbackground=_EMPHASIS,
                        highlightcolor=_EMPHASIS, highlightthickness=1, bd=0)
        card.pack(fill="x", expand=False, padx=18, pady=16)

        card_header = tk.Frame(card, bg=_EMPHASIS)
        card_header.pack(fill="x", side="top")
        tk.Label(card_header, text="Herramientas disponibles", bg=_EMPHASIS, fg=_TEXT,
                 font=("Segoe UI", 11, "bold"), padx=10, pady=6).pack(anchor="w")

        card_body = tk.Frame(card, bg="white")
        card_body.pack(fill="x", padx=10, pady=12)

        info_label = tk.Label(
            card_body,
            text="Esta sección estará disponible próximamente.\n\nAquí podrás realizar diversos cálculos químicos y nutricionales.",
            font=("Segoe UI", 12),
            fg=_TEXT_SECONDARY,
            bg="white",
            justify="left"
        )
        info_label.pack(pady=(4, 16), anchor="w")

        # --------- Botones con paleta ---------
        buttons_frame = tk.Frame(card_body, bg="white")
        buttons_frame.pack(pady=8, anchor="w")

        def make_btn(parent, text, color_bg, color_active, cmd):
            btn = tk.Button(
                parent,
                text=text,
                font=("Segoe UI", 11, "bold"),
                bg=color_bg,
                fg="white",
                activebackground=color_active,
                activeforeground="white",
                relief="flat",
                bd=0,
                padx=18,
                pady=8,
                cursor="hand2",
                command=cmd
            )
            # Efecto hover simple
            def on_enter(_): btn.config(bg=color_active)
            def on_leave(_): btn.config(bg=color_bg)
            btn.bind("<Enter>", on_enter)
            btn.bind("<Leave>", on_leave)
            return btn

        # Primario (rojo), secundarios (azul grisáceo)
        btn1 = make_btn(buttons_frame, "Cálculo de pH", _PRIMARY, _PRIMARY_DARK, self._placeholder_action)
        btn1.pack(side="left", padx=(0, 10))
        btn2 = make_btn(buttons_frame, "Conversiones", _SECONDARY, _PRIMARY, self._placeholder_action)
        btn2.pack(side="left", padx=10)
        btn3 = make_btn(buttons_frame, "Concentraciones", _SECONDARY, _PRIMARY, self._placeholder_action)
        btn3.pack(side="left", padx=10)
    
    def _placeholder_action(self):
        """Acción placeholder para botones"""
        tk.messagebox.showinfo("Próximamente", "Esta funcionalidad estará disponible en futuras versiones.")