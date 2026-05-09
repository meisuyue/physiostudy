from __future__ import annotations

from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QFont, QIcon, QMovie, QPainter, QPixmap
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from ..project_paths import DATA_DIR
from ..storage import search_word_meanings


ICON_PATH = DATA_DIR / "icons" / "default" / "logo.png"
WORD_PAGE_BG_PATH = DATA_DIR / "icons" / "default" / "word_page.png"
THINKING_GIF_PATH = DATA_DIR / "icons" / "default" / "thinking.gif"


class SearchDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("\u67e5\u8be2\u5355\u8bcd")
        self.setWindowIcon(QIcon(str(ICON_PATH)) if ICON_PATH.exists() else QIcon())
        self.setModal(True)
        self.resize(1080, 860)
        self._background_pixmap = QPixmap(str(WORD_PAGE_BG_PATH)) if WORD_PAGE_BG_PATH.exists() else QPixmap()
        self._logo_pixmap = QPixmap(str(ICON_PATH)) if ICON_PATH.exists() else QPixmap()
        self._empty_movie: QMovie | None = None

        self.input_edit = QLineEdit()
        self.input_edit.setPlaceholderText("\u8f93\u5165\u8981\u67e5\u8be2\u7684\u5355\u8bcd\u6216\u5173\u952e\u8bcd")
        self.input_edit.returnPressed.connect(self._run_search)

        self.threshold = QComboBox()
        self.threshold.addItems(["40%", "50%", "60%", "70%", "80%", "90%"])
        self.threshold.setCurrentText("60%")

        self.result_area = QScrollArea()
        self.result_area.setWidgetResizable(True)
        self.result_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.result_area.setFrameShape(QFrame.Shape.NoFrame)

        self.result_host = QWidget()
        self.result_layout = QVBoxLayout(self.result_host)
        self.result_layout.setContentsMargins(0, 0, 0, 0)
        self.result_layout.setSpacing(14)
        self.result_area.setWidget(self.result_host)

        self.btn_search = QPushButton("\u67e5\u8be2")
        self.btn_search.setObjectName("SearchButton")
        self.btn_search.clicked.connect(self._run_search)
        self.btn_search.setAutoDefault(True)
        self.btn_search.setDefault(True)

        self.setStyleSheet(
            """
            QDialog {
                background: transparent;
            }
            QLabel {
                background: transparent;
            }
            QFrame#DialogPanel {
                background: rgba(255, 255, 255, 0.38);
                border: 1px solid rgba(190, 202, 255, 0.95);
                border-radius: 30px;
            }
            QFrame#TopBar {
                background: rgba(255, 255, 255, 0.18);
                border-bottom: 1px solid rgba(190, 202, 255, 0.8);
                border-top-left-radius: 30px;
                border-top-right-radius: 30px;
            }
            QLabel#DialogTitle {
                color: #173583;
                font-size: 28px;
                font-weight: 900;
            }
            QPushButton#CloseButton {
                border: none;
                background: transparent;
                color: rgba(123, 126, 189, 0.96);
                font-size: 36px;
                font-weight: 300;
                padding: 0 8px;
            }
            QPushButton#CloseButton:hover {
                color: #476adc;
            }
            QLabel#FieldLabel {
                color: #213b89;
                font-size: 17px;
                font-weight: 800;
            }
            QLineEdit, QComboBox {
                background: rgba(255, 255, 255, 0.86);
                border: 2px solid rgba(154, 183, 255, 0.95);
                border-radius: 18px;
                color: #21325f;
                font-size: 16px;
                padding: 14px 18px;
            }
            QLineEdit:focus, QComboBox:focus {
                border-color: rgba(102, 151, 255, 1.0);
            }
            QComboBox::drop-down {
                border: none;
                width: 28px;
            }
            QComboBox::down-arrow {
                image: none;
                width: 0;
                height: 0;
            }
            QPushButton#SearchButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                            stop:0 rgba(88, 145, 255, 0.98),
                                            stop:1 rgba(236, 141, 255, 0.98));
                color: white;
                border: 1px solid rgba(255, 255, 255, 0.92);
                border-radius: 22px;
                padding: 14px 24px;
                font-size: 20px;
                font-weight: 900;
            }
            QPushButton#SearchButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                            stop:0 rgba(76, 133, 245, 1.0),
                                            stop:1 rgba(226, 129, 247, 1.0));
            }
            QFrame#ResultStage {
                background: rgba(255, 255, 255, 0.36);
                border: 1px solid rgba(199, 210, 255, 0.9);
                border-radius: 26px;
            }
            QFrame#ResultCard {
                background: rgba(255, 255, 255, 0.7);
                border: 1px solid rgba(210, 218, 255, 0.95);
                border-radius: 20px;
            }
            QFrame#ResultCard[primary='true'] {
                border-color: rgba(255, 193, 92, 0.98);
                background: rgba(255, 255, 255, 0.82);
            }
            QLabel#RankBadge {
                background: rgba(255, 255, 255, 0.84);
                border: 1px solid rgba(219, 223, 240, 0.96);
                border-radius: 21px;
                color: #4a6ddc;
                font-size: 18px;
                font-weight: 900;
                min-width: 42px;
                max-width: 42px;
                min-height: 42px;
                max-height: 42px;
            }
            QLabel#RankBadge[primary='true'] {
                color: #f0ac24;
            }
            QLabel#ResultMain {
                color: #173c93;
                font-size: 20px;
                font-weight: 800;
            }
            QLabel#ResultLang {
                color: rgba(82, 99, 161, 0.95);
                font-size: 15px;
                font-weight: 700;
            }
            QLabel#ScoreChip {
                background: rgba(255, 255, 255, 0.86);
                border: 1px solid rgba(186, 195, 255, 0.95);
                border-radius: 18px;
                color: #4b6fe2;
                font-size: 14px;
                font-weight: 800;
                padding: 10px 18px;
            }
            QLabel#ScoreChip[primary='true'] {
                color: #db9215;
                border-color: rgba(255, 193, 92, 0.98);
            }
            QLabel#SearchEmpty {
                color: rgba(82, 99, 161, 0.92);
                font-size: 16px;
                font-weight: 700;
                padding: 40px;
            }
            """
        )

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 16, 20, 20)
        root.setSpacing(0)

        panel = QFrame()
        panel.setObjectName("DialogPanel")
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(0, 0, 0, 0)
        panel_layout.setSpacing(0)

        top_bar = QFrame()
        top_bar.setObjectName("TopBar")
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(26, 20, 26, 20)
        top_layout.setSpacing(16)

        logo = QLabel()
        if not self._logo_pixmap.isNull():
            logo.setPixmap(
                self._logo_pixmap.scaled(
                    56, 56, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
                )
            )
        top_layout.addWidget(logo)

        title = QLabel("\u67e5\u8be2\u5355\u8bcd")
        title.setObjectName("DialogTitle")
        title.setFont(QFont("Microsoft YaHei UI", 24, QFont.Weight.Black))
        top_layout.addWidget(title)
        top_layout.addStretch()

        close_btn = QPushButton("\u00d7")
        close_btn.setObjectName("CloseButton")
        close_btn.setAutoDefault(False)
        close_btn.setDefault(False)
        close_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        close_btn.clicked.connect(self.reject)
        # top_layout.addWidget(close_btn)
        panel_layout.addWidget(top_bar)

        body = QVBoxLayout()
        body.setContentsMargins(42, 28, 42, 30)
        body.setSpacing(18)

        query_row = QHBoxLayout()
        query_row.setSpacing(22)
        query_label = QLabel("\u67e5\u8be2\u5185\u5bb9")
        query_label.setObjectName("FieldLabel")
        query_label.setFixedWidth(110)
        query_row.addWidget(query_label)
        query_row.addWidget(self.input_edit, stretch=1)

        threshold_row = QHBoxLayout()
        threshold_row.setSpacing(22)
        threshold_label = QLabel("\u5339\u914d\u9608\u503c")
        threshold_label.setObjectName("FieldLabel")
        threshold_label.setFixedWidth(110)
        threshold_row.addWidget(threshold_label)
        threshold_row.addWidget(self.threshold, stretch=1)

        button_row = QHBoxLayout()
        button_row.addStretch()
        button_row.addSpacing(60)
        self.btn_search.setMinimumWidth(580)
        button_row.addWidget(self.btn_search)
        button_row.addStretch()

        result_stage = QFrame()
        result_stage.setObjectName("ResultStage")
        result_layout = QVBoxLayout(result_stage)
        result_layout.setContentsMargins(18, 18, 18, 18)
        result_layout.addWidget(self.result_area)

        body.addLayout(query_row)
        body.addLayout(threshold_row)
        body.addLayout(button_row)
        body.addWidget(result_stage, stretch=1)
        panel_layout.addLayout(body, stretch=1)

        root.addWidget(panel)
        self._show_empty("\u8f93\u5165\u5173\u952e\u8bcd\u540e\u5f00\u59cb\u67e5\u8be2\u3002")

    def _run_search(self) -> None:
        query = self.input_edit.text().strip()
        if not query:
            self._show_empty("\u8bf7\u8f93\u5165\u67e5\u8be2\u5185\u5bb9\u3002")
            return
        threshold = float(self.threshold.currentText().rstrip("%")) / 100.0
        results = search_word_meanings(query, threshold=threshold)
        if not results:
            self._show_empty("\u6ca1\u6709\u627e\u5230\u7b26\u5408\u9608\u503c\u7684\u7ed3\u679c\u3002", show_thinking=True)
            return

        self._clear_results()
        for index, (lang, key, meaning, score) in enumerate(results, start=1):
            self.result_layout.addWidget(self._build_result_card(index, lang, key, meaning, score))
        self.result_layout.addStretch()

    def _clear_results(self) -> None:
        if self._empty_movie is not None:
            self._empty_movie.stop()
            self._empty_movie = None
        while self.result_layout.count():
            item = self.result_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def _show_empty(self, text: str, show_thinking: bool = False) -> None:
        self._clear_results()
        empty = QLabel(text)
        empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty.setObjectName("SearchEmpty")
        self.result_layout.addWidget(empty)
        if show_thinking and THINKING_GIF_PATH.exists():
            gif_label = QLabel()
            gif_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._empty_movie = QMovie(str(THINKING_GIF_PATH))
            self._empty_movie.setScaledSize(QSize(220, 220))
            gif_label.setMovie(self._empty_movie)
            self.result_layout.addWidget(gif_label, alignment=Qt.AlignmentFlag.AlignHCenter)
            self._empty_movie.start()
        self.result_layout.addStretch()

    def _build_result_card(self, rank: int, lang: str, key: str, meaning: str, score: float) -> QFrame:
        card = QFrame()
        card.setObjectName("ResultCard")
        card.setProperty("primary", rank == 1)
        card.style().unpolish(card)
        card.style().polish(card)

        layout = QHBoxLayout(card)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(16)

        badge = QLabel("\u2655" if rank == 1 else str(rank))
        badge.setObjectName("RankBadge")
        badge.setProperty("primary", rank == 1)
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge.style().unpolish(badge)
        badge.style().polish(badge)
        layout.addWidget(badge, alignment=Qt.AlignmentFlag.AlignVCenter)

        text_col = QVBoxLayout()
        text_col.setSpacing(6)
        lang_label = "\u4e2d\u6587" if lang == "c" else "\u82f1\u6587"

        main = QLabel(f"[{lang_label}] {key}  \u2192  {meaning}")
        main.setObjectName("ResultMain")
        main.setWordWrap(True)

        sub = QLabel(f"\u5339\u914d\u7ed3\u679c #{rank}")
        sub.setObjectName("ResultLang")
        text_col.addWidget(main)
        text_col.addWidget(sub)
        layout.addLayout(text_col, stretch=1)

        score_chip = QLabel(f"\u5339\u914d\u5ea6 {score:.2f}")
        score_chip.setObjectName("ScoreChip")
        score_chip.setProperty("primary", rank == 1)
        score_chip.setAlignment(Qt.AlignmentFlag.AlignCenter)
        score_chip.style().unpolish(score_chip)
        score_chip.style().polish(score_chip)
        layout.addWidget(score_chip, alignment=Qt.AlignmentFlag.AlignVCenter)
        return card

    def paintEvent(self, event) -> None:  # type: ignore[override]
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        if not self._background_pixmap.isNull():
            painter.drawPixmap(self.rect(), self._background_pixmap)
        else:
            painter.fillRect(self.rect(), Qt.GlobalColor.white)
        painter.end()
