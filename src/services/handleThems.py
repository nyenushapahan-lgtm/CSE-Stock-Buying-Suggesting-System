from PySide6.QtCore import QFile

#load the theme
def load_stylesheet(app, theme="light"):
    if theme=="light":
        theme_file = QFile("./resources/styles/light_theme.qss")

    else:
        theme_file = QFile("./resources/styles/dark_theme.qss")

    if theme_file.open(QFile.ReadOnly):
        stylesheet = theme_file.readAll().data().decode()

        app.setStyleSheet(stylesheet)

        theme_file.close()
        return True
    return False