import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from src.windows.login_window.LoginWindow import LoginWindow


class LoginWindowTests(unittest.TestCase):
    def test_invalid_credentials_do_not_open_main_window(self):
        dummy_window = SimpleNamespace(
            usernameLineEdit=SimpleNamespace(text=lambda: "wrong"),
            passwordLineEdit=SimpleNamespace(text=lambda: "password"),
            close=Mock(),
        )

        login_window = LoginWindow.__new__(LoginWindow)
        login_window.login_window = dummy_window
        login_window.logMsg = Mock()

        with patch("src.windows.login_window.LoginWindow.QMessageBox.critical") as critical_mock, \
             patch("src.windows.login_window.LoginWindow.QMessageBox.information") as info_mock, \
             patch("src.windows.login_window.LoginWindow.checkUser.CheckUser.checkUser", return_value=(False, "Invalid credentials", None)) as check_user_mock, \
             patch("src.windows.login_window.LoginWindow.MainWindow") as main_window_cls:
            login_window.checkLogin()

        check_user_mock.assert_called_once_with(username="wrong", password="password")
        critical_mock.assert_called_once()
        info_mock.assert_not_called()
        dummy_window.close.assert_not_called()
        main_window_cls.assert_not_called()


if __name__ == "__main__":
    unittest.main()
