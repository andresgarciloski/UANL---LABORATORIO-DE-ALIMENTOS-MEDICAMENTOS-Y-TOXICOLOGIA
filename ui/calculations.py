import tkinter as tk

class CalculationsSection:
    def __init__(self, parent):
        self.parent = parent
        
    def show_calculations_section(self):
        """Mostrar sección de cálculos"""
        # Frame principal
        main_frame = tk.Frame(self.parent.content_frame, bg="white")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Canvas y scrollbar para scroll
        canvas = tk.Canvas(main_frame, bg="white", highlightthickness=0)
        scrollbar = tk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        scrollable_frame = tk.Frame(canvas, bg="white")
        window_id = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

        def resize_inner_frame(event):
            canvas.itemconfig(window_id, width=event.width)
            canvas.configure(scrollregion=canvas.bbox("all"))
        canvas.bind("<Configure>", resize_inner_frame)

        # --- Scroll con mouse solo sobre el canvas ---
        def _on_mousewheel(event):
            try:
                if canvas.winfo_exists():
                    canvas.yview_scroll(int(-1*(event.delta/120)), "units")
            except tk.TclError:
                pass

        def _on_mousewheel_linux(event):
            try:
                if canvas.winfo_exists():
                    canvas.yview_scroll(int(-1*event.delta), "units")
            except tk.TclError:
                pass

        canvas.bind("<Enter>", lambda e: canvas.bind("<MouseWheel>", _on_mousewheel))
        canvas.bind("<Leave>", lambda e: canvas.unbind("<MouseWheel>"))
        canvas.bind("<Enter>", lambda e: canvas.bind("<Button-4>", _on_mousewheel_linux))
        canvas.bind("<Leave>", lambda e: canvas.unbind("<Button-4>"))
        canvas.bind("<Enter>", lambda e: canvas.bind("<Button-5>", _on_mousewheel_linux))
        canvas.bind("<Leave>", lambda e: canvas.unbind("<Button-5>"))
        # --- Fin scroll ---

        # Ahora pon los widgets dentro de scrollable_frame en vez de main_frame
        title_label = tk.Label(
            scrollable_frame,
            text="Módulo de Cálculos",
            font=("Segoe UI", 20, "bold"),
            fg="#0B5394",
            bg="white"
        )
        title_label.pack(pady=(0, 20))

        info_label = tk.Label(
            scrollable_frame,
            text="Esta sección estará disponible próximamente.\n\nAquí podrás realizar diversos cálculos químicos y nutricionales.",
            font=("Segoe UI", 14),
            fg="#666666",
            bg="white",
            justify="center"
        )
        info_label.pack(pady=20)

        buttons_frame = tk.Frame(scrollable_frame, bg="white")
        buttons_frame.pack(pady=20)

        btn_style = {
            "font": ("Segoe UI", 12, "bold"),
            "bg": "#0B5394",
            "fg": "white",
            "relief": "flat",
            "padx": 20,
            "pady": 10,
            "cursor": "hand2"
        }

        btn1 = tk.Button(
            buttons_frame,
            text="Cálculo de pH",
            **btn_style,
            command=self._placeholder_action
        )
        btn1.pack(side="left", padx=10)

        btn2 = tk.Button(
            buttons_frame,
            text="Conversiones",
            **btn_style,
            command=self._placeholder_action
        )
        btn2.pack(side="left", padx=10)

        btn3 = tk.Button(
            buttons_frame,
            text="Concentraciones",
            **btn_style,
            command=self._placeholder_action
        )
        btn3.pack(side="left", padx=10)
    
    def _placeholder_action(self):
        """Acción placeholder para botones"""
        tk.messagebox.showinfo("Próximamente", "Esta funcionalidad estará disponible en futuras versiones.")