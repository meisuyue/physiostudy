from __future__ import annotations

import sys

from PyQt6.QtCore import QEvent, QPoint, Qt
from PyQt6.QtGui import QColor, QFont, QIcon, QLinearGradient, QPainter, QPainterPath, QPen, QPixmap
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

from .app_window import MainWindow
from .project_paths import DATA_DIR
from .storage import UserStore, load_login_memory, save_login_memory
from .tts_service import ensure_temp_tts_dir


ICON_DIR = DATA_DIR / "icons" / "default"


class GradientTextLabel(QLabel):
    def __init__(self, text: str = "", parent: QWidget | None = None) -> None:
        super().__init__(text, parent)
        self._left_color = QColor("#ff7f9a")
        self._right_color = QColor("#5f8fff")

    def set_gradient_colors(self, left: str, right: str) -> None:
        self._left_color = QColor(left)
        self._right_color = QColor(right)
        self.update()

    def paintEvent(self, event) -> None:  # type: ignore[override]
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        font = self.font()
        painter.setFont(font)
        rect = self.rect()
        path = QPainterPath()
        metrics = painter.fontMetrics()
        text = self.text()
        text_width = metrics.horizontalAdvance(text)
        text_height = metrics.ascent()
        x = (rect.width() - text_width) / 2
        y = (rect.height() + text_height) / 2 - 4
        path.addText(x, y, font, text)
        gradient = QLinearGradient(0, 0, rect.width(), 0)
        gradient.setColorAt(0.0, self._left_color)
        gradient.setColorAt(1.0, self._right_color)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(gradient)
        painter.drawPath(path)
        outline = QPen(QColor(255, 255, 255, 120), 1.2)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(outline)
        painter.drawPath(path)
        painter.end()


class LoginWindow(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("PhysioStudy Login")
        self.setFixedSize(900, 560)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)
        if (ICON_DIR / "logo.png").exists():
            self.setWindowIcon(QIcon(str(ICON_DIR / "logo.png")))

        self.store = UserStore()
        self._drag_pos: QPoint | None = None
        self.title_bar: QWidget | None = None
        self.main_window: MainWindow | None = None
        self.remember_checked, self.remembered_user, self.remembered_password = load_login_memory()

        self._build_ui()
        self._apply_login_memory()

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
        self.title_bar = title_bar
        title_bar.setFixedHeight(42)
        title_bar.installEventFilter(self)
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(0, 6, 8, 0)
        title_layout.addStretch()

        min_btn = QPushButton("–")
        close_btn = QPushButton("⨉")
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
        close_btn.clicked.connect(self.close)
        title_layout.addWidget(min_btn)
        title_layout.addWidget(close_btn)
        right_out_layout.addWidget(title_bar)

        panel = QWidget()
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(38, 6, 38, 28)
        panel_layout.setSpacing(14)

        app_title = GradientTextLabel("PhysioStudy")
        app_title.setFont(QFont("Segoe UI", 30, QFont.Weight.Bold))
        app_title.setFixedHeight(52)
        app_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        app_title.set_gradient_colors("#ff7d97", "#5e91ff")
        panel_layout.addWidget(app_title)

        subtitle = QLabel("登录或注册后开始学习")
        subtitle.setFont(QFont("Arial", 13))
        subtitle.setStyleSheet("color:#6d7d8b;")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        panel_layout.addWidget(subtitle)

        avatar = QLabel()
        avatar.setFixedSize(100, 100)
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar_path = ICON_DIR / "logo.png"
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
                background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1, stop: 0 #ff7d97, stop: 1 #5e91ff);
                color: white;
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
        self.remember_box = QCheckBox("记住密码")

        row = QHBoxLayout()
        row.addWidget(self.show_pwd)
        row.addStretch()
        row.addWidget(self.remember_box)

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

    def _apply_login_memory(self) -> None:
        self.remember_box.setChecked(self.remember_checked)
        if self.remember_checked:
            self.login_user.setText(self.remembered_user)
            self.login_pwd.setText(self.remembered_password)

    def _handle_login(self) -> None:
        user = self.login_user.text().strip()
        pwd = self.login_pwd.text()
        if not self.store.authenticate(user, pwd):
            QMessageBox.warning(self, "登录失败", "账号或密码不正确。")
            return
        save_login_memory(self.remember_box.isChecked(), user, pwd)
        self._enter_app(user)

    def _handle_register(self) -> None:
        user = self.reg_user.text().strip()
        pwd1 = self.reg_pwd.text()
        pwd2 = self.reg_pwd2.text()
        if not user or not pwd1:
            QMessageBox.information(self, "提示", "请填写账号和密码。")
            return
        if pwd1 != pwd2:
            QMessageBox.warning(self, "提示", "两次输入的密码不一致。")
            return
        if not self.store.register(user, pwd1):
            QMessageBox.warning(self, "提示", "注册失败：账号已存在或输入无效。")
            return
        save_login_memory(False)
        self._enter_app(user)

    def _enter_app(self, username: str) -> None:
        self.main_window = MainWindow(username=username)
        self.main_window.showMaximized()
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

    def eventFilter(self, watched, event) -> bool:  # type: ignore[override]
        if watched is self.title_bar:
            if event.type() == QEvent.Type.MouseButtonPress and event.button() == Qt.MouseButton.LeftButton:
                child = self.title_bar.childAt(event.position().toPoint()) if self.title_bar is not None else None
                if isinstance(child, QPushButton):
                    return False
                self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
                event.accept()
                return True
            if event.type() == QEvent.Type.MouseMove and self._drag_pos and event.buttons() & Qt.MouseButton.LeftButton:
                self.move(event.globalPosition().toPoint() - self._drag_pos)
                event.accept()
                return True
            if event.type() == QEvent.Type.MouseButtonRelease:
                self._drag_pos = None
        return super().eventFilter(watched, event)

    def mouseReleaseEvent(self, event) -> None:  # type: ignore[override]
        self._drag_pos = None
        super().mouseReleaseEvent(event)


def main() -> None:
    ensure_temp_tts_dir()
    app = QApplication(sys.argv)
    window = LoginWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
