import tkinter as tk
from tkinter import ttk
from ui.base_interface import _BG, _PRIMARY, _TEXT

class LoadingOverlay:
    def __init__(self, toplevel, text="Procesando..."):
        self.root = toplevel.winfo_toplevel()
        self.text = text
        self._overlay = None
        self._bind_id = None
        self._pb = None

    def _position(self):
        try:
            x = self.root.winfo_rootx()
            y = self.root.winfo_rooty()
            w = self.root.winfo_width()
            h = self.root.winfo_height()
            self._overlay.geometry(f"{w}x{h}+{x}+{y}")
        except Exception:
            pass

    def show(self):
        if self._overlay and self._overlay.winfo_exists():
            return
        self._overlay = tk.Toplevel(self.root)
        self._overlay.overrideredirect(True)
        self._overlay.attributes("-topmost", True)
        # semitransparente (si está disponible en la plataforma)
        try:
            self._overlay.attributes("-alpha", 0.90)
        except Exception:
            pass
        self._overlay.configure(bg="#EEEEEE")
        self._position()
        self._bind_id = self.root.bind("<Configure>", lambda e: self._position())

        # Captura interacción
        try:
            self._overlay.grab_set()
        except Exception:
            pass

        container = tk.Frame(self._overlay, bg="#EEEEEE")
        container.pack(fill="both", expand=True)

        panel = tk.Frame(container, bg="white", bd=0, highlightthickness=1, highlightbackground="#CCCCCC")
        panel.place(relx=0.5, rely=0.5, anchor="center")

        lbl = tk.Label(panel, text=self.text, bg="white", fg=_TEXT, font=("Segoe UI", 11, "bold"))
        lbl.pack(padx=24, pady=(18, 6))

        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass
        style.configure("Loading.Horizontal.TProgressbar", troughcolor="#F0F0F0", background=_PRIMARY)

        self._pb = ttk.Progressbar(panel, mode="indeterminate", length=220, style="Loading.Horizontal.TProgressbar")
        self._pb.pack(padx=24, pady=(0, 18))
        try:
            self._pb.start(12)  # velocidad
        except Exception:
            pass

    def close(self):
        try:
            if self._pb:
                self._pb.stop()
        except Exception:
            pass
        try:
            if self._overlay and self._overlay.winfo_exists():
                self._overlay.grab_release()
        except Exception:
            pass
        try:
            if self._bind_id:
                self.root.unbind("<Configure>", self._bind_id)
        except Exception:
            pass
        try:
            if self._overlay and self._overlay.winfo_exists():
                self._overlay.destroy()
        except Exception:
            pass
        self._overlay = None
        self._pb = None
        self._bind_id = None