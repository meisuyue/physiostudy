from __future__ import annotations

import sys
from pathlib import Path

from PyQt6.QtCore import QEasingCurve, QPoint, QPropertyAnimation, QRect, Qt, pyqtProperty
from PyQt6.QtGui import QColor, QFont, QIcon, QPainter, QPainterPath, QPixmap
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from app_window import MainWindow
from storage import UserStore


BASE_DIR = Path(__file__).resolve().parent
ICON_DIR = BASE_DIR / "data" / "icons" / "default"


class LoginWindow(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("PhysioWords Login")
        self.setFixedSize(900, 560)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)
        if (ICON_DIR / "logo.png").exists():
            self.setWindowIcon(QIcon(str(ICON_DIR / "logo.png")))

        self.store = UserStore()

        self._opacity = 1.0
        self._drag_pos: QPoint | None = None
        self.animation_opacity: QPropertyAnimation | None = None
        self.animation_geo: QPropertyAnimation | None = None
        self.main_window: MainWindow | None = None

        self._build_ui()

    def _build_ui(self) -> None:
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        left = QLabel()
        left.setFixedWidth(470)
        left.setScaledContents(True)
        left_bg = ICON_DIR / "where all micracles begin.jpg"
        if left_bg.exists():
            left.setPixmap(QPixmap(str(left_bg)))
        root.addWidget(left)

        right_out = QWidget()
        right_out.setStyleSheet("background:#f8fbff;")
        right_out_layout = QVBoxLayout(right_out)
        right_out_layout.setContentsMargins(0, 0, 0, 0)
        right_out_layout.setSpacing(0)

        title_bar = QWidget()
        title_bar.setFixedHeight(42)
        title_bar.setStyleSheet("background: transparent;")
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(0, 6, 8, 0)
        title_layout.addStretch()

        min_btn = QPushButton("—")
        close_btn = QPushButton("×")
        for btn in (min_btn, close_btn):
            btn.setFixedSize(32, 28)
            btn.setStyleSheet(
                """
                QPushButton {
                    border: none;
                    color: #3f4a56;
                    font-size: 18px;
                    background: rgba(255,255,255,0);
                }
                QPushButton:hover {
                    background: rgba(0, 0, 0, 0.08);
                    border-radius: 6px;
                }
                """
            )
        min_btn.clicked.connect(self.showMinimized)
        close_btn.clicked.connect(lambda: self.fade_out_close(50))
        title_layout.addWidget(min_btn)
        title_layout.addWidget(close_btn)
        right_out_layout.addWidget(title_bar)

        panel = QWidget()
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(38, 6, 38, 28)
        panel_layout.setSpacing(14)

        app_title = QLabel("PhysioWords")
        app_title.setFont(QFont("Arial", 28, QFont.Weight.Bold))
        app_title.setStyleSheet("color:#1b2d43;")
        panel_layout.addWidget(app_title)

        subtitle = QLabel("登录或注册后开始学习")
        subtitle.setFont(QFont("Arial", 13))
        subtitle.setStyleSheet("color:#6d7d8b;")
        panel_layout.addWidget(subtitle)

        avatar = QLabel()
        avatar.setFixedSize(100, 100)
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar_path = ICON_DIR / "默认头像.png"
        if avatar_path.exists():
            avatar_pix = QPixmap(str(avatar_path)).scaled(
                100,
                100,
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation,
            )
            avatar.setPixmap(self.make_circle_pixmap(avatar_pix))
        avatar_row = QHBoxLayout()
        avatar_row.addStretch()
        avatar_row.addWidget(avatar)
        avatar_row.addStretch()
        panel_layout.addLayout(avatar_row)

        self.stack = QStackedWidget()
        self.stack.setStyleSheet(
            """
            QLineEdit {
                border: 2px solid #c1d0dc;
                border-radius: 10px;
                padding: 10px;
                font-size: 15px;
                background: rgba(255,255,255,0.95);
            }
            QLineEdit:focus {
                border: 2px solid #4f8ec7;
                background: #ffffff;
            }
            QCheckBox {
                color: #4a5f72;
                font-size: 13px;
            }
            QPushButton#MainAction {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                            stop:0 #d9f2e6, stop:1 #b9dfff);
                color: #15324a;
                border-radius: 10px;
                padding: 11px;
                font-size: 19px;
                border: none;
            }
            QPushButton#MainAction:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                            stop:0 #c8ecdc, stop:1 #a6d4fa);
            }
            QPushButton#LinkBtn {
                border: none;
                background: transparent;
                color: #2c6aa3;
                font-size: 13px;
                text-align: center;
            }
            """
        )
        self.stack.addWidget(self._build_login_form())
        self.stack.addWidget(self._build_register_form())
        panel_layout.addWidget(self.stack)
        panel_layout.addStretch()

        right_out_layout.addWidget(panel)
        root.addWidget(right_out)

    def _build_login_form(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(12)

        self.login_user = QLineEdit()
        self.login_user.setPlaceholderText("请输入账号")
        self.login_pwd = QLineEdit()
        self.login_pwd.setPlaceholderText("请输入密码")
        self.login_pwd.setEchoMode(QLineEdit.EchoMode.Password)

        self.show_pwd = QCheckBox("显示密码")
        self.show_pwd.stateChanged.connect(
            lambda: self.login_pwd.setEchoMode(
                QLineEdit.EchoMode.Normal if self.show_pwd.isChecked() else QLineEdit.EchoMode.Password
            )
        )
        remember = QCheckBox("记住密码")

        row = QHBoxLayout()
        row.addWidget(self.show_pwd)
        row.addStretch()
        row.addWidget(remember)

        login_btn = QPushButton("登录")
        login_btn.setObjectName("MainAction")
        login_btn.clicked.connect(self._handle_login)

        to_register = QPushButton("没有账号？去注册")
        to_register.setObjectName("LinkBtn")
        to_register.clicked.connect(lambda: self.stack.setCurrentIndex(1))

        layout.addWidget(self.login_user)
        layout.addWidget(self.login_pwd)
        layout.addLayout(row)
        layout.addWidget(login_btn)
        layout.addWidget(to_register, alignment=Qt.AlignmentFlag.AlignCenter)
        return page

    def _build_register_form(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(12)

        self.reg_user = QLineEdit()
        self.reg_user.setPlaceholderText("请输入新账号")
        self.reg_pwd = QLineEdit()
        self.reg_pwd.setPlaceholderText("请输入密码")
        self.reg_pwd.setEchoMode(QLineEdit.EchoMode.Password)
        self.reg_pwd2 = QLineEdit()
        self.reg_pwd2.setPlaceholderText("请再次输入密码")
        self.reg_pwd2.setEchoMode(QLineEdit.EchoMode.Password)

        reg_btn = QPushButton("注册并进入")
        reg_btn.setObjectName("MainAction")
        reg_btn.clicked.connect(self._handle_register)

        to_login = QPushButton("已有账号？去登录")
        to_login.setObjectName("LinkBtn")
        to_login.clicked.connect(lambda: self.stack.setCurrentIndex(0))

        layout.addWidget(self.reg_user)
        layout.addWidget(self.reg_pwd)
        layout.addWidget(self.reg_pwd2)
        layout.addWidget(reg_btn)
        layout.addWidget(to_login, alignment=Qt.AlignmentFlag.AlignCenter)
        return page

    def _handle_login(self) -> None:
        user = self.login_user.text().strip()
        pwd = self.login_pwd.text()
        if not self.store.authenticate(user, pwd):
            QMessageBox.warning(self, "登录失败", "账号或密码不正确。")
            return
        self._enter_app(user)

    def _handle_register(self) -> None:
        user = self.reg_user.text().strip()
        pwd1 = self.reg_pwd.text()
        pwd2 = self.reg_pwd2.text()
        if not user or not pwd1:
            QMessageBox.information(self, "提示", "请填写账号和密码。")
            return
        if pwd1 != pwd2:
            QMessageBox.warning(self, "提示", "两次密码不一致。")
            return
        if not self.store.register(user, pwd1):
            QMessageBox.warning(self, "提示", "注册失败：账号已存在或输入无效。")
            return
        self._enter_app(user)

    def _enter_app(self, username: str) -> None:
        self.main_window = MainWindow(username=username)
        self.main_window.show()
        self.close()

    def make_circle_pixmap(self, pixmap: QPixmap) -> QPixmap:
        size = min(pixmap.width(), pixmap.height())
        final = QPixmap(size, size)
        final.fill(Qt.GlobalColor.transparent)
        painter = QPainter(final)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        path = QPainterPath()
        path.addEllipse(0, 0, size, size)
        painter.setClipPath(path)
        painter.drawPixmap(0, 0, pixmap)
        painter.end()
        return final

    def get_opacity(self) -> float:
        return self._opacity

    def set_opacity(self, value: float) -> None:
        self._opacity = value
        self.setWindowOpacity(value)

    opacity = pyqtProperty(float, fget=get_opacity, fset=set_opacity)

    def fade_out_close(self, move: int = 50) -> None:
        geo = self.geometry()
        self.animation_geo = QPropertyAnimation(self, b"geometry")
        self.animation_geo.setDuration(650)
        self.animation_geo.setStartValue(geo)
        self.animation_geo.setEndValue(QRect(geo.x(), geo.y() + move, geo.width(), geo.height()))
        self.animation_geo.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.animation_geo.start()

        self.animation_opacity = QPropertyAnimation(self, b"opacity")
        self.animation_opacity.setDuration(650)
        self.animation_opacity.setStartValue(1.0)
        self.animation_opacity.setEndValue(0.0)
        self.animation_opacity.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.animation_opacity.finished.connect(self.close)
        self.animation_opacity.start()

    def mousePressEvent(self, event) -> None:  # type: ignore[override]
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event) -> None:  # type: ignore[override]
        if self._drag_pos and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event) -> None:  # type: ignore[override]
        self._drag_pos = None
        super().mouseReleaseEvent(event)


def main() -> None:
    app = QApplication(sys.argv)
    window = LoginWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

