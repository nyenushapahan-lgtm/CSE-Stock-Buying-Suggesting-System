import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QTableWidgetItem, QMessageBox
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile
from src.services import handleThems
from PySide6.QtGui import QIcon, QPixmap

from src.services import checkUser,logger
from src.windows.main_window.MainWindow import MainWindow

class LoginWindow():
    def __init__(self):
        #create application first
        self.app = QApplication(sys.argv)

        self.login_window = None

        try:
            #make logger instance
            self.logMsg = logger.Logging()

            #load the Ui
            loader = QUiLoader()
            ui_file_path = "./resources/ui_files/login_form.ui"
            ui_file = QFile(ui_file_path)

            #open the file
            if not ui_file.open(QFile.ReadOnly):
                QMessageBox.critical(None,"File Error","Ui File Cannot be Opened !")
                sys.exit(-1)

            #load the file content into window
            self.login_window = loader.load(ui_file)
            ui_file.close()

            #load the theme & change the theme
            handleThems.load_stylesheet(app=self.app)

            #add file icon
            file_path = "./resources/icons/icon.png"
            self.login_window.setWindowIcon(QIcon(file_path))

            #connect the login Button
            self.login_window.loginBtn.clicked.connect(self.checkLogin)

            #show the window
            self.login_window.show()

        except Exception as e:
            QMessageBox.critical(None, "Error", f"Error: {str(e)}")
            sys.exit(-1)

    def checkLogin(self):
        #getting username & password
        username = self.login_window.usernameLineEdit.text()
        password = self.login_window.passwordLineEdit.text()

        if not all((username,password)):
            QMessageBox.critical(
                self.login_window,
                "Credential Error",
                "Username & Password Filed Cannot be Empty!"
                )
            return
        
        #pass the values for checking the user credentials
        chkUser = checkUser.CheckUser()
        success,dMessage,result =chkUser.checkUser(
            username=username,
            password=password
            )

        if not success:
            QMessageBox.critical(self.login_window, "Login Error ", dMessage)
            self.logMsg.error_message(message=dMessage)
            return

        #show successfull massage
        QMessageBox.information(self.login_window, "Login Status", "Successfully Loggined!")

        #add logger
        self.logMsg.info_message(message=dMessage + ", Successfully Logined !")

        #hide login window
        self.login_window.close()

        #creating main window instance
        self.main_window = MainWindow()

        #show the main window
        self.main_window.show()
        
            
    def run(self):
        """Start the application"""
        sys.exit(self.app.exec())