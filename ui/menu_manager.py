import tkinter as tk

class MenuManager:
    def __init__(self, parent_window):
        self.parent = parent_window
        self.menu_frame = None
        self.menu_visible = False

    def create_side_menu(self, sections):
        if hasattr(self.parent, "menu_frame") and self.parent.menu_frame is not None:
            try:
                self.parent.menu_frame.destroy()
            except:
                pass

        self.parent.menu_frame = tk.Toplevel(self.parent)
        self.parent.menu_frame.overrideredirect(True)
        self.parent.menu_frame.attributes('-topmost', True)
        self.parent.menu_frame.configure(bg="#0B5394")
        self.parent.menu_frame.transient(self.parent)

        canvas_bg = tk.Canvas(self.parent.menu_frame, bg="#0B5394", highlightthickness=0, bd=0)
        canvas_bg.pack(fill="both", expand=True)
        self.parent.menu_frame.update_idletasks()
        w = 260
        h = self.parent.winfo_height() - 60
        canvas_bg.create_rectangle(10, 10, w-10, h-10, fill="#0B5394", outline="#073763", width=2)

        content_frame = tk.Frame(canvas_bg, bg="#0B5394")
        canvas_bg.create_window((0, 0), window=content_frame, anchor="nw", width=w, height=h)

        # Botón "X" para cerrar el menú en la esquina superior derecha
        close_btn = tk.Button(
            canvas_bg,
            text="✕",
            font=("Segoe UI", 16, "bold"),
            bg="#0B5394",
            fg="white",
            bd=0,
            activebackground="#073763",
            activeforeground="#ffc107",
            command=self.hide_menu,
            cursor="hand2",
            highlightthickness=0
        )
        close_btn.place(x=w-38, y=12, width=28, height=28)

        menu_label = tk.Label(
            content_frame,
            text="Menú",
            bg="#0B5394",
            fg="white",
            font=("Segoe UI", 15, "bold")
        )
        menu_label.pack(pady=(25, 15), anchor="w", padx=30)

        self.parent.menu_buttons = []
        for section in sections:
            btn = tk.Button(
                content_frame,
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
                bd=0,
                highlightthickness=0,
                cursor="hand2",
                command=lambda s=section: [self.parent.show_section(s), self.hide_menu()]
            )
            btn.pack(fill="x", pady=2)
            self.parent.menu_buttons.append(btn)

            # Animación de resaltado al pasar el mouse
            def on_enter(e, b=btn):
                b.configure(bg="#1156b3", fg="#ffc107")
            def on_leave(e, b=btn):
                b.configure(bg="#0B5394", fg="white")
            btn.bind("<Enter>", on_enter)
            btn.bind("<Leave>", on_leave)

        sep = tk.Frame(content_frame, bg="#073763", height=2)
        sep.pack(fill="x", padx=20, pady=10)

        self.parent.update_idletasks()
        x = self.parent.winfo_rootx()
        y = self.parent.winfo_rooty()
        h = self.parent.winfo_height()
        header_height = 60
        menu_width = 260
        self.parent.menu_frame.geometry(f"{menu_width}x{h-header_height}+{x}+{y+header_height}")
        self.parent.menu_visible = True

    def hide_menu(self):
        if hasattr(self.parent, "menu_frame") and self.parent.menu_frame is not None:
            self.parent.menu_frame.withdraw()
            self.parent.menu_visible = False

    def toggle_menu(self):
        if hasattr(self.parent, "menu_frame") and self.parent.menu_frame is not None and self.parent.menu_visible:
            self.hide_menu()
        else:
            sections = getattr(self.parent, 'menu_sections', ["Inicio"])
            self.create_side_menu(sections)
            if hasattr(self.parent, "menu_frame") and self.parent.menu_frame is not None:
                self.parent.menu_frame.deiconify()
                self.parent.menu_visible = True