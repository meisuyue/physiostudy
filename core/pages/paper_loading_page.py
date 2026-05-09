from __future__ import annotations

import random

from PyQt6.QtCore import QElapsedTimer, QRect, QRectF, QSize, QTimer, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QLinearGradient, QMovie, QPainter, QPainterPath, QPixmap
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QSizePolicy, QVBoxLayout, QWidget

from ..project_paths import DATA_DIR


MOVE_GIF_PATH = DATA_DIR / "icons" / "default" / "move.gif"
LOADING_BG_PATH = DATA_DIR / "icons" / "default" / "loading_page.png"
LOGO_PATH = DATA_DIR / "icons" / "default" / "logo.png"


class ProgressTrackWidget(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._progress = 0.0
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)

    def set_progress(self, progress: float) -> None:
        self._progress = max(0.0, min(1.0, progress))
        self.update()

    def paintEvent(self, event) -> None:  # type: ignore[override]
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = QRectF(self.rect().adjusted(0, 0, -1, -1))
        radius = rect.height() / 2

        shell_path = QPainterPath()
        shell_path.addRoundedRect(rect, radius, radius)
        painter.fillPath(shell_path, QColor(255, 255, 255, 214))
        painter.setPen(QColor(225, 224, 255, 245))
        painter.drawPath(shell_path)

        fill_margin = 6
        fill_rect = QRectF(rect.adjusted(fill_margin, fill_margin, -fill_margin, -fill_margin))
        fill_width = int(fill_rect.width() * self._progress)
        if fill_width > 0:
            fill_rect.setWidth(max(fill_width, fill_rect.height()))
            fill_path = QPainterPath()
            fill_radius = fill_rect.height() / 2
            fill_path.addRoundedRect(fill_rect, fill_radius, fill_radius)
            gradient = QLinearGradient(fill_rect.topLeft(), fill_rect.topRight())
            gradient.setColorAt(0.0, QColor(108, 161, 255, 245))
            gradient.setColorAt(1.0, QColor(189, 120, 255, 245))
            painter.fillPath(fill_path, gradient)

        painter.end()


