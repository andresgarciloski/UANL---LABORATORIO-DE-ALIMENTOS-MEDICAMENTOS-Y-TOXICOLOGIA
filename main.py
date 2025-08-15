from ui.login_screen import LoginWindow
from ui.interface import MainInterface
from ui.interface_admin import MainInterfaceAdmin

def main():
    login = LoginWindow()
    # Este mainloop queda hasta que login.quit() sea llamado por el callback
    login.mainloop()

    # Tras cerrar/quit del login, revisar si hay credenciales
    resultado = getattr(login, "login_info", None)
    try:
        login.destroy()
    except Exception:
        pass

    if not resultado:
        # el usuario canceló o cerró la ventana
        return

    username = resultado.get("username")
    rol = resultado.get("rol")

    if rol == "usuario":
        app = MainInterface(username=username, rol=rol)
        app.mainloop()
    elif rol == "admin":
        app = MainInterfaceAdmin(username=username, rol=rol)
        app.mainloop()

if __name__ == "__main__":
    main()
