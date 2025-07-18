import tkinter as tk

class MenuManager:
    def __init__(self, parent_window):
        self.parent = parent_window
        self.menu_frame = None
        self.menu_visible = True

    def create_side_menu(self, sections):
        """Crear menú lateral con secciones personalizadas"""
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

        self.update_side_menu_geometry()

        # Contenido del menú
        menu_label = tk.Label(
            self.parent.menu_frame,
            text="Menú",
            bg="#0B5394",
            fg="white",
            font=("Segoe UI", 15, "bold")
        )
        menu_label.pack(pady=(25, 15), anchor="w", padx=30)

        self.parent.menu_buttons = []
        for section in sections:
            btn = tk.Button(
                self.parent.menu_frame,
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
                command=lambda s=section: [self.parent.show_section(s), self.toggle_menu()]
            )
            btn.pack(fill="x", pady=2)
            self.parent.menu_buttons.append(btn)

        # Línea separadora
        sep = tk.Frame(self.parent.menu_frame, bg="#073763", height=2)
        sep.pack(fill="x", padx=20, pady=10)

        # Botón para cerrar el menú
        close_btn = tk.Button(
            self.parent.menu_frame,
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

        # Eventos
        self.parent.bind("<Configure>", self._on_window_configure)
        self.parent.menu_frame.bind("<FocusOut>", lambda e: None)

    def _on_window_configure(self, event):
        """Maneja cambios en la ventana principal"""
        if event.widget == self.parent and self.parent.menu_visible and hasattr(self.parent, "menu_frame"):
            self.parent.after_idle(self.update_side_menu_geometry)

    def update_side_menu_geometry(self):
        """Actualiza la geometría del menú lateral"""
        if not hasattr(self.parent, "menu_frame") or self.parent.menu_frame is None:
            return
            
        try:
            self.parent.update_idletasks()
            x = self.parent.winfo_rootx()
            y = self.parent.winfo_rooty()
            h = self.parent.winfo_height()
            header_height = 60
            
            if h > header_height and x >= 0 and y >= 0:
                self.parent.menu_frame.geometry(f"260x{h-header_height}+{x}+{y+header_height}")
        except Exception:
            pass

    def toggle_menu(self):
        """Toggle del menú"""
        try:
            if hasattr(self.parent, "menu_frame") and self.parent.menu_frame is not None and self.parent.menu_visible:
                self.parent.menu_frame.withdraw()
                self.parent.menu_visible = False
            else:
                sections = getattr(self.parent, 'menu_sections', ["Inicio"])
                self.create_side_menu(sections)
                if hasattr(self.parent, "menu_frame") and self.parent.menu_frame is not None:
                    self.parent.menu_frame.deiconify()
                    self.parent.menu_visible = True
        except Exception:
            self.parent.menu_visible = False