class PaperLoadingPage(QWidget):
    back_home_clicked = pyqtSignal()
    buffer_finished = pyqtSignal()

    def __init__(self, paper_name: str) -> None:
        super().__init__()
        self.paper_name = paper_name
        self.buffer_duration_ms = random.randint(5000, 10000)
        self._background_pixmap = QPixmap(str(LOADING_BG_PATH)) if LOADING_BG_PATH.exists() else QPixmap()
        self._logo_pixmap = QPixmap(str(LOGO_PATH)) if LOGO_PATH.exists() else QPixmap()
        self._buffer_started = False
        self._move_movie: QMovie | None = None
        self._elapsed_timer = QElapsedTimer()
        self._animation_timer = QTimer(self)
        self._animation_timer.setInterval(16)
        self._animation_timer.timeout.connect(self._advance_animation)
        self._buffer_timer = QTimer(self)
        self._buffer_timer.setSingleShot(True)
        self._buffer_timer.timeout.connect(self.buffer_finished.emit)
        self._min_gif_size = QSize(92, 92)
        self._max_gif_size = QSize(190, 190)
        self._build_ui()

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
                border-radius: 24px;
            }
            QLabel#AppTitle {
                color: #2b428d;
                font-size: 20px;
                font-weight: 800;
            }
            QPushButton#BackButton {
                background: rgba(255, 255, 255, 0.88);
                color: #4b70d8;
                border: 1px solid rgba(255, 255, 255, 0.96);
                border-radius: 22px;
                padding: 14px 26px;
                font-size: 16px;
                font-weight: 700;
            }
            QPushButton#BackButton:hover {
                background: rgba(255, 255, 255, 0.96);
            }
            QLabel#Title {
                color: #3352c7;
                font-size: 34px;
                font-weight: 900;
            }
            QLabel#PaperName {
                color: rgba(75, 100, 180, 0.96);
                font-size: 16px;
                font-weight: 700;
            }
            QLabel#DividerDot {
                color: rgba(196, 158, 255, 0.96);
                font-size: 20px;
                font-weight: 800;
            }
            QFrame#DividerLine {
                background: rgba(215, 187, 255, 0.82);
                min-height: 2px;
                max-height: 2px;
                border-radius: 2px;
            }
            QFrame#Stage {
                background: rgba(255, 255, 255, 0.56);
                border: 1px solid rgba(255, 255, 255, 0.9);
                border-radius: 34px;
            }
            QFrame#InnerStage {
                background: rgba(255, 255, 255, 0.62);
                border: 1px solid rgba(255, 255, 255, 0.92);
                border-radius: 30px;
            }
            QWidget#TrackArea {
                background: transparent;
            }
            QLabel#ArrowHint {
                color: rgba(138, 166, 241, 0.95);
                font-size: 28px;
                font-weight: 700;
            }
            QLabel#StatusText {
                color: rgba(88, 106, 179, 0.96);
                font-size: 16px;
                font-weight: 700;
            }
            QLabel#PercentChip {
                background: rgba(255, 255, 255, 0.82);
                color: #7a69f0;
                border: 1px solid rgba(192, 201, 255, 0.98);
                border-radius: 24px;
                padding: 10px 28px;
                font-size: 18px;
                font-weight: 800;
            }
            """
        )

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 18, 24, 22)
        root.setSpacing(22)

        root.addWidget(self._build_top_bar())

        content = QVBoxLayout()
        content.setSpacing(18)

        self.btn_back_home = QPushButton("← 返回首页")
        self.btn_back_home.setObjectName("BackButton")
        self.btn_back_home.clicked.connect(self.back_home_clicked.emit)
        content.addWidget(self.btn_back_home, alignment=Qt.AlignmentFlag.AlignLeft)
        content.addSpacing(8)
        content.addStretch()

        self.title_label = QLabel("正在进入试题测试")
        self.title_label.setObjectName("Title")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setFont(QFont("Microsoft YaHei UI", 30, QFont.Weight.Black))

        divider = QHBoxLayout()
        divider.setSpacing(12)
        divider.addStretch()
        left_line = QFrame()
        left_line.setObjectName("DividerLine")
        left_line.setFixedWidth(92)
        dot_left = QLabel("✦")
        dot_left.setObjectName("DividerDot")
        self.paper_label = QLabel(self.paper_name)
        self.paper_label.setObjectName("PaperName")
        self.paper_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        dot_right = QLabel("✦")
        dot_right.setObjectName("DividerDot")
        right_line = QFrame()
        right_line.setObjectName("DividerLine")
        right_line.setFixedWidth(92)
        divider.addWidget(left_line)
        divider.addWidget(dot_left)
        divider.addWidget(self.paper_label)
        divider.addWidget(dot_right)
        divider.addWidget(right_line)
        divider.addStretch()

        self.stage_frame = QFrame()
        self.stage_frame.setObjectName("Stage")
        self.stage_frame.setMinimumWidth(1080)
        self.stage_frame.setMaximumWidth(1180)
        self.stage_frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        stage_outer = QVBoxLayout(self.stage_frame)
        stage_outer.setContentsMargins(14, 14, 14, 14)

        self.inner_stage = QFrame()
        self.inner_stage.setObjectName("InnerStage")
        self.inner_stage.setMinimumHeight(360)
        inner_layout = QVBoxLayout(self.inner_stage)
        inner_layout.setContentsMargins(34, 30, 34, 28)
        inner_layout.setSpacing(16)

        self.track_area = QWidget()
        self.track_area.setObjectName("TrackArea")
        self.track_area.setMinimumHeight(180)
        self.track_area.setMinimumWidth(980)
        self.track_area.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        self.progress_track = ProgressTrackWidget(self.track_area)
        self.progress_track.setMinimumHeight(46)

        self.arrow_hint = QLabel("Loading......")
        self.arrow_hint.setObjectName("ArrowHint")
        self.arrow_hint.setParent(self.track_area)

        self.move_label = QLabel(self.track_area)
        self.move_label.setStyleSheet("background: transparent;")
        self.move_label.hide()

        if MOVE_GIF_PATH.exists():
            self._move_movie = QMovie(str(MOVE_GIF_PATH))
            self._move_movie.setScaledSize(self._min_gif_size)
            self.move_label.setMovie(self._move_movie)
            self.move_label.resize(self._min_gif_size)
        else:
            self.move_label.setText("Loading")
            self.move_label.setStyleSheet(
                "background: rgba(255,255,255,0.88); color:#4b70d8; border-radius:20px; padding:18px 20px;"
            )
            self.move_label.adjustSize()

        self.status_label = QLabel("·· 正在载入题库与测试环境 ··")
        self.status_label.setObjectName("StatusText")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.percent_label = QLabel("加载中 0%")
        self.percent_label.setObjectName("PercentChip")
        self.percent_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        inner_layout.addWidget(self.track_area)
        inner_layout.addWidget(self.status_label, alignment=Qt.AlignmentFlag.AlignHCenter)
        inner_layout.addWidget(self.percent_label, alignment=Qt.AlignmentFlag.AlignHCenter)
        stage_outer.addWidget(self.inner_stage)

        content.addWidget(self.title_label)
        content.addLayout(divider)
        content.addSpacing(18)
        content.addWidget(self.stage_frame, alignment=Qt.AlignmentFlag.AlignHCenter)
        content.addStretch()
        root.addLayout(content, stretch=1)

    def _build_top_bar(self) -> QFrame:
        bar = QFrame()
        bar.setObjectName("TopBar")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(18, 14, 18, 14)
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

    def showEvent(self, event) -> None:  # type: ignore[override]
        super().showEvent(event)
        self._layout_track_elements()
        if not self._buffer_started:
            QTimer.singleShot(0, self._start_buffering)

    def resizeEvent(self, event) -> None:  # type: ignore[override]
        super().resizeEvent(event)
        self._layout_track_elements()
        if self._buffer_started:
            self._advance_animation()

    def _start_buffering(self) -> None:
        if self._buffer_started:
            return
        self._buffer_started = True
        self._buffer_timer.start(self.buffer_duration_ms)
        self._elapsed_timer.start()
        self._animation_timer.start()
        self._advance_animation()
        if self._move_movie is not None:
            self._move_movie.start()

    def _layout_track_elements(self) -> None:
        area_w = max(self.track_area.width(), 700)
        area_h = max(self.track_area.height(), 170)

        shell_w = max(760, int(area_w * 0.86))
        shell_h = 46
        shell_x = (area_w - shell_w) // 2
        shell_y = max(82, area_h - 88)
        self.progress_track.setGeometry(shell_x, shell_y, shell_w, shell_h)

        self.arrow_hint.adjustSize()
        arrow_x = shell_x + shell_w - self.arrow_hint.width() - 2
        arrow_y = max(8, shell_y - self.arrow_hint.height() - 12)
        self.arrow_hint.move(arrow_x, arrow_y)

    def _advance_animation(self) -> None:
        if not self._buffer_started:
            return

        duration = max(1, self.buffer_duration_ms)
        elapsed = min(self._elapsed_timer.elapsed(), duration)
        ratio = elapsed / duration
        percent = min(100, max(0, int(ratio * 100)))
        self.percent_label.setText(f"加载中 {percent}%")

        self.progress_track.set_progress(ratio)

        shell_rect = self.progress_track.geometry()

        area_w = max(self.track_area.width(), 700)
        area_h = max(self.track_area.height(), 170)

        if ratio <= 0.5:
            scale_ratio = ratio / 0.5
        else:
            scale_ratio = 1.0

        width = int(self._min_gif_size.width() + (self._max_gif_size.width() - self._min_gif_size.width()) * scale_ratio)
        height = int(self._min_gif_size.height() + (self._max_gif_size.height() - self._min_gif_size.height()) * scale_ratio)
        target_size = QSize(width, height)

        if self._move_movie is not None:
            self._move_movie.setScaledSize(target_size)
        self.move_label.resize(target_size)

        start_center_x = area_w + width // 2
        end_center_x = -width // 2
        current_center_x = int(start_center_x + (end_center_x - start_center_x) * ratio)
        current_x = current_center_x - width // 2
        current_y = max(0, shell_rect.y() - height // 2 + 8)

        self.move_label.setGeometry(QRect(current_x, current_y, width, height))
        self.move_label.show()

        if elapsed >= duration:
            self._animation_timer.stop()

    def cleanup(self) -> None:
        self._buffer_timer.stop()
        self._animation_timer.stop()
        if self._move_movie is not None:
            self._move_movie.stop()

    def paintEvent(self, event) -> None:  # type: ignore[override]
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        if not self._background_pixmap.isNull():
            painter.drawPixmap(self.rect(), self._background_pixmap)
        else:
            painter.fillRect(self.rect(), Qt.GlobalColor.white)
        painter.end()
