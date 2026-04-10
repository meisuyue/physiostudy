from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import List

from PyQt6.QtCore import QSize, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QImageReader, QMovie
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QMessageBox, QPushButton, QVBoxLayout, QWidget

from app_config import StudySettings
from storage import WordEntry


class StudyPage(QWidget):
    back_home_clicked = pyqtSignal()

    def __init__(
        self,
        words: List[WordEntry],
        lang: str,
        settings: StudySettings,
        mark_past: Callable[[str], None],
        mark_important: Callable[[str], bool],
    ) -> None:
        super().__init__()
        self.words = words
        self.lang = lang
        self.settings = settings
        self.mark_past = mark_past
        self.mark_important = mark_important
        self.index = 0
        self.wrong_count = 0

        self._movie: QMovie | None = None
        self._gif_source_size: QSize | None = None
        self._gif_dir = Path(__file__).resolve().parents[1] / "data" / "icons" / "TandF"
        self._answer_shown = False

        self._timer_show = QTimer(self)
        self._timer_show.setSingleShot(True)
        self._timer_show.timeout.connect(self._show_answer)
        self._timer_next = QTimer(self)
        self._timer_next.setSingleShot(True)
        self._timer_next.timeout.connect(self._auto_next)

        self._build_ui()
        if not self.words:
            QMessageBox.warning(self, "提示", "词库为空，无法开始学习。")
        self._render()

    def _build_ui(self) -> None:
        self.setStyleSheet(
            """
            QWidget { background: #f7f9fb; }
            #KeyLabel { color: #123047; }
            #Meaning { color: #214e75; }
            #Meta { color: #4b6478; }
            QPushButton {
                padding: 10px 18px;
                font-size: 16px;
                border-radius: 10px;
                background: #dcecf7;
                border: 1px solid #c2d7e6;
                color: #123047;
            }
            QPushButton:hover { background: #cfe3f3; }
            QPushButton:disabled {
                background: #eef3f7;
                color: #9aa8b6;
            }
            """
        )

        top_row = QHBoxLayout()
        self.btn_back_home = QPushButton("返回首页")
        self.btn_back_home.clicked.connect(self._on_back_home)
        self.btn_save_word = QPushButton("保存该单词")
        self.btn_save_word.clicked.connect(self._save_current_word)
        top_row.addWidget(self.btn_back_home)
        top_row.addStretch()
        top_row.addWidget(self.btn_save_word)

        self.mode_hint = QLabel("")
        self.mode_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.mode_hint.setFont(QFont("Arial", 12))
        self.mode_hint.setStyleSheet("color:#66798b;")

        self.key_label = QLabel("--")
        self.key_label.setObjectName("KeyLabel")
        self.key_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.key_label.setFont(QFont("Arial", 32, QFont.Weight.Bold))

        self.meaning_label = QLabel("")
        self.meaning_label.setObjectName("Meaning")
        self.meaning_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.meaning_label.setFont(QFont("Arial", 18))

        meta_row = QHBoxLayout()
        self.abbrev_label = QLabel("")
        self.abbrev_label.setObjectName("Meta")
        self.page_label = QLabel("")
        self.page_label.setObjectName("Meta")
        self.abbrev_label.setFont(QFont("Arial", 14))
        self.page_label.setFont(QFont("Arial", 14))
        meta_row.addStretch()
        meta_row.addWidget(self.abbrev_label)
        meta_row.addSpacing(20)
        meta_row.addWidget(self.page_label)
        meta_row.addStretch()

        self.btn_prev = QPushButton("前一个单词")
        self.btn_show = QPushButton("显示答案")
        self.btn_next = QPushButton("下一个单词")
        self.btn_prev.clicked.connect(self._prev)
        self.btn_show.clicked.connect(self._show_answer)
        self.btn_next.clicked.connect(self._next)

        nav_row = QHBoxLayout()
        nav_row.addStretch()
        nav_row.addWidget(self.btn_prev)
        nav_row.addSpacing(16)
        nav_row.addWidget(self.btn_show)
        nav_row.addSpacing(16)
        nav_row.addWidget(self.btn_next)
        nav_row.addStretch()

        self.btn_right = QPushButton("答对了")
        self.btn_wrong = QPushButton("没答对")
        self.btn_right.clicked.connect(lambda: self._grade_answer(True))
        self.btn_wrong.clicked.connect(lambda: self._grade_answer(False))

        grade_row = QHBoxLayout()
        grade_row.addStretch()
        grade_row.addWidget(self.btn_right)
        grade_row.addSpacing(16)
        grade_row.addWidget(self.btn_wrong)
        grade_row.addStretch()

        self.gif_label = QLabel("")
        self.gif_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.gif_label.setMinimumHeight(210)
        self.gif_label.setMaximumHeight(260)

        self.wrong_count_label = QLabel("错误次数: 0")
        self.wrong_count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.wrong_count_label.setFont(QFont("Arial", 12))
        self.wrong_count_label.setStyleSheet("color:#6b7a88;")

        self.progress_label = QLabel("")
        self.progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.progress_label.setFont(QFont("Arial", 12))
        self.progress_label.setStyleSheet("color:#6b7a88;")

        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.addLayout(top_row)
        layout.addWidget(self.mode_hint)
        layout.addStretch()
        layout.addWidget(self.key_label)
        layout.addWidget(self.meaning_label)
        layout.addLayout(meta_row)
        layout.addSpacing(8)
        layout.addLayout(nav_row)
        layout.addLayout(grade_row)
        layout.addWidget(self.gif_label)
        layout.addSpacing(6)
        layout.addWidget(self.wrong_count_label)
        layout.addWidget(self.progress_label)
        layout.addStretch()

    def _render(self) -> None:
        self._stop_auto_timers()
        self._answer_shown = False

        if not self.words:
            self.key_label.setText("暂无词条")
            self.meaning_label.clear()
            self.abbrev_label.clear()
            self.page_label.clear()
            self.btn_prev.setDisabled(True)
            self.btn_show.setDisabled(True)
            self.btn_next.setDisabled(True)
            self.btn_right.setVisible(False)
            self.btn_wrong.setVisible(False)
            self._clear_gif()
            return

        entry = self.words[self.index]
        self.key_label.setText(entry.key)
        self.meaning_label.clear()
        self.abbrev_label.clear()
        self.page_label.clear()
        self.btn_right.setVisible(False)
        self.btn_wrong.setVisible(False)
        self._clear_gif()
        self._update_nav_state()
        self.progress_label.setText(f"{self.index + 1} / {len(self.words)}")
        self._apply_mode_ui()

        if self.settings.mode == "browse":
            self._timer_show.start(self.settings.auto_show_delay_sec * 1000)

    def _apply_mode_ui(self) -> None:
        is_browse = self.settings.mode == "browse"
        if is_browse:
            self.mode_hint.setText(
                f"阅览模式: {self.settings.auto_show_delay_sec}s 自动显示答案，"
                f"{self.settings.auto_next_delay_sec}s 自动下一题"
            )
            self.btn_show.setDisabled(True)
            self.btn_right.setVisible(False)
            self.btn_wrong.setVisible(False)
            self.wrong_count_label.setVisible(False)
        else:
            self.mode_hint.setText("默写模式: 手动显示答案并自评")
            self.btn_show.setDisabled(False)
            self.wrong_count_label.setVisible(True)

    def _show_answer(self) -> None:
        if not self.words or self._answer_shown:
            return
        entry = self.words[self.index]
        self._answer_shown = True
        self.meaning_label.setText(entry.meaning)
        self.abbrev_label.setText(f"缩写: {entry.abbrev}" if entry.abbrev else "")
        self.page_label.setText(f"页码: {entry.page}" if entry.page else "")
        self.mark_past(entry.key)

        if self.settings.mode == "browse":
            self._timer_next.start(self.settings.auto_next_delay_sec * 1000)
        else:
            self.btn_right.setVisible(True)
            self.btn_wrong.setVisible(True)

    def _save_current_word(self) -> None:
        if not self.words:
            return
        entry = self.words[self.index]
        created = self.mark_important(entry.key)
        if created:
            QMessageBox.information(self, "提示", "该单词已加入重要单词。")
        else:
            QMessageBox.information(self, "提示", "该单词已在重要单词中。")

    def _grade_answer(self, is_right: bool) -> None:
        if is_right:
            self._play_gif("right.gif")
            return

        self.wrong_count += 1
        if self.wrong_count >= 5:
            self._play_gif("lose.gif")
            self.wrong_count = 0
        else:
            self._play_gif("wrong.gif")
        self.wrong_count_label.setText(f"错误次数: {self.wrong_count}")

    def _auto_next(self) -> None:
        if self.index < len(self.words) - 1:
            self.index += 1
            self._render()

    def _play_gif(self, name: str) -> None:
        gif_path = self._gif_dir / name
        if not gif_path.exists():
            self.gif_label.setText(f"未找到 {name}")
            return

        reader = QImageReader(str(gif_path))
        source_size = reader.size()
        if source_size.width() <= 0 or source_size.height() <= 0:
            source_size = QSize(400, 220)
        self._gif_source_size = source_size
        target_size = self._calc_gif_size(source_size)

        if self._movie is not None:
            self._movie.stop()
        self._movie = QMovie(str(gif_path))
        self._movie.setScaledSize(target_size)
        self.gif_label.setMovie(self._movie)
        self._movie.start()

    def _clear_gif(self) -> None:
        if self._movie is not None:
            self._movie.stop()
            self._movie = None
        self._gif_source_size = None
        self.gif_label.clear()

    def _calc_gif_size(self, source_size: QSize) -> QSize:
        box_w = max(260, min(self.width() - 120, 560))
        box_h = 240
        target = QSize(source_size.width(), source_size.height())
        target.scale(box_w, box_h, Qt.AspectRatioMode.KeepAspectRatio)
        return target

    def _prev(self) -> None:
        if self.index > 0:
            self.index -= 1
            self._render()

    def _next(self) -> None:
        if self.index < len(self.words) - 1:
            self.index += 1
            self._render()

    def _update_nav_state(self) -> None:
        self.btn_prev.setDisabled(self.index == 0)
        self.btn_next.setDisabled(self.index >= len(self.words) - 1)

    def _stop_auto_timers(self) -> None:
        self._timer_show.stop()
        self._timer_next.stop()

    def _on_back_home(self) -> None:
        self._stop_auto_timers()
        self.back_home_clicked.emit()

    def resizeEvent(self, event) -> None:  # type: ignore[override]
        super().resizeEvent(event)
        if self._movie is not None and self._gif_source_size is not None:
            self._movie.setScaledSize(self._calc_gif_size(self._gif_source_size))

