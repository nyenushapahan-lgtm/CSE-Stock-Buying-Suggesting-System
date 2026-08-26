from src.windows.login_window.LoginWindow import LoginWindow

class Main:
    def __init__(self):
        #call the login Window
        self.loginWindow = LoginWindow()

        #run the commands
        self.loginWindow.run()


if __name__ == "__main__":
    app_instance = Main()