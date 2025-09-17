import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk, ImageDraw
import os
from ui.base_interface import _BG, _PRIMARY, _PRIMARY_DARK, _TEXT, _TEXT_SECONDARY, _SECONDARY, _EMPHASIS

# Cargar dinámicamente para evitar problemas de importación circular
def get_user_data_module():
    try:
        from core.user_data_function import get_user_data, update_user_profile
        return get_user_data, update_user_profile
    except ImportError as e:
        print(f"Error importando módulos de datos de usuario: {e}")
        return None, None


class UserProfileSection:
    def __init__(self, parent):
        self.parent = parent
        self.bruni_img = None
        self._header_photo = None  # ref para header
        self._header_h = 220  # altura del encabezado (antes 150)
        # Intentar cargar imagen (opcional)
        try:
            img_path = os.path.join(os.path.dirname(__file__), '..', 'img', 'bruni.png')
            img_path = os.path.abspath(img_path)
            if os.path.exists(img_path):
                # Cargar como avatar circular
                img = Image.open(img_path).resize((64, 64), Image.LANCZOS).convert("RGBA")
                mask = Image.new("L", (64, 64), 0)
                d = ImageDraw.Draw(mask)
                d.ellipse((0, 0, 64, 64), fill=255)
                img.putalpha(mask)
                self.bruni_img = ImageTk.PhotoImage(img)
        except Exception:
            self.bruni_img = None

    # Estilo moderno para entradas
    def _apply_input_style(self, entry):
        entry.configure(
            relief="flat",
            bd=0,
            highlightthickness=2,
            highlightbackground=_EMPHASIS,
            highlightcolor=_PRIMARY,
            bg=_BG,
            insertbackground=_TEXT,
        )

    def _get_img_path(self, name: str) -> str:
        return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "img", name))

    def _render_header(self, canvas: tk.Canvas, title: str, subtitle: str = ""):
        # Ajuste de tamaño (usar 'cover' para no deformar)
        width = max(canvas.winfo_width(), 540)
        height = self._header_h
        img_path = self._get_img_path("fcq3.jpg")
        if os.path.exists(img_path):
            try:
                base = Image.open(img_path).convert("RGB")
                # Escala tipo COVER
                scale = max(width / base.width, height / base.height)
                new_w, new_h = int(base.width * scale), int(base.height * scale)
                resized = base.resize((new_w, new_h), Image.LANCZOS)
                # Recorte centrado al tamaño objetivo
                left = max((new_w - width) // 2, 0)
                top = max((new_h - height) // 2, 0)
                final = resized.crop((left, top, left + width, top + height))
                self._header_photo = ImageTk.PhotoImage(final)

                canvas.delete("all")
                canvas.create_image(0, 0, anchor="nw", image=self._header_photo)
                canvas.create_rectangle(0, 0, width, height, fill=_PRIMARY, outline="", stipple="gray25")
            except Exception:
                canvas.delete("all")
                canvas.configure(bg=_PRIMARY)
        else:
            canvas.delete("all")
            canvas.configure(bg=_PRIMARY)

        # Texto
        canvas.create_text(24, height // 2 - 6, text=title, anchor="w", fill="white", font=("Segoe UI", 20, "bold"))
        if subtitle:
            canvas.create_text(24, height // 2 + 20, text=subtitle, anchor="w", fill="white", font=("Segoe UI", 11))

    def show_profile_section(self):
        """Muestra la sección de perfil con estilo más plano y moderno."""
        get_user_data, update_user_profile = get_user_data_module()
        if not get_user_data:
            messagebox.showerror("Error", "No se pudieron cargar los módulos de datos")
            return

        for widget in self.parent.content_frame.winfo_children():
            try:
                widget.destroy()
            except Exception:
                pass

        username = getattr(self.parent, 'username', None)
        if not username:
            messagebox.showerror("Error", "No se ha iniciado sesión correctamente")
            return
        user_data = get_user_data(username)
        if not user_data:
            messagebox.showerror("Error", "No se pudieron obtener los datos del usuario")
            return

        # Contenedor principal sin bordes
        main_frame = tk.Frame(self.parent.content_frame, bg=_BG)
        main_frame.pack(fill="both", expand=True)

        # Encabezado con imagen
        header_canvas = tk.Canvas(main_frame, height=self._header_h, highlightthickness=0, bd=0, bg=_PRIMARY)
        header_canvas.pack(fill="x")
        name_display = f"{user_data.get('nombre','')} {user_data.get('apellido','')}".strip() or user_data.get('username', '')
        self._render_header(header_canvas, "Mi Perfil", name_display)
        header_canvas.bind("<Configure>", lambda e: self._render_header(header_canvas, "Mi Perfil", name_display))

        # Contenido
        content_wrap = tk.Frame(main_frame, bg=_BG)
        content_wrap.pack(fill="both", expand=True, padx=36, pady=22)

        # Separador sutil
        tk.Frame(content_wrap, height=1, bg=_EMPHASIS).pack(fill="x", pady=(0, 18))

        # Formulario plano (sin 'card')
        form = tk.Frame(content_wrap, bg=_BG)
        form.pack(fill="x")

        campo_styles = {"font": ("Segoe UI", 10), "bg": _BG, "fg": _TEXT}
        title_styles = {"font": ("Segoe UI", 12, "bold"), "bg": _BG, "fg": _PRIMARY}

        # Valores
        self.nombre_var = tk.StringVar(value=user_data.get('nombre', ''))
        self.apellido_var = tk.StringVar(value=user_data.get('apellido', ''))
        self.email_var = tk.StringVar(value=user_data.get('email', ''))
        self.telefono_var = tk.StringVar(value=user_data.get('telefono', ''))
        self.current_password_var = tk.StringVar()
        self.new_password_var = tk.StringVar()
        self.confirm_password_var = tk.StringVar()

        # Información de cuenta (lectura)
        tk.Label(form, text="Información de Cuenta", **title_styles).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))
        tk.Label(form, text="Usuario", **campo_styles).grid(row=1, column=0, sticky="w", pady=3)
        tk.Label(form, text=user_data.get('username', ''), **campo_styles).grid(row=1, column=1, sticky="w", pady=3)
        tk.Label(form, text="Rol", **campo_styles).grid(row=2, column=0, sticky="w", pady=3)
        tk.Label(form, text=user_data.get('rol', 'usuario'), **campo_styles).grid(row=2, column=1, sticky="w", pady=3)
        tk.Label(form, text="Fecha de creación", **campo_styles).grid(row=3, column=0, sticky="w", pady=3)
        created_at = user_data.get('createdAt', '')
        if created_at:
            created_at = created_at.strftime('%d/%m/%Y') if hasattr(created_at, 'strftime') else str(created_at)
        tk.Label(form, text=created_at, **campo_styles).grid(row=3, column=1, sticky="w", pady=3)

        tk.Frame(form, height=1, bg=_EMPHASIS).grid(row=4, column=0, columnspan=2, sticky="ew", pady=14)
        tk.Label(form, text="Datos de contacto", **title_styles).grid(row=5, column=0, columnspan=2, sticky="w", pady=(0, 10))

        tk.Label(form, text="Email", **campo_styles).grid(row=6, column=0, sticky="w", pady=3)
        email_entry = tk.Entry(form, textvariable=self.email_var, font=("Segoe UI", 10))
        self._apply_input_style(email_entry)
        email_entry.grid(row=6, column=1, sticky="ew", pady=3)

        tk.Frame(form, height=1, bg=_EMPHASIS).grid(row=7, column=0, columnspan=2, sticky="ew", pady=14)
        tk.Label(form, text="Cambiar contraseña (opcional)", **title_styles).grid(row=8, column=0, columnspan=2, sticky="w", pady=(0, 10))

        tk.Label(form, text="Contraseña actual", **campo_styles).grid(row=9, column=0, sticky="w", pady=3)
        current_entry = tk.Entry(form, textvariable=self.current_password_var, show="*", font=("Segoe UI", 10))
        self._apply_input_style(current_entry)
        current_entry.grid(row=9, column=1, sticky="ew", pady=3)

        tk.Label(form, text="Nueva contraseña", **campo_styles).grid(row=10, column=0, sticky="w", pady=3)
        new_entry = tk.Entry(form, textvariable=self.new_password_var, show="*", font=("Segoe UI", 10))
        self._apply_input_style(new_entry)
        new_entry.grid(row=10, column=1, sticky="ew", pady=3)

        tk.Label(form, text="Confirmar contraseña", **campo_styles).grid(row=11, column=0, sticky="w", pady=3)
        confirm_entry = tk.Entry(form, textvariable=self.confirm_password_var, show="*", font=("Segoe UI", 10))
        self._apply_input_style(confirm_entry)
        confirm_entry.grid(row=11, column=1, sticky="ew", pady=3)

        form.columnconfigure(1, weight=1)

        note = tk.Label(
            content_wrap,
            text="Nota: En esta versión puedes modificar solo el correo electrónico y la contraseña.",
            font=("Segoe UI", 10, "italic"),
            fg=_TEXT, bg=_BG, wraplength=620, justify="left"
        )
        note.pack(fill="x", pady=(14, 8))

        actions = tk.Frame(content_wrap, bg=_BG)
        actions.pack(fill="x", pady=(8, 0))

        _update_user_profile = update_user_profile
        tk.Button(
            actions, text="Guardar cambios",
            font=("Segoe UI", 10, "bold"),
            bg=_PRIMARY, fg="white",
            activebackground=_PRIMARY_DARK, activeforeground="white",
            bd=0, cursor="hand2",
            command=lambda: self._save_profile(user_data.get('id'), _update_user_profile)
        ).pack(side="right", padx=(8, 0))

        tk.Button(
            actions, text="Cancelar",
            font=("Segoe UI", 10),
            bg=_BG, fg=_PRIMARY,
            activebackground=_BG, activeforeground=_PRIMARY,
            bd=0, cursor="hand2",
            relief="flat",
            command=self.show_profile_section
        ).pack(side="right")

    def _save_profile(self, user_id, update_user_profile):
        email = self.email_var.get().strip()
        current = self.current_password_var.get().strip()
        new = self.new_password_var.get().strip()
        confirm = self.confirm_password_var.get().strip()

        # Validaciones mínimas
        if not email:
            messagebox.showwarning("Validación", "El email no puede estar vacío.")
            return
        if any([current, new, confirm]):
            if not current or not new or not confirm:
                messagebox.showwarning("Validación", "Completa todos los campos de contraseña.")
                return
            if new != confirm:
                messagebox.showerror("Validación", "La nueva contraseña y su confirmación no coinciden.")
                return
            if len(new) < 6:
                messagebox.showwarning("Validación", "La nueva contraseña debe tener al menos 6 caracteres.")
                return

        try:
            # Preferir kwargs para ser tolerantes con la firma de update_user_profile
            kwargs = {"user_id": user_id, "email": email}
            if new:
                kwargs.update(current_password=current, new_password=new)
            result = update_user_profile(**kwargs)
        except TypeError:
            # Intento alternativo por si la función no acepta kwargs
            try:
                result = update_user_profile(user_id, email, current if new else None, new if new else None)
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo actualizar el perfil:\n{e}")
                return
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo actualizar el perfil:\n{e}")
            return

        if result is False:
            messagebox.showerror("Error", "La actualización fue rechazada por el servidor/validador.")
            return

        messagebox.showinfo("Perfil", "Cambios guardados correctamente.")
        # Refrescar vista
        self.show_profile_section()


def add_profile_to_menu(app):
    """
    Inserta 'Mi Perfil' en el menú/lateral de la app y enlaza la vista.
    Retorna el callback por si se quiere usar manualmente.
    """
    section = UserProfileSection(app)

    def _open_profile():
        section.show_profile_section()

    # Intentar integrarse con distintos tipos de menús de la app
    for meth_name in ("add_menu_item", "add_nav_item", "add_sidebar_item", "add_option"):
        if hasattr(app, meth_name):
            try:
                getattr(app, meth_name)("Mi Perfil", command=_open_profile)
                return _open_profile
            except TypeError:
                try:
                    getattr(app, meth_name)("Mi Perfil", _open_profile)
                    return _open_profile
                except Exception:
                    pass

    # Menú clásico de Tk
    if hasattr(app, "menu") and hasattr(app.menu, "add_command"):
        try:
            app.menu.add_command(label="Perfil", command=_open_profile)
            return _open_profile
        except Exception:
            pass

    # Lateral como Frame
    if hasattr(app, "side_menu") and isinstance(app.side_menu, tk.Misc):
        try:
            tk.Button(
                app.side_menu, text="Mi Perfil",
                bg=_BG, fg=_PRIMARY, bd=0, cursor="hand2",
                activebackground=_BG, activeforeground=_PRIMARY,
                relief="flat", command=_open_profile
            ).pack(fill="x", padx=8, pady=2)
            return _open_profile
        except Exception:
            pass

    # Si no hay menú detectable, devolver el callback para uso manual
    return _open_profile