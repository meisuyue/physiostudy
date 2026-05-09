from __future__ import annotations

from PyQt6.QtCore import QDateTime, QTimer, Qt, pyqtSignal
from PyQt6.QtGui import QPainter, QPixmap
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from ..project_paths import DATA_DIR


HOME_BG_PATH = DATA_DIR / "icons" / "default" / "home_page_bg.png"
LOGO_PATH = DATA_DIR / "icons" / "default" / "logo.png"
TITLE_PATH = DATA_DIR / "icons" / "default" / "title.png"


class WelcomePage(QWidget):
    home_clicked = pyqtSignal()
    start_learning_clicked = pyqtSignal()
    settings_clicked = pyqtSignal()
    help_clicked = pyqtSignal()
    contact_clicked = pyqtSignal()
    exit_clicked = pyqtSignal()

    def __init__(self, username: str, quote_text: str) -> None:
        super().__init__()
        self.username = username
        self.quote_text = quote_text
        self._background_pixmap = QPixmap(str(HOME_BG_PATH)) if HOME_BG_PATH.exists() else QPixmap()
        self._logo_pixmap = QPixmap(str(LOGO_PATH)) if LOGO_PATH.exists() else QPixmap()
        self._title_pixmap = QPixmap(str(TITLE_PATH)) if TITLE_PATH.exists() else QPixmap()
        self._clock_timer = QTimer(self)
        self._clock_timer.timeout.connect(self._update_clock)
        self._build_ui()
        self._apply_responsive_layout()
        self._update_clock()
        self._clock_timer.start(1000)
        QTimer.singleShot(0, self._apply_responsive_layout)

    def _build_ui(self) -> None:
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        self.setStyleSheet(
            """
            QLabel {
                background: transparent;
            }
            QFrame#TopBar {
                background: rgba(255, 255, 255, 0.58);
                border: 1px solid rgba(255, 255, 255, 0.96);
                border-radius: 26px;
            }
            QPushButton#NavButton {
                border: none;
                background: transparent;
                color: #2e3445;
                font-size: 16px;
                font-weight: 700;
                padding: 12px 24px;
                border-radius: 16px;
            }
            QPushButton#NavButton:hover {
                color: #394fc7;
                background: rgba(255, 255, 255, 0.42);
            }
            QPushButton#NavButton[active='true'] {
                color: #263ea7;
                background: rgba(213, 221, 255, 0.94);
                border: 1px solid rgba(179, 194, 255, 0.98);
            }
            QFrame#HeroPanel {
                background: transparent;
                border: none;
            }
            QFrame#DividerLine {
                background: rgba(204, 168, 255, 0.95);
                min-height: 3px;
                max-height: 3px;
                border-radius: 2px;
            }
            QLabel#DividerDot {
                color: #d2a1ff;
                font-size: 18px;
                font-weight: 800;
            }
            QFrame#QuoteCard {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                            stop:0 rgba(255, 120, 140, 0.88),
                                            stop:1 rgba(89, 140, 255, 0.88));
                border: 1px solid rgba(255, 255, 255, 0.85);
                border-radius: 24px;
            }
            QLabel#QuoteText {
                color: white;
                font-size: 16px;
                font-weight: 700;
                line-height: 1.7;
            }
            QPushButton#PrimaryButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                            stop:0 #5a94ff, stop:1 #ad6cff);
                color: white;
                border: 2px solid #E8B0F6;
                border-radius: 22px;
                padding: 18px 34px;
                font-size: 18px;
                font-weight: 800;
                min-width: 280px;
            }
            QPushButton#PrimaryButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                            stop:0 #4e88f3, stop:1 #9b5ff2);
            }
            QPushButton#SecondaryButton {
                background: rgba(255, 255, 255, 0.92);
                color: #3650b7;
                border: 2px solid rgba(197, 201, 255, 0.98);
                border-radius: 22px;
                padding: 18px 34px;
                font-size: 18px;
                font-weight: 800;
                min-width: 280px;
            }
            QPushButton#SecondaryButton:hover {
                background: rgba(255, 255, 255, 1.0);
                border-color: rgba(162, 171, 250, 1.0);
            }
            QFrame#ClockPanel {
                color: white;
                border: 0px solid rgba(255, 255, 255, 0.9);
                border-radius: 24px;
            }
            QLabel#ClockDate {
                color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                            stop:0 rgba(108, 154, 255, 0.95),
                                            stop:1 rgba(180, 115, 255, 0.95));
                font-size: 16px;
                font-weight: 700;
            }
            QLabel#ClockTime {
                color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                            stop:0 rgba(108, 154, 255, 0.95),
                                            stop:1 rgba(180, 115, 255, 0.95));
                font-size: 34px;
                font-weight: 900;
            }
            """
        )

        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(0)

        root.addWidget(self._build_top_bar())
        root.addStretch()
        root.addWidget(self._build_hero_panel(), alignment=Qt.AlignmentFlag.AlignCenter)
        root.addStretch()

    def _build_top_bar(self) -> QFrame:
        bar = QFrame()
        bar.setObjectName("TopBar")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(14)

        self.icon_label = QLabel()
        if not self._logo_pixmap.isNull():
            self.icon_label.setPixmap(
                self._logo_pixmap.scaled(
                    32,
                    32,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
        layout.addWidget(self.icon_label)

        self.top_title_label = QLabel()
        self.top_title_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.top_title_label)

        layout.addSpacing(18)

        btn_home = QPushButton("首页")
        btn_home.setObjectName("NavButton")
        btn_home.setProperty("active", True)
        btn_home.clicked.connect(self.home_clicked.emit)

        btn_settings = QPushButton("设置")
        btn_settings.setObjectName("NavButton")
        btn_settings.clicked.connect(self.settings_clicked.emit)

        btn_help = QPushButton("帮助")
        btn_help.setObjectName("NavButton")
        btn_help.clicked.connect(self.help_clicked.emit)

        btn_contact = QPushButton("联系作者")
        btn_contact.setObjectName("NavButton")
        btn_contact.clicked.connect(self.contact_clicked.emit)

        layout.addWidget(btn_home)
        layout.addWidget(btn_settings)
        layout.addWidget(btn_help)
        layout.addWidget(btn_contact)
        layout.addStretch()
        layout.addWidget(self._build_clock_panel(), alignment=Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)
        return bar

    def _build_clock_panel(self) -> QFrame:
        self.clock_panel = QFrame()
        self.clock_panel.setObjectName("ClockPanel")

        layout = QVBoxLayout(self.clock_panel)
        layout.setContentsMargins(18, 12, 18, 12)
        layout.setSpacing(0)

        self.clock_date_label = QLabel("")
        self.clock_date_label.setObjectName("ClockDate")
        self.clock_date_label.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.clock_time_label = QLabel("")
        self.clock_time_label.setObjectName("ClockTime")
        self.clock_time_label.setAlignment(Qt.AlignmentFlag.AlignRight)

        layout.addWidget(self.clock_date_label)
        layout.addWidget(self.clock_time_label)
        return self.clock_panel

    def _build_hero_panel(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("HeroPanel")
        self.hero_layout = QVBoxLayout(panel)
        self.hero_layout.setContentsMargins(80, 96, 80, 96)
        self.hero_layout.setSpacing(22)

        self.hero_title_label = QLabel()
        self.hero_title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        divider = QHBoxLayout()
        divider.addStretch()
        self.hero_left_line = QFrame()
        self.hero_left_line.setObjectName("DividerLine")
        dot = QLabel("•")
        dot.setObjectName("DividerDot")
        self.hero_right_line = QFrame()
        self.hero_right_line.setObjectName("DividerLine")
        divider.addWidget(self.hero_left_line)
        divider.addSpacing(12)
        divider.addWidget(dot)
        divider.addSpacing(12)
        divider.addWidget(self.hero_right_line)
        divider.addStretch()

        self.quote_card = QFrame()
        self.quote_card.setObjectName("QuoteCard")
        quote_layout = QVBoxLayout(self.quote_card)
        quote_layout.setContentsMargins(22, 20, 22, 20)
        quote_layout.setSpacing(0)
        self.quote_label = QLabel(self.quote_text)
        self.quote_label.setObjectName("QuoteText")
        self.quote_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.quote_label.setWordWrap(True)
        quote_layout.addWidget(self.quote_label)

        self.btn_start = QPushButton("开始学习")
        self.btn_start.setObjectName("PrimaryButton")
        self.btn_start.clicked.connect(self.start_learning_clicked.emit)

        self.btn_exit = QPushButton("退出软件")
        self.btn_exit.setObjectName("SecondaryButton")
        self.btn_exit.clicked.connect(self.exit_clicked.emit)

        self.hero_layout.addWidget(self.hero_title_label)
        self.hero_layout.addLayout(divider)
        self.hero_layout.addWidget(self.quote_card)
        self.hero_layout.addSpacing(18)
        self.hero_layout.addWidget(self.btn_start, alignment=Qt.AlignmentFlag.AlignHCenter)
        self.hero_layout.addWidget(self.btn_exit, alignment=Qt.AlignmentFlag.AlignHCenter)
        return panel

    def _refresh_title_pixmaps(self) -> None:
        if not self._title_pixmap.isNull():
            top_pix = self._title_pixmap.scaledToHeight(34, Qt.TransformationMode.SmoothTransformation)
            hero_height = max(64, min(160, self.height() // 6 if self.height() > 0 else 120))
            hero_pix = self._title_pixmap.scaledToHeight(hero_height, Qt.TransformationMode.SmoothTransformation)
            self.top_title_label.setPixmap(top_pix)
            self.hero_title_label.setPixmap(hero_pix)
        else:
            self.top_title_label.setText("PhysioStudy")
            self.hero_title_label.setText("PhysioStudy")

    def _apply_responsive_layout(self) -> None:
        page_width = max(self.width(), 900)
        page_height = max(self.height(), 680)

        hero_side_margin = max(28, min(80, page_width // 18))
        hero_vertical_margin = max(26, min(96, page_height // 10))
        divider_width = max(90, min(180, page_width // 8))
        button_width = max(220, min(280, page_width // 5))
        top_title_width = max(140, min(210, page_width // 7))
        clock_width = max(220, min(280, page_width // 5))

        self.top_title_label.setMinimumWidth(top_title_width)
        self.clock_panel.setMinimumWidth(clock_width)
        self.hero_layout.setContentsMargins(
            hero_side_margin,
            hero_vertical_margin,
            hero_side_margin,
            hero_vertical_margin,
        )
        self.hero_left_line.setFixedWidth(divider_width)
        self.hero_right_line.setFixedWidth(divider_width)
        self.btn_start.setMinimumWidth(button_width)
        self.btn_exit.setMinimumWidth(button_width)
        self.quote_card.setMaximumWidth(max(620, min(820, page_width - hero_side_margin * 2)))
        self._refresh_title_pixmaps()

    def _update_clock(self) -> None:
        now = QDateTime.currentDateTime()
        weekday_map = {
            1: "星期一",
            2: "星期二",
            3: "星期三",
            4: "星期四",
            5: "星期五",
            6: "星期六",
            7: "星期日",
        }
        weekday = weekday_map.get(now.date().dayOfWeek(), "")
        self.clock_date_label.setText(now.toString(f"yyyy年MM月dd日 {weekday}"))
        self.clock_time_label.setText(now.toString("HH:mm"))

    def resizeEvent(self, event) -> None:  # type: ignore[override]
        super().resizeEvent(event)
        self._apply_responsive_layout()

    def paintEvent(self, event) -> None:  # type: ignore[override]
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        if not self._background_pixmap.isNull():
            painter.drawPixmap(self.rect(), self._background_pixmap)
        else:
            painter.fillRect(self.rect(), Qt.GlobalColor.white)
        painter.end()
