from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import QUrl
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWidgets import QDialog, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from ..project_paths import DATA_DIR


HELP_DIR = DATA_DIR / "help"


class HelpCenterDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("帮助中心")
        self.setModal(True)
        self.resize(460, 420)
        self._build_ui()

    def _build_ui(self) -> None:
        self.setStyleSheet(
            """
            QDialog {
                background: rgba(246, 248, 255, 0.98);
            }
            QLabel#Title {
                color: #304db5;
                font-size: 24px;
                font-weight: 900;
            }
            QLabel#Hint {
                color: #6876a8;
                font-size: 14px;
                font-weight: 600;
            }
            QPushButton#HelpItem {
                text-align: left;
                padding: 14px 18px;
                border-radius: 16px;
                border: 1px solid rgba(197, 209, 255, 0.96);
                background: rgba(255, 255, 255, 0.92);
                color: #3d5ac0;
                font-size: 15px;
                font-weight: 800;
            }
            QPushButton#HelpItem:hover {
                background: rgba(240, 245, 255, 1.0);
            }
            QPushButton#CloseBtn {
                padding: 10px 20px;
                border-radius: 14px;
                border: 1px solid rgba(197, 209, 255, 0.96);
                background: white;
                color: #5a68a4;
                font-size: 14px;
                font-weight: 700;
            }
            """
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 22, 24, 20)
        layout.setSpacing(14)

        title = QLabel("帮助中心")
        title.setObjectName("Title")
        hint = QLabel("选择一个主题后，会使用默认浏览器打开对应说明页。")
        hint.setObjectName("Hint")

        layout.addWidget(title)
        layout.addWidget(hint)

        items = [
            ("单词学习", HELP_DIR / "word_study.html"),
            ("试题测试", HELP_DIR / "paper_test.html"),
            ("设置含义", HELP_DIR / "settings_meaning.html"),
            ("插图替换", HELP_DIR / "art_replacement.html"),
            ("进度复原", HELP_DIR / "progress_restore.html"),
            ("如何制作试卷", HELP_DIR / "how_to_make_papers.html"),
        ]
        for label, path in items:
            btn = QPushButton(label)
            btn.setObjectName("HelpItem")
            btn.clicked.connect(lambda _checked=False, p=path: self._open_help_file(p))
            layout.addWidget(btn)

        layout.addStretch()

        bottom = QHBoxLayout()
        bottom.addStretch()
        btn_close = QPushButton("关闭")
        btn_close.setObjectName("CloseBtn")
        btn_close.clicked.connect(self.reject)
        bottom.addWidget(btn_close)
        layout.addLayout(bottom)

    def _open_help_file(self, path: Path) -> None:
        if path.exists():
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))
        self.accept()
