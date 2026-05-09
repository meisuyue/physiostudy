from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import List

from PyQt6.QtCore import QSize, Qt, QTimer, QUrl, pyqtSignal
from PyQt6.QtGui import QFont, QIcon, QImageReader, QKeySequence, QMovie, QPainter, QPixmap, QShortcut
from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QMessageBox, QPushButton, QVBoxLayout, QWidget

from ..app_config import StudySettings
from ..project_paths import DATA_DIR
from ..storage import WordEntry
from ..tts_service import TextTtsManager


DEFAULT_ICON_DIR = DATA_DIR / "icons" / "default"
WORD_BG_PATH = DEFAULT_ICON_DIR / "word_page.png"
SAVE_ICON_PATH = DEFAULT_ICON_DIR / "save.png"
EYE_ICON_PATH = DEFAULT_ICON_DIR / "eye.png"
WRITE_ICON_PATH = DEFAULT_ICON_DIR / "write.png"


class StudyPage(QWidget):
    back_home_clicked = pyqtSignal()
    WRONG_COUNT_LIMIT = 5

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
        self._gif_side: str | None = None
        self._gif_dir = DATA_DIR / "icons" / "TandF"
        self._answer_shown = False
        self._background_pixmap = QPixmap(str(WORD_BG_PATH)) if WORD_BG_PATH.exists() else QPixmap()
        self._word_tts_manager: TextTtsManager | None = None

        self.audio_output = QAudioOutput(self)
        self.audio_output.setVolume(1.0)
        self.media_player = QMediaPlayer(self)
        self.media_player.setAudioOutput(self.audio_output)

        if self.lang == "e":
            self._word_tts_manager = TextTtsManager(scope_prefix="word_study", parent=self)
            self._word_tts_manager.audio_ready.connect(self._on_word_audio_ready)
            self._word_tts_manager.audio_failed.connect(self._on_word_audio_failed)

        self._timer_show = QTimer(self)
        self._timer_show.setSingleShot(True)
        self._timer_show.timeout.connect(self._show_answer)
        self._timer_next = QTimer(self)
        self._timer_next.setSingleShot(True)
        self._timer_next.timeout.connect(self._auto_next)

        self._prev_shortcut = QShortcut(QKeySequence("L"), self)
        self._prev_shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        self._prev_shortcut.activated.connect(self._prev)
        self._next_shortcut = QShortcut(QKeySequence("N"), self)
        self._next_shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        self._next_shortcut.activated.connect(self._next)
        self._answer_shortcut = QShortcut(QKeySequence("S"), self)
        self._answer_shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        self._answer_shortcut.activated.connect(self._toggle_answer_visibility)
        self._replay_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Space), self)
        self._replay_shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        self._replay_shortcut.activated.connect(self._handle_replay_shortcut)

        self._build_ui()
        if not self.words:
            QMessageBox.warning(self, "提示", "词库为空，无法开始学习。")
        self._render()

    def _build_ui(self) -> None:
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        self.setStyleSheet(
            """
            QLabel {
                background: transparent;
            }
            QFrame#GlassPanel {
                background: rgba(255, 255, 255, 0.72);
                border: 1px solid rgba(255, 255, 255, 0.88);
                border-radius: 30px;
            }
            QFrame#WordCard {
                background: rgba(255, 255, 255, 0.8);
                border: 1px solid rgba(255, 255, 255, 0.92);
                border-radius: 34px;
            }
            QLabel#ModeHint {
                color: #6b63c8;
                font-size: 15px;
                font-weight: 700;
            }
            QLabel#KeyLabel {
                color: #263f9f;
                font-size: 40px;
                font-weight: 900;
            }
            QLabel#Meaning {
                color: #7a74e7;
                font-size: 16px;
                font-weight: 700;
            }
            QFrame#PulseLine {
                background: rgba(216, 189, 255, 0.8);
                min-height: 2px;
                max-height: 2px;
                border-radius: 1px;
            }
            QLabel#PulseDot {
                color: #c99cf5;
                font-size: 22px;
                font-weight: 800;
            }
            QLabel#Meta {
                color: #6e63d4;
                font-size: 13px;
                font-weight: 700;
            }
            QPushButton {
                padding: 12px 20px;
                font-size: 16px;
                font-weight: 700;
                border-radius: 18px;
                color: #3b57bc;
                background: rgba(255, 255, 255, 0.88);
                border: 1px solid rgba(188, 198, 255, 0.96);
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 1.0);
            }
            QPushButton:disabled {
                background: rgba(240, 242, 252, 0.9);
                color: #9aa8b6;
            }
            QPushButton#PrimaryBtn {
                min-width: 160px;
            }
            QPushButton#SaveBtn {
                padding-left: 16px;
                padding-right: 16px;
                min-width: 170px;
            }
            QPushButton#RightBtn {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                            stop:0 rgba(95, 145, 255, 0.98),
                                            stop:1 rgba(142, 175, 255, 0.98));
                color: white;
                border: 1px solid rgba(114, 147, 255, 1.0);
                min-width: 190px;
            }
            QPushButton#WrongBtn {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                            stop:0 rgba(255, 194, 225, 0.98),
                                            stop:1 rgba(255, 145, 193, 0.98));
                color: white;
                border: 1px solid rgba(255, 160, 200, 1.0);
                min-width: 190px;
            }
            QFrame#AnswerPanel {
                background: rgba(255, 255, 255, 0.76);
                border: 1px solid rgba(255, 255, 255, 0.9);
                border-radius: 28px;
            }
            QLabel#AnswerHint {
                color: #7385df;
                font-size: 14px;
                font-weight: 700;
            }
            QLabel#AnswerContent {
                color: #314fb2;
                font-size: 24px;
                font-weight: 700;
            }
            QFrame#AnswerDivider {
                background: rgba(208, 198, 245, 0.75);
                min-height: 1px;
                max-height: 1px;
            }
            QFrame#StatusBar {
                background: rgba(255, 255, 255, 0.7);
                border: 1px solid rgba(255, 255, 255, 0.88);
                border-radius: 22px;
            }
            QLabel#StatusText {
                color: #6677cf;
                font-size: 13px;
                font-weight: 700;
            }
            QLabel#DividerBar {
                color: rgba(170, 170, 210, 0.9);
                font-size: 18px;
            }
            """
        )

        root = QVBoxLayout(self)
        root.setContentsMargins(26, 24, 26, 24)
        root.setSpacing(18)

        top_row = QHBoxLayout()
        top_row.setSpacing(16)
        self.btn_back_home = QPushButton("返回首页")
        self.btn_back_home.setObjectName("PrimaryBtn")
        self.btn_back_home.clicked.connect(self._on_back_home)
        self.btn_save_word = QPushButton("保存该单词")
        self.btn_save_word.setObjectName("SaveBtn")
        self.btn_save_word.clicked.connect(self._save_current_word)
        self._set_button_icon(self.btn_save_word, SAVE_ICON_PATH, 22)
        top_row.addWidget(self.btn_back_home)
        top_row.addStretch()
        top_row.addWidget(self.btn_save_word)

        self.mode_hint = QLabel("")
        self.mode_hint.setObjectName("ModeHint")
        self.mode_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.mode_hint.setFont(QFont("Microsoft YaHei UI", 11, QFont.Weight.Bold))

        self.word_card = QFrame()
        self.word_card.setObjectName("WordCard")
        word_layout = QVBoxLayout(self.word_card)
        word_layout.setContentsMargins(54, 42, 54, 28)
        word_layout.setSpacing(14)

        self.key_label = QLabel("--")
        self.key_label.setObjectName("KeyLabel")
        self.key_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.key_label.setFont(QFont("Segoe UI", 28, QFont.Weight.Black))
        self.key_label.setWordWrap(True)
        self.key_label.setMinimumHeight(150)

        self.meaning_label = QLabel("")
        self.meaning_label.setObjectName("Meaning")
        self.meaning_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.meaning_label.setFont(QFont("Microsoft YaHei UI", 15, QFont.Weight.Bold))
        self.meaning_label.setWordWrap(True)
        self.meaning_label.setVisible(False)

        pulse_row = QHBoxLayout()
        pulse_row.addStretch()
        left_pulse = QFrame()
        left_pulse.setObjectName("PulseLine")
        left_pulse.setFixedWidth(320)
        pulse_dot = QLabel("∿")
        pulse_dot.setObjectName("PulseDot")
        right_pulse = QFrame()
        right_pulse.setObjectName("PulseLine")
        right_pulse.setFixedWidth(320)
        pulse_row.addWidget(left_pulse)
        pulse_row.addSpacing(12)
        pulse_row.addWidget(pulse_dot)
        pulse_row.addSpacing(12)
        pulse_row.addWidget(right_pulse)
        pulse_row.addStretch()

        meta_row = QHBoxLayout()
        meta_row.setSpacing(42)
        meta_row.addStretch()
        self.abbrev_label = QLabel("")
        self.abbrev_label.setObjectName("Meta")
        self.page_label = QLabel("")
        self.page_label.setObjectName("Meta")
        self.abbrev_label.setFont(QFont("Microsoft YaHei UI", 12, QFont.Weight.Bold))
        self.page_label.setFont(QFont("Microsoft YaHei UI", 12, QFont.Weight.Bold))
        meta_row.addWidget(self.abbrev_label)
        meta_row.addWidget(self.page_label)
        meta_row.addStretch()

        word_layout.addWidget(self.key_label)
        word_layout.addLayout(pulse_row)
        word_layout.addLayout(meta_row)

        control_panel = QFrame()
        control_panel.setObjectName("GlassPanel")
        control_layout = QVBoxLayout(control_panel)
        control_layout.setContentsMargins(26, 18, 26, 18)
        control_layout.setSpacing(14)

        self.btn_prev = QPushButton("上一题")
        self.btn_prev.setObjectName("PrimaryBtn")
        self.btn_show = QPushButton("显示答案")
        self.btn_show.setObjectName("PrimaryBtn")
        self._set_button_icon(self.btn_show, EYE_ICON_PATH, 20)
        self.btn_next = QPushButton("下一题")
        self.btn_next.setObjectName("PrimaryBtn")
        self.btn_prev.clicked.connect(self._prev)
        self.btn_show.clicked.connect(self._show_answer)
        self.btn_next.clicked.connect(self._next)

        nav_row = QHBoxLayout()
        nav_row.setSpacing(18)
        nav_row.addWidget(self.btn_prev)
        nav_row.addWidget(self.btn_show)
        nav_row.addWidget(self.btn_next)

        self.btn_right = QPushButton("答对了")
        self.btn_right.setObjectName("RightBtn")
        self.btn_wrong = QPushButton("没答对")
        self.btn_wrong.setObjectName("WrongBtn")
        self.btn_right.clicked.connect(lambda: self._grade_answer(True))
        self.btn_wrong.clicked.connect(lambda: self._grade_answer(False))

        grade_row = QHBoxLayout()
        grade_row.setSpacing(18)
        grade_row.addStretch()
        grade_row.addWidget(self.btn_right)
        grade_row.addWidget(self.btn_wrong)
        grade_row.addStretch()

        control_layout.addLayout(nav_row)
        control_layout.addLayout(grade_row)

        answer_panel = QFrame()
        answer_panel.setObjectName("AnswerPanel")
        answer_layout = QVBoxLayout(answer_panel)
        answer_layout.setContentsMargins(36, 26, 36, 24)
        answer_layout.setSpacing(18)

        answer_head = QHBoxLayout()
        answer_head.setSpacing(10)
        self.answer_icon_label = QLabel()
        self.answer_icon_label.setFixedSize(26, 26)
        self._set_label_icon(self.answer_icon_label, WRITE_ICON_PATH, 26)
        self.answer_hint_label = QLabel("答案将显示在此处...")
        self.answer_hint_label.setObjectName("AnswerHint")
        self.answer_hint_label.setFont(QFont("Microsoft YaHei UI", 12, QFont.Weight.Bold))
        answer_head.addWidget(self.answer_icon_label)
        answer_head.addWidget(self.answer_hint_label)
        answer_head.addStretch()

        answer_divider = QFrame()
        answer_divider.setObjectName("AnswerDivider")

        self.answer_content_label = QLabel("")
        self.answer_content_label.setObjectName("AnswerContent")
        self.answer_content_label.setFont(QFont("Microsoft YaHei UI", 18, QFont.Weight.Bold))
        self.answer_content_label.setWordWrap(True)
        self.answer_content_label.setMinimumHeight(92)
        self.answer_content_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

        answer_layout.addLayout(answer_head)
        answer_layout.addWidget(answer_divider)
        answer_layout.addWidget(self.answer_content_label)

        self.left_gif_label = QLabel("")
        self.left_gif_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.left_gif_label.setFixedSize(240, 220)
        self.right_gif_label = QLabel("")
        self.right_gif_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.right_gif_label.setFixedSize(240, 220)

        status_bar = QFrame()
        status_bar.setObjectName("StatusBar")
        status_layout = QHBoxLayout(status_bar)
        status_layout.setContentsMargins(26, 14, 26, 14)
        status_layout.setSpacing(16)

        self.wrong_count_label = QLabel(f"错误次数: 0/{self.WRONG_COUNT_LIMIT}")
        self.wrong_count_label.setObjectName("StatusText")
        self.wrong_count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.progress_label = QLabel("")
        self.progress_label.setObjectName("StatusText")
        self.progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        divider_bar = QLabel("|")
        divider_bar.setObjectName("DividerBar")
        divider_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)

        status_layout.addStretch()
        status_layout.addWidget(self.wrong_count_label)
        status_layout.addWidget(divider_bar)
        status_layout.addWidget(self.progress_label)
        status_layout.addStretch()

        root.addLayout(top_row)
        root.addWidget(self.mode_hint)
        root.addSpacing(8)
        root.addWidget(self.word_card, alignment=Qt.AlignmentFlag.AlignHCenter)
        root.addWidget(control_panel, alignment=Qt.AlignmentFlag.AlignHCenter)
        answer_row = QHBoxLayout()
        answer_row.setSpacing(20)
        answer_row.addStretch()
        answer_row.addWidget(self.left_gif_label, alignment=Qt.AlignmentFlag.AlignVCenter)
        answer_row.addWidget(answer_panel, alignment=Qt.AlignmentFlag.AlignVCenter)
        answer_row.addWidget(self.right_gif_label, alignment=Qt.AlignmentFlag.AlignVCenter)
        answer_row.addStretch()

        root.addLayout(answer_row)
        root.addWidget(status_bar, alignment=Qt.AlignmentFlag.AlignHCenter)
        root.addStretch()

        self.word_card.setMaximumWidth(860)
        control_panel.setMaximumWidth(660)
        answer_panel.setMinimumWidth(980)
        answer_panel.setMaximumWidth(1280)
        status_bar.setMaximumWidth(780)

    def _set_button_icon(self, button: QPushButton, path: Path, size: int) -> None:
        if path.exists():
            button.setIcon(QIcon(str(path)))
            button.setIconSize(QSize(size, size))

    def _set_label_icon(self, label: QLabel, path: Path, size: int) -> None:
        if path.exists():
            pix = QPixmap(str(path)).scaled(
                size,
                size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            label.setPixmap(pix)

    def _render(self) -> None:
        self._stop_auto_timers()
        self._answer_shown = False

        if not self.words:
            self.key_label.setText("暂无词条")
            self.answer_content_label.clear()
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
        self.answer_hint_label.setText("答案将显示在此处...")
        self.answer_content_label.clear()
        self.abbrev_label.clear()
        self.page_label.clear()
        self.btn_show.setText("显示答案")
        self.btn_right.setVisible(False)
        self.btn_wrong.setVisible(False)
        self._clear_gif()
        self._update_nav_state()
        self.progress_label.setText(f"{self.index + 1} / {len(self.words)}")
        self._apply_mode_ui()

        if self.settings.mode == "browse":
            self._timer_show.start(self.settings.auto_show_delay_sec * 1000)
        self._prepare_current_word_audio(auto_play=True)

    def _apply_mode_ui(self) -> None:
        is_browse = self.settings.mode == "browse"
        if is_browse:
            self.mode_hint.setText(
                f"浏览模式：{self.settings.auto_show_delay_sec}s 自动显示答案，"
                f"{self.settings.auto_next_delay_sec}s 自动下一题"
            )
            self.btn_show.setDisabled(True)
            self.btn_right.setVisible(False)
            self.btn_wrong.setVisible(False)
            self.wrong_count_label.setVisible(False)
        else:
            self.mode_hint.setText("默写模式：手动显示答案并自评")
            self.btn_show.setDisabled(False)
            self.wrong_count_label.setVisible(True)
            self.wrong_count_label.setText(f"错误次数: {self.wrong_count}/{self.WRONG_COUNT_LIMIT}")

    def _show_answer(self) -> None:
        if not self.words or self._answer_shown:
            return
        entry = self.words[self.index]
        self._answer_shown = True
        self.answer_hint_label.setText("答案")
        self.answer_content_label.setText(entry.meaning)
        self.abbrev_label.setText(f"缩写：{entry.abbrev}" if entry.abbrev else "")
        self.page_label.setText(f"页码：{entry.page}" if entry.page else "")
        self.mark_past(entry.key)

        if self.settings.mode == "browse":
            self._timer_next.start(self.settings.auto_next_delay_sec * 1000)
        else:
            self.btn_right.setVisible(True)
            self.btn_wrong.setVisible(True)
        self.btn_show.setText("隐藏答案")

    def _hide_answer(self) -> None:
        if not self._answer_shown:
            return
        self._timer_next.stop()
        self._answer_shown = False
        self.answer_hint_label.setText("答案将显示在此处...")
        self.answer_content_label.clear()
        self.abbrev_label.clear()
        self.page_label.clear()
        self.btn_right.setVisible(False)
        self.btn_wrong.setVisible(False)
        self.btn_show.setText("显示答案")

    def _toggle_answer_visibility(self) -> None:
        if not self.words:
            return
        if self._answer_shown:
            self._hide_answer()
            return
        self._show_answer()

    def _save_current_word(self) -> None:
        if not self.words:
            return
        entry = self.words[self.index]
        created = self.mark_important(entry.key)
        if created:
            QMessageBox.information(self, "提示", "该单词已加入重点单词。")
        else:
            QMessageBox.information(self, "提示", "该单词已在重点单词中。")

    def _prepare_current_word_audio(self, auto_play: bool = False) -> None:
        if self.lang != "e" or self._word_tts_manager is None:
            return
        current_text = self._word_audio_text_at(self.index)
        if not current_text:
            return

        # Render the current word immediately, and prefetch the next one in
        # parallel so navigation usually does not need to wait for TTS.
        self._word_tts_manager.ensure_text(current_text)
        self._prefetch_word_audio_at(self.index + 1)
        if auto_play:
            self._play_current_word_audio()

    def _word_audio_text_at(self, index: int) -> str:
        if self.lang != "e" or not self.words:
            return ""
        if index < 0 or index >= len(self.words):
            return ""
        return (self.words[index].key or "").strip()

    def _prefetch_word_audio_at(self, index: int) -> None:
        if self._word_tts_manager is None:
            return
        next_text = self._word_audio_text_at(index)
        if next_text:
            self._word_tts_manager.ensure_text(next_text)

    def _play_current_word_audio(self) -> None:
        if self.lang != "e" or not self.words or self._word_tts_manager is None:
            return
        current_text = self._word_audio_text_at(self.index)
        if not current_text:
            return
        self._word_tts_manager.ensure_text(current_text)
        path = self._word_tts_manager.get_audio_path(current_text)
        if path is None or not path.exists():
            return
        self.media_player.stop()
        self.media_player.setSource(QUrl.fromLocalFile(str(path)))
        self.media_player.play()

    def _on_word_audio_ready(self, source_text: str, path_str: str) -> None:
        if not self.words or self.lang != "e":
            return
        current_text = self._word_audio_text_at(self.index)
        if source_text != current_text:
            return
        if Path(path_str).exists():
            self._play_current_word_audio()

    def _on_word_audio_failed(self, _source_text: str) -> None:
        return

    def _grade_answer(self, is_right: bool) -> None:
        if is_right:
            self._gif_side = "left"
            self._play_gif("right.gif")
            return

        self.wrong_count += 1
        self._gif_side = "right"
        if self.wrong_count >= self.WRONG_COUNT_LIMIT:
            self._play_gif("lose.gif")
            self.wrong_count = 0
        else:
            self._play_gif("wrong.gif")
        self.wrong_count_label.setText(f"错误次数: {self.wrong_count}/{self.WRONG_COUNT_LIMIT}")

    def _auto_next(self) -> None:
        if self.index < len(self.words) - 1:
            self.index += 1
            self._render()

    def _play_gif(self, name: str) -> None:
        gif_path = self._gif_dir / name
        if not gif_path.exists():
            target_label = self.left_gif_label if self._gif_side == "left" else self.right_gif_label
            target_label.setText(f"未找到 {name}")
            return

        reader = QImageReader(str(gif_path))
        source_size = reader.size()
        if source_size.width() <= 0 or source_size.height() <= 0:
            source_size = QSize(400, 220)
        self._gif_source_size = source_size
        target_size = self._calc_gif_size(source_size)
        target_label = self.left_gif_label if self._gif_side == "left" else self.right_gif_label
        other_label = self.right_gif_label if self._gif_side == "left" else self.left_gif_label
        target_label.clear()
        other_label.clear()

        if self._movie is not None:
            self._movie.stop()
        self._movie = QMovie(str(gif_path))
        self._movie.setScaledSize(target_size)
        target_label.setMovie(self._movie)
        self._movie.start()

    def _clear_gif(self) -> None:
        if self._movie is not None:
            self._movie.stop()
            self._movie = None
        self._gif_source_size = None
        self._gif_side = None
        self.left_gif_label.clear()
        self.right_gif_label.clear()

    def _calc_gif_size(self, source_size: QSize) -> QSize:
        box_w = 220
        box_h = 220
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

    def _handle_replay_shortcut(self) -> None:
        if self.lang == "e":
            self._play_current_word_audio()

    def cleanup(self) -> None:
        self._stop_auto_timers()
        self.media_player.stop()
        if self._word_tts_manager is not None:
            try:
                self._word_tts_manager.audio_ready.disconnect(self._on_word_audio_ready)
                self._word_tts_manager.audio_failed.disconnect(self._on_word_audio_failed)
            except TypeError:
                pass
            self._word_tts_manager.shutdown()
            self._word_tts_manager = None

    def paintEvent(self, event) -> None:  # type: ignore[override]
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        if not self._background_pixmap.isNull():
            painter.drawPixmap(self.rect(), self._background_pixmap)
        else:
            painter.fillRect(self.rect(), Qt.GlobalColor.white)
        painter.end()
