from __future__ import annotations

import random
from pathlib import Path
from typing import Callable

from PyQt6.QtCore import QDate, QDateTime, QTimer, Qt, pyqtSignal
from PyQt6.QtGui import QFont, QPainter, QPixmap
from PyQt6.QtWidgets import (
    QCalendarWidget,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QProgressBar,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from ..project_paths import DATA_DIR


HUB_BG_PATH = DATA_DIR / 'icons' / 'default' / 'study_hub.png'
ITEM_ICONS_DIR = DATA_DIR / 'icons' / 'items'


class SidebarButton(QPushButton):
    def __init__(self, text: str, active: bool = False, parent: QWidget | None = None) -> None:
        super().__init__(text, parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setProperty('active', active)
        self.setObjectName('SidebarButton')


class FeatureCard(QFrame):
    clicked = pyqtSignal()

    def __init__(
        self,
        icon_path: Path | None,
        title: str,
        description: str,
        accent: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.icon_path = icon_path
        self.title = title
        self.description = description
        self.accent = accent
        self._build_ui()

    def _build_ui(self) -> None:
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setObjectName('FeatureCard')
        self.setMinimumHeight(210)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setStyleSheet(
            f"""
            QFrame#FeatureCard {{
                background: rgba(255, 255, 255, 0.50);
                border: 1px solid rgba(255, 255, 255, 0.90);
                border-radius: 28px;
            }}
            QFrame#FeatureCard:hover {{
                background: rgba(255, 255, 255, 0.66);
                border: 1px solid rgba(215, 227, 255, 0.95);
            }}
            QLabel#FeatureTitle {{
                color: {self.accent};
                font-size: 20px;
                font-weight: 900;
            }}
            QLabel#FeatureBody {{
                color: #5d6686;
                font-size: 13px;
                line-height: 1.75;
            }}
            QPushButton#ArrowButton {{
                background: rgba(255, 255, 255, 0.88);
                border: none;
                color: {self.accent};
                min-width: 42px;
                max-width: 42px;
                min-height: 42px;
                max-height: 42px;
                border-radius: 21px;
                font-size: 24px;
                font-weight: 900;
            }}
            """
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 22)
        layout.setSpacing(16)

        top_row = QHBoxLayout()
        top_row.setSpacing(16)

        icon_box = QFrame()
        icon_box.setStyleSheet(
            'background: rgba(255,255,255,0.45); border: 1px solid rgba(255,255,255,0.78); border-radius: 26px;'
        )
        icon_box.setFixedSize(82, 82)
        icon_layout = QVBoxLayout(icon_box)
        icon_layout.setContentsMargins(12, 12, 12, 12)

        icon_label = QLabel()
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if self.icon_path and self.icon_path.exists():
            icon_label.setPixmap(QPixmap(str(self.icon_path)).scaled(56, 56, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        else:
            icon_label.setText('•')
            icon_label.setStyleSheet(f'color:{self.accent}; font-size:36px; font-weight:900;')
        icon_layout.addWidget(icon_label)

        text_col = QVBoxLayout()
        text_col.setSpacing(10)
        text_col.addStretch()
        title = QLabel(self.title)
        title.setObjectName('FeatureTitle')
        body = QLabel(self.description)
        body.setObjectName('FeatureBody')
        body.setWordWrap(True)
        text_col.addWidget(title)
        text_col.addWidget(body)
        text_col.addStretch()

        top_row.addWidget(icon_box)
        top_row.addLayout(text_col, stretch=1)
        layout.addLayout(top_row)
        layout.addStretch()

        bottom_row = QHBoxLayout()
        bottom_row.addStretch()
        arrow = QPushButton('›')
        arrow.setObjectName('ArrowButton')
        arrow.clicked.connect(self.clicked.emit)
        bottom_row.addWidget(arrow)
        layout.addLayout(bottom_row)

    def mousePressEvent(self, event) -> None:  # type: ignore[override]
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class StatTile(QFrame):
    def __init__(self, value_text: str, caption: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.value_label = QLabel(value_text)
        self.caption_label = QLabel(caption)
        self._build_ui()

    def _build_ui(self) -> None:
        self.setStyleSheet(
            """
            QFrame {
                background: rgba(255,255,255,0.38);
                border: 1px solid rgba(255,255,255,0.82);
                border-radius: 18px;
            }
            QLabel {
                background: transparent;
            }
            """
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(6)
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.value_label.setStyleSheet('color:#2f4ab5; font-size:16px; font-weight:900;')
        self.caption_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.caption_label.setStyleSheet('color:#7d86a9; font-size:12px; font-weight:600;')
        layout.addWidget(self.value_label)
        layout.addWidget(self.caption_label)


class LearnHubPage(QWidget):
    home_clicked = pyqtSignal()
    settings_clicked = pyqtSignal()
    help_clicked = pyqtSignal()
    contact_clicked = pyqtSignal()
    word_study_clicked = pyqtSignal()
    roots_affixes_clicked = pyqtSignal()
    review_marked_clicked = pyqtSignal()
    search_clicked = pyqtSignal()
    paper_test_clicked = pyqtSignal()

    def __init__(
        self,
        username: str,
        usage_seconds_provider: Callable[[], int],
        progress_items: list[dict[str, object]],
    ) -> None:
        super().__init__()
        self.username = username
        self.usage_seconds_provider = usage_seconds_provider
        self.progress_items = progress_items
        self._background_pixmap = QPixmap(str(HUB_BG_PATH)) if HUB_BG_PATH.exists() else QPixmap()
        self._clock_timer = QTimer(self)
        self._clock_timer.timeout.connect(self._tick)
        self._icon_paths = self._pick_item_icons(8)
        self._build_ui()
        self._tick()
        self._clock_timer.start(1000)

    def _pick_item_icons(self, count: int) -> list[Path]:
        icons = [path for path in sorted(ITEM_ICONS_DIR.glob('*')) if path.suffix.lower() in {'.png', '.jpg', '.jpeg', '.webp', '.bmp'}]
        if not icons:
            return []
        shuffled = icons[:]
        random.shuffle(shuffled)
        if len(shuffled) >= count:
            return shuffled[:count]
        result: list[Path] = []
        while len(result) < count:
            batch = icons[:]
            random.shuffle(batch)
            result.extend(batch)
        return result[:count]

    def _build_ui(self) -> None:
        self.setStyleSheet(
            """
            QLabel {
                background: transparent;
            }
            QFrame#Sidebar {
                background: rgba(255,255,255,0.38);
                border: 1px solid rgba(255,255,255,0.84);
                border-radius: 28px;
            }
            QPushButton#SidebarButton {
                text-align: left;
                padding: 16px 24px;
                border: none;
                border-radius: 18px;
                background: transparent;
                color: #405291;
                font-size: 16px;
                font-weight: 700;
            }
            QPushButton#SidebarButton:hover {
                background: rgba(255,255,255,0.45);
                color: #3049b7;
            }
            QPushButton#SidebarButton[active='true'] {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(85,142,255,0.98),
                    stop:1 rgba(190,105,255,0.98));
                color: white;
            }
            QFrame#MainPanel {
                background: rgba(255,255,255,0.28);
                border: 1px solid rgba(255,255,255,0.86);
                border-radius: 34px;
            }
            QLabel#GreetingTitle {
                color: #2f48b4;
                font-size: 44px;
                font-weight: 900;
            }
            QLabel#GreetingSub {
                color: #6170a7;
                font-size: 18px;
                font-weight: 600;
            }
            QFrame#HeroChip {
                background: rgba(255,255,255,0.56);
                border: 1px solid rgba(255,255,255,0.88);
                border-radius: 16px;
            }
            QLabel#HeroChipLabel {
                color: #4658a7;
                font-size: 14px;
                font-weight: 700;
            }
            QFrame#SectionCard {
                background: rgba(255,255,255,0.42);
                border: 1px solid rgba(255,255,255,0.88);
                border-radius: 28px;
            }
            QLabel#SectionTitle {
                color: #3048b0;
                font-size: 18px;
                font-weight: 900;
            }
            QLabel#SectionSub {
                color: #7d86a8;
                font-size: 12px;
                font-weight: 600;
            }
            QProgressBar {
                min-height: 10px;
                max-height: 10px;
                border: none;
                border-radius: 5px;
                background: rgba(222, 228, 255, 0.9);
                text-align: center;
            }
            QProgressBar::chunk {
                border-radius: 5px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(97,145,255,0.98),
                    stop:1 rgba(180,104,255,0.98));
            }
            QCalendarWidget QWidget {
                alternate-background-color: transparent;
            }
            QCalendarWidget QToolButton {
                color: #4354a0;
                font-size: 14px;
                font-weight: 800;
                background: transparent;
                border: none;
            }
            QCalendarWidget QAbstractItemView:enabled {
                color: #56668e;
                selection-background-color: rgba(100, 135, 255, 0.95);
                selection-color: white;
                background: transparent;
                border: none;
                outline: 0;
                font-size: 13px;
                gridline-color: rgba(0,0,0,0);
            }
            """
        )

        root = QHBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(20)

        root.addWidget(self._build_sidebar())
        root.addWidget(self._build_main_panel(), stretch=1)

    def _build_sidebar(self) -> QFrame:
        sidebar = QFrame()
        sidebar.setObjectName('Sidebar')
        sidebar.setFixedWidth(215)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(18, 20, 18, 20)
        layout.setSpacing(10)

        nav_items = [
            ('首页', self.home_clicked.emit, True),
            ('学习', self.word_study_clicked.emit, False),
            ('练习', self.paper_test_clicked.emit, False),
            ('复习', self.review_marked_clicked.emit, False),
            ('词根词缀', self.roots_affixes_clicked.emit, False),
            ('查询', self.search_clicked.emit, False),
            ('设置', self.settings_clicked.emit, False),
            ('帮助', self.help_clicked.emit, False),
            ('关于', self.contact_clicked.emit, False),
        ]
        for text, slot, active in nav_items:
            btn = SidebarButton(text, active=active)
            btn.clicked.connect(slot)
            layout.addWidget(btn)

        layout.addStretch()
        layout.addWidget(self._build_today_time_card())
        return sidebar

    def _build_today_time_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName('SectionCard')
        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(10)

        title = QLabel('今日已学习时长')
        title.setObjectName('SectionTitle')

        self.today_time_label = QLabel('0 分钟')
        self.today_time_label.setStyleSheet('color:#2f48b4; font-size:22px; font-weight:900;')

        tip = QLabel('好好学习！')
        tip.setObjectName('SectionSub')

        progress_row = QHBoxLayout()
        self.today_time_bar = QProgressBar()
        self.today_time_bar.setRange(0, 100)
        self.today_time_bar.setTextVisible(False)
        self.today_time_percent = QLabel('0%')
        self.today_time_percent.setStyleSheet('color:#5d71bd; font-size:13px; font-weight:800;')
        progress_row.addWidget(self.today_time_bar, stretch=1)
        progress_row.addWidget(self.today_time_percent)

        layout.addWidget(title)
        layout.addWidget(self.today_time_label)
        layout.addWidget(tip)
        layout.addSpacing(4)
        layout.addLayout(progress_row)
        return card

    def _build_main_panel(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName('MainPanel')
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(26, 24, 26, 22)
        layout.setSpacing(22)

        layout.addLayout(self._build_top_bar())
        layout.addLayout(self._build_feature_row())
        layout.addLayout(self._build_bottom_row())
        return panel

    def _build_top_bar(self) -> QHBoxLayout:
        layout = QHBoxLayout()
        layout.setSpacing(24)

        left = QVBoxLayout()
        left.setSpacing(14)

        self.greeting_title = QLabel('下午好，继续加油！')
        self.greeting_title.setObjectName('GreetingTitle')
        self.greeting_title.setFont(QFont('Microsoft YaHei UI', 26, QFont.Weight.Black))

        subtitle = QLabel('科学学习，循序渐进，牢记于心')
        subtitle.setObjectName('GreetingSub')

        chip_row = QHBoxLayout()
        chip_row.setSpacing(12)
        self.date_chip = self._build_chip('')
        self.time_chip = self._build_chip('')
        chip_row.addWidget(self.date_chip)
        chip_row.addWidget(self.time_chip)
        chip_row.addStretch()

        left.addStretch()
        left.addWidget(self.greeting_title)
        left.addWidget(subtitle)
        left.addLayout(chip_row)
        left.addStretch()

        art = QFrame()
        art.setObjectName('SectionCard')
        art.setMinimumWidth(360)
        art_layout = QVBoxLayout(art)
        art_layout.setContentsMargins(20, 20, 20, 20)
        art_layout.setSpacing(10)
        art_icon = QLabel()
        art_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        art_icon_path = self._icon_paths[0] if self._icon_paths else None
        if art_icon_path and art_icon_path.exists():
            art_icon.setPixmap(QPixmap(str(art_icon_path)).scaled(180, 180, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        art_tip = QLabel('今天想先从哪一块开始？')
        art_tip.setAlignment(Qt.AlignmentFlag.AlignCenter)
        art_tip.setStyleSheet('color:#6070ab; font-size:15px; font-weight:700;')
        art_layout.addStretch()
        art_layout.addWidget(art_icon)
        art_layout.addWidget(art_tip)
        art_layout.addStretch()

        layout.addLayout(left, stretch=3)
        layout.addWidget(art, stretch=2)
        return layout

    def _build_chip(self, text: str) -> QFrame:
        chip = QFrame()
        chip.setObjectName('HeroChip')
        chip_layout = QHBoxLayout(chip)
        chip_layout.setContentsMargins(14, 10, 14, 10)
        chip_layout.setSpacing(0)
        label = QLabel(text)
        label.setObjectName('HeroChipLabel')
        chip_layout.addWidget(label)
        chip.label = label  # type: ignore[attr-defined]
        return chip

    def _build_feature_row(self) -> QHBoxLayout:
        layout = QHBoxLayout()
        layout.setSpacing(18)

        feature_specs = [
            ('单词学习', '学习与复习都从这里进入\n支持中文、英文双向切换', '#4b8dff', self.word_study_clicked.emit),
            ('词根词缀学习', '掌握高频词根词缀\n顺带把例词一并吃透', '#30c7a0', self.roots_affixes_clicked.emit),
            ('试题测试', '从题库里直接进入训练\n巩固知识与答题表达', '#8363f0', self.paper_test_clicked.emit),
            ('查询单词与释义', '遇到拿不准的词时\n这里随时查一下', '#f4a42a', self.search_clicked.emit),
        ]
        for index, (title, body, accent, slot) in enumerate(feature_specs, start=1):
            icon_path = self._icon_paths[index] if len(self._icon_paths) > index else None
            card = FeatureCard(icon_path, title, body, accent)
            card.clicked.connect(slot)
            layout.addWidget(card)
        return layout

    def _build_bottom_row(self) -> QHBoxLayout:
        layout = QHBoxLayout()
        layout.setSpacing(18)
        layout.addWidget(self._build_stats_card(), stretch=3)
        layout.addWidget(self._build_progress_card(), stretch=3)
        layout.addWidget(self._build_calendar_card(), stretch=2)
        return layout

    def _build_stats_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName('SectionCard')
        layout = QVBoxLayout(card)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(16)

        title = QLabel('学习统计')
        title.setObjectName('SectionTitle')
        subtitle = QLabel('把英文、中文和词根三条线的进度放在一起看。')
        subtitle.setObjectName('SectionSub')

        tiles_row = QHBoxLayout()
        tiles_row.setSpacing(12)
        self.stat_tiles: list[StatTile] = []
        for item in self.progress_items[:3]:
            completed = int(item.get('completed', 0))
            total = int(item.get('total', 0))
            label = str(item.get('label', ''))
            tile = StatTile(f'{completed}', f'{label} / {total}')
            self.stat_tiles.append(tile)
            tiles_row.addWidget(tile)

        summary = QLabel(self._build_summary_text())
        summary.setWordWrap(True)
        summary.setStyleSheet('color:#6572a4; font-size:13px; line-height:1.8;')

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addLayout(tiles_row)
        layout.addStretch()
        layout.addWidget(summary)
        return card

    def _build_progress_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName('SectionCard')
        layout = QVBoxLayout(card)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(14)

        title = QLabel('学习进度')
        title.setObjectName('SectionTitle')
        subtitle = QLabel('这里直接统计英文形式学习、中文形式学习和词根词缀学习。')
        subtitle.setObjectName('SectionSub')
        layout.addWidget(title)
        layout.addWidget(subtitle)

        self.progress_bars: list[QProgressBar] = []
        self.progress_labels: list[QLabel] = []
        for item in self.progress_items[:3]:
            row = QVBoxLayout()
            row.setSpacing(6)
            head = QHBoxLayout()
            label = QLabel(str(item.get('label', '')))
            label.setStyleSheet('color:#45539a; font-size:14px; font-weight:800;')
            percent_label = QLabel(f"{int(item.get('percent', 0))}%")
            percent_label.setStyleSheet('color:#6a78ac; font-size:13px; font-weight:800;')
            head.addWidget(label)
            head.addStretch()
            head.addWidget(percent_label)
            progress = QProgressBar()
            progress.setRange(0, 100)
            progress.setValue(int(item.get('percent', 0)))
            progress.setTextVisible(False)
            caption = QLabel(f"{int(item.get('completed', 0))} / {int(item.get('total', 0))} 已完成")
            caption.setStyleSheet('color:#7a84a8; font-size:12px; font-weight:600;')
            row.addLayout(head)
            row.addWidget(progress)
            row.addWidget(caption)
            layout.addLayout(row)
            self.progress_bars.append(progress)
            self.progress_labels.append(percent_label)
        layout.addStretch()
        return card

    def _build_calendar_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName('SectionCard')
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(12)

        title = QLabel('学习日历')
        title.setObjectName('SectionTitle')
        subtitle = QLabel('哈哈我也想知道我加这一块用来干嘛')
        subtitle.setObjectName('SectionSub')

        calendar = QCalendarWidget()
        calendar.setGridVisible(False)
        calendar.setVerticalHeaderFormat(QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader)
        calendar.setSelectedDate(QDate.currentDate())

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addWidget(calendar, stretch=1)
        return card

    def _build_summary_text(self) -> str:
        parts: list[str] = []
        for item in self.progress_items[:3]:
            label = str(item.get('label', ''))
            completed = int(item.get('completed', 0))
            total = int(item.get('total', 0))
            parts.append(f'{label} {completed}/{total}')
        return ' / '.join(parts) if parts else '暂时还没有可统计的学习数据。'

    def _tick(self) -> None:
        now = QDateTime.currentDateTime()
        hour = now.time().hour()
        if hour < 12:
            greeting = '上午好，继续加油！'
        elif hour < 18:
            greeting = '下午好，继续加油！'
        else:
            greeting = '晚上好，继续加油！'
        self.greeting_title.setText(greeting)

        weekday_map = {
            1: '星期一',
            2: '星期二',
            3: '星期三',
            4: '星期四',
            5: '星期五',
            6: '星期六',
            7: '星期日',
        }
        weekday = weekday_map.get(now.date().dayOfWeek(), '')
        self.date_chip.label.setText(now.toString(f'yyyy年MM月dd日 {weekday}'))  # type: ignore[attr-defined]
        self.time_chip.label.setText(now.toString('HH:mm'))  # type: ignore[attr-defined]
        self._update_today_usage()

    def _update_today_usage(self) -> None:
        seconds = max(0, int(self.usage_seconds_provider()))
        minutes = seconds // 60
        hours = minutes // 60
        remain_minutes = minutes % 60
        if hours > 0:
            text = f'{hours}小时 {remain_minutes}分钟'
        else:
            text = f'{minutes} 分钟'
        self.today_time_label.setText(text)
        percent = min(100, int((seconds / 1800) * 100))
        self.today_time_bar.setValue(percent)
        self.today_time_percent.setText(f'{percent}%')

    def paintEvent(self, event) -> None:  # type: ignore[override]
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        if not self._background_pixmap.isNull():
            painter.drawPixmap(self.rect(), self._background_pixmap)
        else:
            painter.fillRect(self.rect(), Qt.GlobalColor.white)
        painter.end()
