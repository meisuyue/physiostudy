from __future__ import annotations

import random
from pathlib import Path
from typing import List

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QPainter, QPixmap
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from ..project_paths import DATA_DIR
from ..storage import PaperInfo


BG_PATH = DATA_DIR / "icons" / "default" / "word_page.png"
LOGO_PATH = DATA_DIR / "icons" / "default" / "logo.png"
ITEMS_DIR = DATA_DIR / "icons" / "items"


class PaperOptionCard(QFrame):
    clicked = pyqtSignal(str)
    double_clicked = pyqtSignal(str)

    def __init__(
        self,
        key: str,
        title: str,
        subtitle: str,
        question_count: int,
        icon_path: Path | None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.key = key
        self._selected = False
        self._icon_pixmap = QPixmap(str(icon_path)) if icon_path and icon_path.exists() else QPixmap()
        self._title_text = title
        self._subtitle_text = subtitle
        self._question_count = question_count
        self._build_ui()
        self._apply_selected_style()

    def _build_ui(self) -> None:
        self.setObjectName("PaperCard")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(108)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(22, 18, 22, 18)
        layout.setSpacing(18)

        self.check_label = QLabel("○")
        self.check_label.setObjectName("CheckLabel")
        self.check_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.check_label.setFixedWidth(32)
        layout.addWidget(self.check_label, alignment=Qt.AlignmentFlag.AlignVCenter)

        self.icon_wrap = QFrame()
        self.icon_wrap.setObjectName("IconWrap")
        self.icon_wrap.setFixedSize(64, 64)
        icon_layout = QVBoxLayout(self.icon_wrap)
        icon_layout.setContentsMargins(10, 10, 10, 10)

        self.icon_label = QLabel()
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if not self._icon_pixmap.isNull():
            self.icon_label.setPixmap(
                self._icon_pixmap.scaled(
                    42,
                    42,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
        else:
            self.icon_label.setText("题")
            self.icon_label.setObjectName("FallbackIcon")
        icon_layout.addWidget(self.icon_label)
        layout.addWidget(self.icon_wrap, alignment=Qt.AlignmentFlag.AlignVCenter)

        text_col = QVBoxLayout()
        text_col.setSpacing(6)
        self.title_label = QLabel(self._title_text)
        self.title_label.setObjectName("CardTitle")
        self.title_label.setWordWrap(True)

        self.subtitle_label = QLabel(self._subtitle_text)
        self.subtitle_label.setObjectName("CardSubtitle")
        self.subtitle_label.setWordWrap(True)

        text_col.addStretch()
        text_col.addWidget(self.title_label)
        text_col.addWidget(self.subtitle_label)
        text_col.addStretch()
        layout.addLayout(text_col, stretch=1)

        right_col = QHBoxLayout()
        right_col.setSpacing(16)
        right_col.addStretch()

        self.count_chip = QLabel(f"{self._question_count}题")
        self.count_chip.setObjectName("CountChip")
        self.count_chip.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.count_chip.setMinimumWidth(80)

        self.arrow_label = QLabel("›")
        self.arrow_label.setObjectName("ArrowLabel")
        self.arrow_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.arrow_label.setFixedWidth(18)

        right_col.addWidget(self.count_chip, alignment=Qt.AlignmentFlag.AlignVCenter)
        right_col.addWidget(self.arrow_label, alignment=Qt.AlignmentFlag.AlignVCenter)
        layout.addLayout(right_col)

    def set_selected(self, selected: bool) -> None:
        self._selected = selected
        self._apply_selected_style()

    def _apply_selected_style(self) -> None:
        border_color = "rgba(115, 152, 255, 0.96)" if self._selected else "rgba(221, 227, 255, 0.96)"
        background = "rgba(255, 255, 255, 0.84)" if self._selected else "rgba(255, 255, 255, 0.74)"
        self.setStyleSheet(
            f"""
            QFrame#PaperCard {{
                background: {background};
                border: 1px solid {border_color};
                border-radius: 24px;
            }}
            QFrame#PaperCard:hover {{
                background: rgba(255, 255, 255, 0.9);
                border-color: rgba(136, 169, 255, 1.0);
            }}
            QLabel#CheckLabel {{
                color: {'#4d88f4' if self._selected else 'rgba(171, 181, 231, 0.95)'};
                font-size: 24px;
                font-weight: 800;
            }}
            QFrame#IconWrap {{
                background: rgba(255, 255, 255, 0.72);
                border: 1px solid rgba(189, 206, 255, 0.95);
                border-radius: 18px;
            }}
            QLabel#FallbackIcon {{
                color: #5a87f6;
                font-size: 24px;
                font-weight: 900;
            }}
            QLabel#CardTitle {{
                color: #1d2e72;
                font-size: 19px;
                font-weight: 900;
            }}
            QLabel#CardSubtitle {{
                color: rgba(88, 104, 164, 0.9);
                font-size: 13px;
                font-weight: 500;
            }}
            QLabel#CountChip {{
                background: rgba(255, 255, 255, 0.82);
                color: #4f73ea;
                border: 1px solid rgba(176, 191, 255, 0.96);
                border-radius: 16px;
                padding: 7px 12px;
                font-size: 13px;
                font-weight: 800;
            }}
            QLabel#ArrowLabel {{
                color: rgba(126, 146, 232, 0.96);
                font-size: 28px;
                font-weight: 500;
            }}
            """
        )
        self.check_label.setText("●" if self._selected else "○")

    def mousePressEvent(self, event) -> None:  # type: ignore[override]
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.key)
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event) -> None:  # type: ignore[override]
        if event.button() == Qt.MouseButton.LeftButton:
            self.double_clicked.emit(self.key)
        super().mouseDoubleClickEvent(event)


class PaperSelectPage(QWidget):
    back_home_clicked = pyqtSignal()
    start_paper_clicked = pyqtSignal(str)
    RANDOM_ALL_PAPERS_KEY = "__random_all_papers__"

    def __init__(self, papers: List[PaperInfo]) -> None:
        super().__init__()
        self.papers = papers
        self._background_pixmap = QPixmap(str(BG_PATH)) if BG_PATH.exists() else QPixmap()
        self._logo_pixmap = QPixmap(str(LOGO_PATH)) if LOGO_PATH.exists() else QPixmap()
        self._selected_key: str | None = None
        self._cards: dict[str, PaperOptionCard] = {}
        self._item_icons = self._build_item_icon_assignment()
        self._build_ui()
        self._load_cards()

    def _build_ui(self) -> None:
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        self.setStyleSheet(
            """
            QLabel {
                background: transparent;
            }
            QFrame#TopBar {
                background: rgba(255, 255, 255, 0.76);
                border: 1px solid rgba(255, 255, 255, 0.92);
            }
            QLabel#AppTitle {
                color: #243f92;
                font-size: 20px;
                font-weight: 800;
            }
            QPushButton#BackButton {
                background: rgba(255, 255, 255, 0.88);
                color: #466bdb;
                border: 1px solid rgba(255, 255, 255, 0.96);
                border-radius: 22px;
                padding: 14px 28px;
                font-size: 16px;
                font-weight: 700;
            }
            QPushButton#BackButton:hover {
                background: rgba(255, 255, 255, 0.96);
            }
            QLabel#Title {
                color: #1f388d;
                font-size: 34px;
                font-weight: 900;
            }
            QLabel#SubTitle {
                color: rgba(82, 104, 176, 0.96);
                font-size: 16px;
                font-weight: 700;
            }
            QLabel#DividerDot {
                color: rgba(176, 153, 255, 0.94);
                font-size: 18px;
                font-weight: 800;
            }
            QFrame#DividerLine {
                background: rgba(215, 187, 255, 0.84);
                min-height: 2px;
                max-height: 2px;
                border-radius: 2px;
            }
            QFrame#SelectionGroup {
                background: transparent;
            }
            QFrame#CardStage {
                background: rgba(255, 255, 255, 0.44);
                border: 1px solid rgba(255, 255, 255, 0.88);
                border-radius: 28px;
            }
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollArea > QWidget > QWidget {
                background: transparent;
            }
            QFrame#BottomInfo {
                background: rgba(255, 255, 255, 0.74);
                border: 1px solid rgba(255, 255, 255, 0.9);
                border-radius: 22px;
            }
            QLabel#BottomText {
                color: #2d499f;
                font-size: 16px;
                font-weight: 700;
            }
            QPushButton#StartButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                            stop:0 rgba(108, 161, 255, 0.96),
                                            stop:1 rgba(189, 120, 255, 0.96));
                color: white;
                border: 1px solid rgba(255, 255, 255, 0.88);
                border-radius: 24px;
                padding: 16px 36px;
                font-size: 18px;
                font-weight: 900;
                min-width: 250px;
            }
            QPushButton#StartButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                            stop:0 rgba(96, 150, 247, 0.98),
                                            stop:1 rgba(177, 110, 246, 0.98));
            }
            QPushButton#StartButton:disabled {
                background: rgba(196, 205, 232, 0.88);
                color: rgba(255, 255, 255, 0.92);
            }
            QLabel#EmptyLabel {
                color: rgba(84, 101, 160, 0.92);
                font-size: 15px;
                font-weight: 700;
                padding: 24px;
            }
            """
        )

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self._build_top_bar())

        content = QVBoxLayout()
        content.setContentsMargins(44, 30, 44, 30)
        content.setSpacing(18)

        self.btn_back_home = QPushButton("← 返回首页")
        self.btn_back_home.setObjectName("BackButton")
        self.btn_back_home.clicked.connect(self.back_home_clicked.emit)
        content.addWidget(self.btn_back_home, alignment=Qt.AlignmentFlag.AlignLeft)

        title = QLabel("选择试题")
        title.setObjectName("Title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Microsoft YaHei UI", 32, QFont.Weight.Black))

        subtitle = QLabel("请选择一个题库开始练习")
        subtitle.setObjectName("SubTitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)

        divider = QHBoxLayout()
        divider.addStretch()
        left_line = QFrame()
        left_line.setObjectName("DividerLine")
        left_line.setFixedWidth(120)
        left_dot = QLabel("•")
        left_dot.setObjectName("DividerDot")
        right_dot = QLabel("•")
        right_dot.setObjectName("DividerDot")
        right_line = QFrame()
        right_line.setObjectName("DividerLine")
        right_line.setFixedWidth(120)
        divider.addWidget(left_line)
        divider.addSpacing(10)
        divider.addWidget(left_dot)
        divider.addSpacing(12)
        divider.addWidget(subtitle)
        divider.addSpacing(12)
        divider.addWidget(right_dot)
        divider.addSpacing(10)
        divider.addWidget(right_line)
        divider.addStretch()

        self.selection_group = QFrame()
        self.selection_group.setObjectName("SelectionGroup")
        self.selection_group.setMaximumWidth(1280)
        group_layout = QVBoxLayout(self.selection_group)
        group_layout.setContentsMargins(0, 0, 0, 0)
        group_layout.setSpacing(18)

        self.stage = QFrame()
        self.stage.setObjectName("CardStage")
        self.stage.setMinimumWidth(1120)
        self.stage.setMaximumWidth(1280)
        stage_layout = QVBoxLayout(self.stage)
        stage_layout.setContentsMargins(18, 20, 18, 20)
        stage_layout.setSpacing(0)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll.setMinimumHeight(560)

        self.list_host = QWidget()
        self.list_layout = QVBoxLayout(self.list_host)
        self.list_layout.setContentsMargins(0, 0, 0, 0)
        self.list_layout.setSpacing(12)
        self.scroll.setWidget(self.list_host)

        self.empty_label = QLabel("当前没有可用试卷。")
        self.empty_label.setObjectName("EmptyLabel")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        stage_layout.addWidget(self.scroll)
        stage_layout.addWidget(self.empty_label)

        self.bottom_wrap = QWidget()
        bottom_row = QHBoxLayout(self.bottom_wrap)
        bottom_row.setContentsMargins(0, 0, 0, 0)
        bottom_row.setSpacing(18)

        self.selection_info = QFrame()
        self.selection_info.setObjectName("BottomInfo")
        info_layout = QHBoxLayout(self.selection_info)
        info_layout.setContentsMargins(24, 18, 24, 18)
        info_layout.setSpacing(12)
        self.selection_icon = QLabel("◉")
        self.selection_icon.setStyleSheet("color:#4d88f4; font-size: 22px; font-weight: 800;")
        self.selection_text = QLabel("已选择：")
        self.selection_text.setObjectName("BottomText")
        self.selection_text.setWordWrap(True)
        info_layout.addWidget(self.selection_icon)
        info_layout.addWidget(self.selection_text, stretch=1)

        self.btn_start = QPushButton(f"{' '*10}开始测试{' '*20}⨠")
        self.btn_start.setObjectName("StartButton")
        self.btn_start.clicked.connect(self._emit_selected_paper)

        bottom_row.addWidget(self.selection_info, stretch=3)
        bottom_row.addWidget(self.btn_start, stretch=1, alignment=Qt.AlignmentFlag.AlignVCenter)

        group_layout.addWidget(self.stage)
        group_layout.addWidget(self.bottom_wrap)

        content.addWidget(title)
        content.addLayout(divider)
        content.addSpacing(8)
        content.addWidget(self.selection_group, alignment=Qt.AlignmentFlag.AlignHCenter)
        content.addStretch()

        root.addLayout(content, stretch=1)

    def _build_top_bar(self) -> QFrame:
        bar = QFrame()
        bar.setObjectName("TopBar")
        bar.setFixedHeight(58)
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(18, 10, 18, 10)
        layout.setSpacing(12)

        logo = QLabel()
        if not self._logo_pixmap.isNull():
            logo.setPixmap(
                self._logo_pixmap.scaled(
                    34,
                    34,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
        layout.addWidget(logo)

        title = QLabel("Physiology Quize Imitation")
        title.setObjectName("AppTitle")
        layout.addWidget(title)
        layout.addStretch()
        return bar

    def _build_item_icon_assignment(self) -> List[Path | None]:
        icon_paths = (
            sorted(
                [
                    path
                    for path in ITEMS_DIR.iterdir()
                    if path.is_file() and path.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}
                ]
            )
            if ITEMS_DIR.exists()
            else []
        )

        total_items = len(self.papers) + (1 if sum(paper.question_count for paper in self.papers) > 0 else 0)
        if total_items <= 0:
            return []
        if not icon_paths:
            return [None] * total_items
        if total_items <= len(icon_paths):
            return random.sample(icon_paths, total_items)
        return [random.choice(icon_paths) for _ in range(total_items)]

    def _clear_cards(self) -> None:
        while self.list_layout.count():
            item = self.list_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        self._cards.clear()

    def _load_cards(self) -> None:
        self._clear_cards()
        descriptors: List[tuple[str, str, str, int]] = []

        total_questions = sum(paper.question_count for paper in self.papers)
        if total_questions > 0:
            random_count = min(100, total_questions)
            descriptors.append(
                (
                    self.RANDOM_ALL_PAPERS_KEY,
                    "所有试题随机抽取",
                    "从全部题库中随机抽取试题进行练习",
                    random_count,
                )
            )

        for paper in self.papers:
            descriptors.append(
                (
                    paper.filename,
                    paper.name,
                    paper.title or f"{paper.name} 题库练习",
                    paper.question_count,
                )
            )

        for index, (key, title, subtitle, count) in enumerate(descriptors):
            icon_path = self._item_icons[index] if index < len(self._item_icons) else None
            card = PaperOptionCard(key, title, subtitle, count, icon_path)
            card.clicked.connect(self._select_card)
            card.double_clicked.connect(self._emit_selected_key)
            self.list_layout.addWidget(card)
            self._cards[key] = card

        self.list_layout.addStretch()

        has_paper = bool(descriptors)
        self.scroll.setVisible(has_paper)
        self.empty_label.setVisible(not has_paper)
        self.btn_start.setEnabled(has_paper)

        if has_paper:
            self._select_card(descriptors[0][0])
        else:
            self._selected_key = None
            self.selection_text.setText("已选择：当前没有可用试卷")

    def _select_card(self, key: str) -> None:
        self._selected_key = key
        for card_key, card in self._cards.items():
            card.set_selected(card_key == key)

        if key == self.RANDOM_ALL_PAPERS_KEY:
            total_questions = sum(paper.question_count for paper in self.papers)
            random_count = min(100, total_questions)
            self.selection_text.setText(f"已选择： 所有试题随机抽取（{random_count}题）")
            return

        for paper in self.papers:
            if paper.filename == key:
                self.selection_text.setText(f"已选择： {paper.name}（{paper.question_count}题）")
                return

        self.selection_text.setText("已选择：")

    def _emit_selected_key(self, key: str) -> None:
        if key:
            self.start_paper_clicked.emit(key)

    def _emit_selected_paper(self) -> None:
        if self._selected_key:
            self.start_paper_clicked.emit(self._selected_key)

    def paintEvent(self, event) -> None:  # type: ignore[override]
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        if not self._background_pixmap.isNull():
            painter.drawPixmap(self.rect(), self._background_pixmap)
        else:
            painter.fillRect(self.rect(), Qt.GlobalColor.white)
        painter.end()
