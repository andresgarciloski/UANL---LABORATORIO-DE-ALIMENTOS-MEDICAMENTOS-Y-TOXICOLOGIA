import tkinter as tk
from tkinter import messagebox, simpledialog
from ui.interface import MainInterface
from ui.interface_admin import MainInterfaceAdmin  # Agrega este import al inicio
from PIL import Image, ImageTk, ImageDraw
import os

from core.auth import verificar_login
from ui.base_interface import _BG, _PRIMARY, _PRIMARY_DARK, _TEXT

# Tamaño único para ambos avatares
AVATAR_SIZE = 120

class LoginWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        # Configuración ventana principal
        self.title("UANL FoodLab")
        self.geometry("540x600")
        self.configure(bg=_BG)
        self.resizable(False, False)

        # refs para iconos (evitar GC)
        self._eye_icon = None
        self._eye_off_icon = None
        self._admin_icon = None
        self._arrow_icon = None

        self._user_pw_visible = False
        self._admin_pw_visible = False

        # Placeholders
        self._placeholders = {}  # entry -> text
        self._ph_color = "#9AA1A9"
        self._fg_color = "#111111"

        # Track de jobs programados con after
        self._after_jobs = set()
        # Cerrar de forma segura
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self.build_login_ui()

    # Interceptar after para registrar ids
    def after(self, ms, func=None, *args):
        job_id = super().after(ms, func, *args)
        # Solo registrar si hay callback (after sin callback devuelve tiempo restante)
        if func is not None:
            self._after_jobs.add(job_id)
        return job_id

    def after_cancel(self, job):
        try:
            super().after_cancel(job)
        finally:
            # Quitar del registro si estaba
            if job in self._after_jobs:
                self._after_jobs.discard(job)

    def _cancel_all_afters(self):
        # Cancelar cualquier after pendiente registrado en esta ventana
        jobs = list(self._after_jobs)
        for j in jobs:
            try:
                super().after_cancel(j)
            except Exception:
                pass
        self._after_jobs.clear()

    def _on_close(self):
        # Cancelar timers y destruir
        self._cancel_all_afters()
        self.destroy()

    # ------------- helpers UI -------------
    def _load_image(self, path, size):
        try:
            img = Image.open(path).convert("RGBA").resize(size, Image.LANCZOS)
            return ImageTk.PhotoImage(img)
        except Exception:
            return None

    def _get_img_path(self, name):
        return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "img", name))

    def _load_common_icons(self):
        # Ojo (mostrar/ocultar)
        eye = self._load_image(self._get_img_path("eye.jpg"), (22, 22))
        self._eye_icon = eye
        # Si no hay imagen, se usará texto en los botones

        # Admin icon
        # (no requerido por ahora)

    def _apply_input_style(self, entry):
        # Estilo de campo moderno (plano, sin borde, realce al foco)
        entry.configure(
            relief="flat",
            bd=0,
            highlightthickness=2,
            highlightbackground="#E6E8EC",
            highlightcolor=_PRIMARY,
            bg="#F7F8FA",
            insertbackground="#111111",
        )

    def _is_placeholder(self, entry):
        ph = self._placeholders.get(entry, None)
        return ph is not None and entry.get() == ph

    def _set_placeholder(self, entry, text, is_password=False, group="user"):
        # Inicial
        self._placeholders[entry] = text
        entry.delete(0, tk.END)
        entry.insert(0, text)
        entry.config(fg=self._ph_color)
        if is_password:
            # Mostrar placeholder en claro (sin *)
            entry.config(show="")

        def on_focus_in(e):
            if self._is_placeholder(entry):
                entry.delete(0, tk.END)
                entry.config(fg=self._fg_color)
                if is_password:
                    visible = (self._user_pw_visible if group == "user" else self._admin_pw_visible)
                    entry.config(show="" if visible else "*")

        def on_focus_out(e):
            if entry.get() == "":
                entry.insert(0, text)
                entry.config(fg=self._ph_color)
                if is_password:
                    entry.config(show="")

            # Recalcular estado del botón
            if group == "user":
                self._update_user_login_state()
            else:
                self._update_admin_login_state()

        def on_key(e):
            if group == "user":
                self._update_user_login_state()
            else:
                self._update_admin_login_state()

        entry.bind("<FocusIn>", on_focus_in)
        entry.bind("<FocusOut>", on_focus_out)
        entry.bind("<KeyRelease>", on_key)

    def _get_clean_value(self, entry):
        val = entry.get().strip()
        ph = self._placeholders.get(entry)
        return "" if val == ph else val

    def clear_ui(self):
        # Antes de destruir widgets, cancelar callbacks pendientes
        self._cancel_all_afters()
        for widget in self.winfo_children():
            widget.destroy()

    # ------------- Login usuario -------------
    def build_login_ui(self):
        self.clear_ui()
        self._load_common_icons()

        # Encabezado (alineado a la izquierda)
        header = tk.Frame(self, bg=_PRIMARY, height=64)
        header.pack(fill="x")
        tk.Label(
            header, text="Acceso de usuarios", bg=_PRIMARY, fg="white",
            font=("Segoe UI", 16, "bold")
        ).pack(side="left", padx=18, pady=14)

        # Avatar
        avatar_holder = tk.Frame(self, bg=_BG)
        avatar_holder.pack(pady=(28, 6))
        try:
            img_path = self._get_img_path("bruni.png")
            bruni_img = Image.open(img_path).resize((AVATAR_SIZE, AVATAR_SIZE), Image.LANCZOS)
            mask = Image.new('L', (AVATAR_SIZE, AVATAR_SIZE), 0)
            draw = ImageDraw.Draw(mask)
            draw.ellipse((0, 0, AVATAR_SIZE, AVATAR_SIZE), fill=255)
            bruni_img.putalpha(mask)
            bruni_photo = ImageTk.PhotoImage(bruni_img)
            lbl = tk.Label(avatar_holder, image=bruni_photo, bg=_BG)
            lbl.image = bruni_photo
            lbl.pack()
        except Exception:
            tk.Label(avatar_holder, text="🧪", font=("Segoe UI", 48), bg=_BG, fg=_PRIMARY).pack()

        # Contenido sin "card"
        content = tk.Frame(self, bg=_BG)
        content.pack(padx=24, pady=8, fill="x")

        tk.Label(
            content, text="Inicia sesión para continuar", bg=_BG, fg=_TEXT, font=("Segoe UI", 12)
        ).pack(anchor="w", pady=(4, 10))

        form = tk.Frame(content, bg=_BG)
        form.pack(fill="x")

        # Usuario
        user_row = tk.Frame(form, bg=_BG)
        user_row.pack(fill="x", pady=6)
        tk.Label(user_row, text="Usuario", bg=_BG, fg=_TEXT, font=("Segoe UI", 11)).pack(anchor="w")
        self.username_entry = tk.Entry(user_row, font=("Segoe UI", 12))
        self._apply_input_style(self.username_entry)
        self.username_entry.pack(fill="x", ipady=8)
        self._set_placeholder(self.username_entry, "Ej.: nombre.apellido", is_password=False, group="user")

        # Contraseña + botón ojo
        pass_row = tk.Frame(form, bg=_BG)
        pass_row.pack(fill="x", pady=10)
        tk.Label(pass_row, text="Contraseña", bg=_BG, fg=_TEXT, font=("Segoe UI", 11)).pack(anchor="w")
        pass_box = tk.Frame(pass_row, bg=_BG)
        pass_box.pack(fill="x")
        self.password_entry = tk.Entry(pass_box, show="*", font=("Segoe UI", 12))
        self._apply_input_style(self.password_entry)
        self.password_entry.pack(side="left", fill="x", expand=True, ipady=8)
        # Placeholder password
        self._set_placeholder(self.password_entry, "Ingresa tu contraseña", is_password=True, group="user")

        if self._eye_icon:
            toggle_btn = tk.Button(
                pass_box, image=self._eye_icon, bd=0, bg=_BG, activebackground=_BG,
                cursor="hand2", relief="flat", command=self._toggle_user_password
            )
        else:
            toggle_btn = tk.Button(
                pass_box, text="Mostrar", bd=0, bg=_BG, fg=_PRIMARY, activebackground=_BG,
                cursor="hand2", relief="flat", command=self._toggle_user_password
            )
        toggle_btn.pack(side="left", padx=(8, 0))

        # Botón entrar (plano, ancho) — empieza deshabilitado
        self._user_login_btn = tk.Button(
            content, text="Iniciar sesión", font=("Segoe UI", 12, "bold"),
            bg=_PRIMARY, fg="white", activebackground=_PRIMARY_DARK,
            activeforeground="white", relief="flat", height=2, command=self.authenticate
        )
        self._user_login_btn.pack(fill="x", pady=(14, 8))
        self._disable_button(self._user_login_btn)

        # Link para administrador
        link = tk.Button(
            content, text="¿Entrar como administrador?", bd=0, bg=_BG,
            fg=_PRIMARY, cursor="hand2", font=("Segoe UI", 10, "underline"),
            activebackground=_BG, activeforeground=_PRIMARY,
            command=self.build_admin_ui
        )
        link.pack(pady=(2, 6))

        # Bind teclas
        self.username_entry.bind('<Return>', lambda e: self.password_entry.focus())
        self.password_entry.bind('<Return>', lambda e: self.authenticate())
        self.username_entry.focus()

        # Estado inicial
        self._update_user_login_state()

    def _disable_button(self, btn):
        btn.config(state="disabled", bg="#C5C9CF", activebackground="#C5C9CF", cursor="arrow")

    def _enable_button(self, btn):
        btn.config(state="normal", bg=_PRIMARY, activebackground=_PRIMARY_DARK, cursor="hand2")

    def _update_user_login_state(self):
        u = self._get_clean_value(self.username_entry)
        p = self._get_clean_value(self.password_entry)
        if (u == "") and (p == ""):
            self._disable_button(self._user_login_btn)
        else:
            self._enable_button(self._user_login_btn)

    def _toggle_user_password(self):
        self._user_pw_visible = not self._user_pw_visible
        # Si hay placeholder, mantenerlo visible sin asteriscos
        if self._is_placeholder(self.password_entry):
            self.password_entry.config(show="")
        else:
            self.password_entry.config(show="" if self._user_pw_visible else "*")

    # ------------- Login admin -------------
    def build_admin_ui(self):
        self.clear_ui()
        self._load_common_icons()

        header = tk.Frame(self, bg=_PRIMARY, height=64)
        header.pack(fill="x")
        # Alineado a la izquierda (igual al de usuario)
        tk.Label(
            header, text="Acceso administrador", bg=_PRIMARY, fg="white",
            font=("Segoe UI", 16, "bold")
        ).pack(side="left", padx=18, pady=14)

        # Avatar admin
        avatar = tk.Frame(self, bg=_BG)
        avatar.pack(pady=(28, 6))
        try:
            img_path = self._get_img_path("bruni.png")
            admin_img = Image.open(img_path).resize((AVATAR_SIZE, AVATAR_SIZE), Image.LANCZOS)
            mask = Image.new('L', (AVATAR_SIZE, AVATAR_SIZE), 0)
            draw = ImageDraw.Draw(mask)
            draw.ellipse((0, 0, AVATAR_SIZE, AVATAR_SIZE), fill=255)
            admin_img.putalpha(mask)
            admin_photo = ImageTk.PhotoImage(admin_img)
            lbl = tk.Label(avatar, image=admin_photo, bg=_BG)
            lbl.image = admin_photo
            lbl.pack()
        except Exception:
            tk.Label(avatar, text="👤", font=("Segoe UI", 48), bg=_BG, fg=_PRIMARY).pack()

        # Contenido sin "card"
        content = tk.Frame(self, bg=_BG)
        content.pack(padx=24, pady=8, fill="x")

        tk.Label(content, text="Ingresa con credenciales de administrador", bg=_BG, fg=_TEXT, font=("Segoe UI", 12)).pack(anchor="w", pady=(4, 10))

        form = tk.Frame(content, bg=_BG)
        form.pack(fill="x")

        # Usuario admin
        user_row = tk.Frame(form, bg=_BG)
        user_row.pack(fill="x", pady=6)
        tk.Label(user_row, text="Usuario", bg=_BG, fg=_TEXT, font=("Segoe UI", 11)).pack(anchor="w")
        self.admin_username_entry = tk.Entry(user_row, font=("Segoe UI", 12))
        self._apply_input_style(self.admin_username_entry)
        self.admin_username_entry.pack(fill="x", ipady=8)
        self._set_placeholder(self.admin_username_entry, "Ej.: admin.uanl", is_password=False, group="admin")

        # Contraseña admin + ojo
        pass_row = tk.Frame(form, bg=_BG)
        pass_row.pack(fill="x", pady=10)
        tk.Label(pass_row, text="Contraseña", bg=_BG, fg=_TEXT, font=("Segoe UI", 11)).pack(anchor="w")
        pass_box = tk.Frame(pass_row, bg=_BG)
        pass_box.pack(fill="x")
        self.admin_password_entry = tk.Entry(pass_box, show="*", font=("Segoe UI", 12))
        self._apply_input_style(self.admin_password_entry)
        self.admin_password_entry.pack(side="left", fill="x", expand=True, ipady=8)
        self._set_placeholder(self.admin_password_entry, "Contraseña de administrador", is_password=True, group="admin")

        if self._eye_icon:
            toggle_btn = tk.Button(
                pass_box, image=self._eye_icon, bd=0, bg=_BG, activebackground=_BG,
                cursor="hand2", relief="flat", command=self._toggle_admin_password
            )
        else:
            toggle_btn = tk.Button(
                pass_box, text="Mostrar", bd=0, bg=_BG, fg=_PRIMARY, activebackground=_BG,
                cursor="hand2", relief="flat", command=self._toggle_admin_password
            )
        toggle_btn.pack(side="left", padx=(8, 0))

        # Botón entrar admin — empieza deshabilitado
        self._admin_login_btn = tk.Button(
            content, text="Iniciar sesión", font=("Segoe UI", 12, "bold"),
            bg=_PRIMARY, fg="white", activebackground=_PRIMARY_DARK,
            activeforeground="white", relief="flat", height=2, command=self.authenticate_admin
        )
        self._admin_login_btn.pack(fill="x", pady=(14, 8))
        self._disable_button(self._admin_login_btn)

        # Link volver a usuario
        link = tk.Button(
            content, text="← Volver a acceso de usuario", bd=0, bg=_BG,
            fg=_PRIMARY, cursor="hand2", font=("Segoe UI", 10, "underline"),
            activebackground=_BG, activeforeground=_PRIMARY,
            command=self.build_login_ui
        )
        link.pack(pady=(2, 6))

        # Binds
        self.admin_username_entry.bind('<Return>', lambda e: self.admin_password_entry.focus())
        self.admin_password_entry.bind('<Return>', lambda e: self.authenticate_admin())
        self.admin_username_entry.focus()

        # Estado inicial
        self._update_admin_login_state()

    def _update_admin_login_state(self):
        u = self._get_clean_value(self.admin_username_entry)
        p = self._get_clean_value(self.admin_password_entry)
        if (u == "") and (p == ""):
            self._disable_button(self._admin_login_btn)
        else:
            self._enable_button(self._admin_login_btn)

    def _toggle_admin_password(self):
        self._admin_pw_visible = not self._admin_pw_visible
        if self._is_placeholder(self.admin_password_entry):
            self.admin_password_entry.config(show="")
        else:
            self.admin_password_entry.config(show="" if self._admin_pw_visible else "*")

    # ------------- Autenticación (robustecida) -------------
    def authenticate(self):
        username = self._get_clean_value(self.username_entry)
        password = self._get_clean_value(self.password_entry)

        if username == "" and password == "":
            messagebox.showwarning("Campos vacíos", "Escribe tu usuario o contraseña para continuar.")
            return

        try:
            result = verificar_login(username, password)
        except Exception:
            messagebox.showerror("Error", "No se pudo verificar las credenciales. Intenta de nuevo.")
            return

        if isinstance(result, tuple) and result[0] is True:
            rol = result[1]
            if rol == "usuario":
                # Guardar resultado y salir del mainloop para que main.py abra la app principal
                self.login_info = {"username": username, "rol": rol}
                self.quit()
            else:
                messagebox.showerror("Acceso denegado", "Solo los usuarios pueden acceder desde este login.")
        else:
            messagebox.showerror("Error", "Usuario o contraseña incorrectos.")

    def authenticate_admin(self):
        username = self._get_clean_value(self.admin_username_entry)
        password = self._get_clean_value(self.admin_password_entry)

        if username == "" and password == "":
            messagebox.showwarning("Campos vacíos", "Escribe usuario o contraseña de administrador.")
            return

        try:
            result = verificar_login(username, password)
        except Exception:
            messagebox.showerror("Error", "No se pudo verificar las credenciales. Intenta de nuevo.")
            return

        if isinstance(result, tuple) and result[0] is True and result[1] == "admin":
            # Guardar resultado y salir del mainloop para que main.py abra la interfaz admin
            self.login_info = {"username": username, "rol": "admin"}
            self.quit()
        else:
            messagebox.showerror("Acceso denegado", "Solo los administradores pueden acceder aquí.")

    def submit_registration(self):
        # Registro deshabilitado deliberadamente
        messagebox.showwarning("Registro deshabilitado", "La creación de usuarios está deshabilitada.")