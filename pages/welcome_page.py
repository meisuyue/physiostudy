from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget


class WelcomePage(QWidget):
    cn_clicked = pyqtSignal()
    en_clicked = pyqtSignal()
    settings_clicked = pyqtSignal()
    review_marked_clicked = pyqtSignal()
    search_clicked = pyqtSignal()

    def __init__(self, username: str) -> None:
        super().__init__()
        self.username = username
        self._build_ui()

    def _build_ui(self) -> None:
        self.setStyleSheet(
            """
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                            stop:0 #cfd9df, stop:1 #e2ebf0);
            }
            QPushButton {
                padding: 14px 26px;
                font-size: 20px;
                border-radius: 14px;
                color: #0b2d39;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                            stop:0 #a1ffce, stop:1 #faffd1);
                border: 1px solid #b5d9c7;
                min-width: 180px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                            stop:0 #8be0b8, stop:1 #f0ffb8);
            }
            QPushButton#MiniBtn {
                padding: 14px 26px;
                font-size: 20px;
                border-radius: 14px;
                color: #0b2d39;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                            stop:0 #a1ffce, stop:1 #faffd1);
                border: 1px solid #b5d9c7;
                min-width: 180px;
            }
            QPushButton#MiniBtn:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                            stop:0 #8be0b8, stop:1 #f0ffb8);
            }
            """
        )

        top_row = QHBoxLayout()
        top_row.addStretch()
        btn_settings = QPushButton("设置")
        btn_settings.setObjectName("MiniBtn")
        btn_settings.clicked.connect(self.settings_clicked.emit)
        top_row.addWidget(btn_settings)

        title = QLabel("PhysioWords")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Arial", 36, QFont.Weight.Bold))

        welcome = QLabel(f"欢迎回来，{self.username}！\n请选择你的学习模式")
        welcome.setAlignment(Qt.AlignmentFlag.AlignCenter)
        welcome.setFont(QFont("Arial", 18))

        btn_cn = QPushButton("中文开始学习")
        btn_en = QPushButton("英文开始学习")
        btn_review = QPushButton("复习标记单词")
        btn_review.setObjectName("MiniBtn")
        btn_search = QPushButton("查询单词")
        btn_search.setObjectName("MiniBtn")

        btn_cn.clicked.connect(self.cn_clicked.emit)
        btn_en.clicked.connect(self.en_clicked.emit)
        btn_review.clicked.connect(self.review_marked_clicked.emit)
        btn_search.clicked.connect(self.search_clicked.emit)

        layout = QVBoxLayout(self)
        layout.setSpacing(24)
        layout.addLayout(top_row)
        layout.addStretch()
        layout.addWidget(title)
        layout.addWidget(welcome)
        layout.addSpacing(8)
        layout.addWidget(btn_cn, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(btn_en, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(btn_review, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(btn_search, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addStretch()
