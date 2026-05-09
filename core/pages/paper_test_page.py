from __future__ import annotations

from pathlib import Path
from typing import List

from PyQt6.QtCore import QTimer, Qt, QUrl, pyqtSignal
from PyQt6.QtGui import QFont, QIcon, QKeySequence, QPainter, QPixmap, QShortcut
from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ..project_paths import DATA_DIR
from ..storage import PaperQuestion
from ..tts_service import PaperTtsManager


BG_PATH = DATA_DIR / "icons" / "default" / "loading_page.png"
PLAY_ICON_PATH = DATA_DIR / "icons" / "default" / "play.png"
FILE_ICON_PATH = DATA_DIR / "icons" / "default" / "file.png"


class PaperTestPage(QWidget):
    back_home_clicked = pyqtSignal()
    choose_other_paper_clicked = pyqtSignal()

    def __init__(self, paper_name: str, questions: List[PaperQuestion], tts_manager: PaperTtsManager) -> None:
        super().__init__()
        self.paper_name = paper_name
        self.questions = questions
        self.tts_manager = tts_manager
        self.index = 0
        self.question_visible = False
        self.answer_visible = False
        self.analysis_visible = False

        self._background_pixmap = QPixmap(str(BG_PATH)) if BG_PATH.exists() else QPixmap()
        self._play_pixmap = QPixmap(str(PLAY_ICON_PATH)) if PLAY_ICON_PATH.exists() else QPixmap()
        self._file_pixmap = QPixmap(str(FILE_ICON_PATH)) if FILE_ICON_PATH.exists() else QPixmap()

        self.audio_output = QAudioOutput(self)
        self.audio_output.setVolume(1.0)
        self.media_player = QMediaPlayer(self)
        self.media_player.setAudioOutput(self.audio_output)
        self.media_player.errorOccurred.connect(self._on_audio_error)

        self.tts_manager.audio_ready.connect(self._on_audio_ready)
        self.tts_manager.audio_failed.connect(self._on_audio_failed)

        self._prev_shortcut = QShortcut(QKeySequence("L"), self)
        self._prev_shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        self._prev_shortcut.activated.connect(self._prev)
        self._next_shortcut = QShortcut(QKeySequence("N"), self)
        self._next_shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        self._next_shortcut.activated.connect(self._next)
        self._answer_shortcut = QShortcut(QKeySequence("S"), self)
        self._answer_shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        self._answer_shortcut.activated.connect(self._toggle_answer)
        self._analysis_shortcut = QShortcut(QKeySequence("E"), self)
        self._analysis_shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        self._analysis_shortcut.activated.connect(self._toggle_analysis)
        self._replay_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Space), self)
        self._replay_shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        self._replay_shortcut.activated.connect(self._play_current_audio)

        self._build_ui()
        self._apply_responsive_layout()
        QTimer.singleShot(0, self._apply_responsive_layout)
        self._render(auto_play=True)

    def _build_ui(self) -> None:
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        self.setStyleSheet(
            """
            QLabel {
                background: transparent;
            }
            QPushButton#TopButton {
                background: rgba(255, 255, 255, 0.88);
                color: #466bdb;
                border: 1px solid rgba(255, 255, 255, 0.96);
                border-radius: 22px;
                padding: 14px 26px;
                font-size: 16px;
                font-weight: 700;
            }
            QPushButton#TopButton:hover {
                background: rgba(255, 255, 255, 0.96);
            }
            QLabel#PaperTitle {
                color: #173583;
                font-size: 34px;
                font-weight: 900;
            }
            QFrame#DividerLine {
                background: rgba(215, 187, 255, 0.84);
                min-height: 2px;
                max-height: 2px;
                border-radius: 2px;
            }
            QLabel#ProgressChip {
                background: rgba(255, 255, 255, 0.72);
                border: 1px solid rgba(189, 206, 255, 0.95);
                border-radius: 18px;
                color: #425fd0;
                padding: 8px 18px;
                font-size: 16px;
                font-weight: 800;
            }
            QFrame#QuestionStage {
                background: rgba(255, 255, 255, 0.52);
                border: 1px solid rgba(255, 255, 255, 0.88);
                border-radius: 30px;
            }
            QFrame#QuestionInner {
                background: rgba(255, 255, 255, 0.24);
                border: 2px dashed rgba(184, 204, 255, 0.9);
                border-radius: 24px;
            }
            QLabel#QuestionText {
                color: #173c93;
                font-size: 24px;
                font-weight: 800;
            }
            QLabel#QuestionHint {
                color: rgba(122, 141, 196, 0.96);
                font-size: 15px;
                font-weight: 700;
            }
            QPushButton#PlayButton {
                background: rgba(255, 255, 255, 0.82);
                border: 1px solid rgba(214, 220, 255, 0.96);
                border-radius: 34px;
                min-width: 68px;
                max-width: 68px;
                min-height: 68px;
                max-height: 68px;
            }
            QPushButton#PlayButton:hover {
                background: rgba(255, 255, 255, 0.96);
            }
            QLabel#AudioStatus {
                color: #4564c7;
                font-size: 14px;
                font-weight: 700;
            }
            QFrame#AnswerStage {
                background: rgba(255, 255, 255, 0.56);
                border: 1px solid rgba(255, 255, 255, 0.9);
                border-radius: 24px;
            }
            QLabel#AnswerPlaceholder {
                color: rgba(122, 141, 196, 0.96);
                font-size: 15px;
                font-weight: 700;
            }
            QTextEdit {
                background: transparent;
                border: none;
                color: #183d96;
                font-size: 18px;
                padding: 8px;
            }
            QPushButton#BottomButton {
                background: rgba(255, 255, 255, 0.86);
                color: #3555c2;
                border: 1px solid rgba(214, 220, 255, 0.96);
                border-radius: 20px;
                padding: 16px 26px;
                font-size: 16px;
                font-weight: 800;
                min-width: 170px;
            }
            QPushButton#BottomButton:hover {
                background: rgba(255, 255, 255, 0.96);
            }
            QPushButton#BottomButton[primary='true'] {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                            stop:0 rgba(88, 145, 255, 0.98),
                                            stop:1 rgba(236, 141, 255, 0.98));
                color: white;
                border-color: rgba(255, 255, 255, 0.92);
            }
            QPushButton#BottomButton:disabled {
                background: rgba(233, 237, 248, 0.82);
                color: rgba(154, 165, 198, 0.96);
            }
            """
        )

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 18, 24, 24)
        root.setSpacing(18)

        top_row = QHBoxLayout()
        top_row.setSpacing(18)
        self.btn_back_home = QPushButton("\u2190 \u8fd4\u56de\u9996\u9875")
        self.btn_back_home.setObjectName("TopButton")
        self.btn_back_home.clicked.connect(self.back_home_clicked.emit)

        self.btn_choose_other = QPushButton("\u21bb \u66f4\u6362\u8bd5\u5377")
        self.btn_choose_other.setObjectName("TopButton")
        self.btn_choose_other.clicked.connect(self.choose_other_paper_clicked.emit)

        top_row.addWidget(self.btn_back_home)
        top_row.addWidget(self.btn_choose_other)
        top_row.addStretch()

        self.paper_title = QLabel("")
        self.paper_title.setObjectName("PaperTitle")
        self.paper_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.paper_title.setFont(QFont("Microsoft YaHei UI", 30, QFont.Weight.Black))

        divider = QHBoxLayout()
        divider.addStretch()
        self.left_line = QFrame()
        self.left_line.setObjectName("DividerLine")
        self.progress_label = QLabel("")
        self.progress_label.setObjectName("ProgressChip")
        self.progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.right_line = QFrame()
        self.right_line.setObjectName("DividerLine")
        divider.addWidget(self.left_line)
        divider.addSpacing(18)
        divider.addWidget(self.progress_label)
        divider.addSpacing(18)
        divider.addWidget(self.right_line)
        divider.addStretch()

        self.question_stage = QFrame()
        self.question_stage.setObjectName("QuestionStage")
        self.question_stage.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        q_stage_layout = QVBoxLayout(self.question_stage)
        q_stage_layout.setContentsMargins(24, 24, 24, 24)
        q_stage_layout.setSpacing(18)

        self.question_inner = QFrame()
        self.question_inner.setObjectName("QuestionInner")
        self.question_inner.setMinimumHeight(190)
        inner_layout = QVBoxLayout(self.question_inner)
        inner_layout.setContentsMargins(32, 20, 32, 20)
        inner_layout.setSpacing(10)
        inner_layout.addStretch()

        self.file_icon_label = QLabel()
        self.file_icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if not self._file_pixmap.isNull():
            self.file_icon_label.setPixmap(
                self._file_pixmap.scaled(
                    72,
                    72,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
        else:
            self.file_icon_label.setText("?")

        self.question_label = QLabel("")
        self.question_label.setObjectName("QuestionText")
        self.question_label.setWordWrap(True)
        self.question_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.question_hint_label = QLabel("")
        self.question_hint_label.setObjectName("QuestionHint")
        self.question_hint_label.setWordWrap(True)
        self.question_hint_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        inner_layout.addWidget(self.file_icon_label, alignment=Qt.AlignmentFlag.AlignHCenter)
        inner_layout.addWidget(self.question_label)
        inner_layout.addWidget(self.question_hint_label)
        inner_layout.addStretch()

        q_stage_layout.addWidget(self.question_inner)

        play_col = QVBoxLayout()
        play_col.setSpacing(10)

        self.btn_play_audio = QPushButton()
        self.btn_play_audio.setObjectName("PlayButton")
        if not self._play_pixmap.isNull():
            play_icon = self._play_pixmap.scaled(
                34, 34, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
            )
            self.btn_play_audio.setIcon(QIcon(play_icon))
            self.btn_play_audio.setIconSize(play_icon.size())
        self.btn_play_audio.clicked.connect(self._play_current_audio)

        self.audio_status_label = QLabel("")
        self.audio_status_label.setObjectName("AudioStatus")
        self.audio_status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        play_col.addWidget(self.btn_play_audio, alignment=Qt.AlignmentFlag.AlignHCenter)
        play_col.addWidget(self.audio_status_label)
        q_stage_layout.addLayout(play_col)

        self.answer_stage = QFrame()
        self.answer_stage.setObjectName("AnswerStage")
        self.answer_stage.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        answer_layout = QVBoxLayout(self.answer_stage)
        answer_layout.setContentsMargins(28, 18, 28, 18)
        answer_layout.setSpacing(10)

        self.answer_placeholder = QLabel("\u7b54\u6848\u4e0e\u89e3\u6790\u5c06\u5728\u6b64\u5904\u663e\u793a")
        self.answer_placeholder.setObjectName("AnswerPlaceholder")
        self.answer_placeholder.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        self.answer_box = QTextEdit()
        self.answer_box.setReadOnly(True)
        self.answer_box.setMinimumHeight(92)
        self.answer_box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        answer_layout.addWidget(self.answer_placeholder)
        answer_layout.addWidget(self.answer_box)

        nav_row = QHBoxLayout()
        nav_row.setSpacing(18)
        nav_row.addStretch()

        self.btn_prev = QPushButton("\u2190 \u4e0a\u4e00\u9898")
        self.btn_prev.setObjectName("BottomButton")
        self.btn_prev.clicked.connect(self._prev)

        self.btn_show_question = QPushButton("\u25c9 \u663e\u793a\u5f53\u524d\u9898\u76ee")
        self.btn_show_question.setObjectName("BottomButton")
        self.btn_show_question.setProperty("primary", True)
        self.btn_show_question.style().unpolish(self.btn_show_question)
        self.btn_show_question.style().polish(self.btn_show_question)
        self.btn_show_question.clicked.connect(self._toggle_question)

        self.btn_show_answer = QPushButton("\u25eb \u663e\u793a\u7b54\u6848")
        self.btn_show_answer.setObjectName("BottomButton")
        self.btn_show_answer.clicked.connect(self._toggle_answer)

        self.btn_show_analysis = QPushButton("\u25a3 \u89e3\u6790")
        self.btn_show_analysis.setObjectName("BottomButton")
        self.btn_show_analysis.clicked.connect(self._toggle_analysis)

        self.btn_next = QPushButton("\u2192 \u4e0b\u4e00\u9898")
        self.btn_next.setObjectName("BottomButton")
        self.btn_next.clicked.connect(self._next)

        nav_row.addWidget(self.btn_prev)
        nav_row.addWidget(self.btn_show_question)
        nav_row.addWidget(self.btn_show_answer)
        nav_row.addWidget(self.btn_show_analysis)
        nav_row.addWidget(self.btn_next)
        nav_row.addStretch()

        root.addLayout(top_row)
        root.addSpacing(8)
        root.addWidget(self.paper_title)
        root.addLayout(divider)
        root.addWidget(self.question_stage, alignment=Qt.AlignmentFlag.AlignHCenter)
        root.addWidget(self.answer_stage, alignment=Qt.AlignmentFlag.AlignHCenter)
        root.addLayout(nav_row)

    def _apply_responsive_layout(self) -> None:
        page_width = max(self.width(), 960)
        content_width = max(760, min(1220, page_width - 120))
        divider_width = max(120, min(330, (content_width - 220) // 2))

        self.question_stage.setFixedWidth(content_width)
        self.answer_stage.setFixedWidth(content_width)
        self.left_line.setFixedWidth(divider_width)
        self.right_line.setFixedWidth(divider_width)
        self.answer_box.setMinimumHeight(92 if self.height() > 860 else 78)

    def _render(self, auto_play: bool = False) -> None:
        if not self.questions:
            self.paper_title.setText(self.paper_name)
            self.progress_label.setText("0 / 0")
            self.question_label.setText("\u5f53\u524d\u8bd5\u5377\u6ca1\u6709\u53ef\u7528\u9898\u76ee\u3002")
            self.question_hint_label.setText("")
            self.answer_box.setPlainText("")
            self.audio_status_label.setText("")
            self.btn_prev.setEnabled(False)
            self.btn_next.setEnabled(False)
            self.btn_show_question.setEnabled(False)
            self.btn_show_answer.setEnabled(False)
            self.btn_show_analysis.setEnabled(False)
            self.btn_play_audio.setEnabled(False)
            return

        current = self.questions[self.index]
        self.paper_title.setText(self.paper_name)
        self.progress_label.setText(f"{self.index + 1} / {len(self.questions)}")

        if self.question_visible:
            self.file_icon_label.setVisible(False)
            self.question_label.setText(current.question_en or "No question text.")
            self.question_hint_label.setText("")
        else:
            self.file_icon_label.setVisible(True)
            self.question_label.setText("\u5f53\u524d\u9898\u76ee\u5df2\u9690\u85cf\uff0c\u70b9\u51fb\u4e0b\u65b9\u6309\u94ae\u67e5\u770b")
            self.question_hint_label.setText("\u8bf7\u5148\u67e5\u770b\u9898\u76ee\u518d\u4f5c\u7b54")

        answer_parts: list[str] = []
        if self.answer_visible:
            answer_parts.append(f"\u7b54\u6848\uff1a{current.answer_en or 'N/A'}")
        if self.analysis_visible:
            answer_parts.append(f"\u89e3\u6790\uff1a{current.analysis_zh or '\u65e0'}")
        self.answer_box.setPlainText("\n\n".join(answer_parts))

        self.btn_show_question.setText(
            "\u9690\u85cf\u5f53\u524d\u9898\u76ee" if self.question_visible else "\u663e\u793a\u5f53\u524d\u9898\u76ee"
        )
        self.btn_show_answer.setText("\u9690\u85cf\u7b54\u6848" if self.answer_visible else "\u663e\u793a\u7b54\u6848")
        self.btn_show_analysis.setText("\u9690\u85cf\u89e3\u6790" if self.analysis_visible else "\u89e3\u6790")
        self.btn_prev.setEnabled(self.index > 0)
        self.btn_next.setEnabled(self.index < len(self.questions) - 1)
        self.btn_play_audio.setEnabled(True)

        if answer_parts:
            self.answer_placeholder.setText("\u7b54\u6848\u4e0e\u89e3\u6790\u5df2\u663e\u793a")
        else:
            self.answer_placeholder.setText("\u7b54\u6848\u4e0e\u89e3\u6790\u5c06\u5728\u6b64\u5904\u663e\u793a")

        self.tts_manager.ensure_question(self.index)
        path = self.tts_manager.get_audio_path(self.index)
        if path is not None and path.exists():
            self.audio_status_label.setText("\u64ad\u653e\u5f53\u524d\u9898\u76ee\u8bed\u97f3")
        else:
            self.audio_status_label.setText("\u5f53\u524d\u9898\u76ee\u8bed\u97f3\u751f\u6210\u4e2d...")

        if auto_play:
            self._play_current_audio()

    def _toggle_question(self) -> None:
        if not self.questions:
            return
        self.question_visible = not self.question_visible
        self._render(auto_play=False)

    def _toggle_answer(self) -> None:
        if not self.questions:
            return
        self.answer_visible = not self.answer_visible
        self._render(auto_play=False)

    def _toggle_analysis(self) -> None:
        if not self.questions:
            return
        self.analysis_visible = not self.analysis_visible
        self._render(auto_play=False)

    def _prev(self) -> None:
        if self.index <= 0:
            return
        self.index -= 1
        self.question_visible = False
        self.answer_visible = False
        self.analysis_visible = False
        self._render(auto_play=True)

    def _next(self) -> None:
        if self.index >= len(self.questions) - 1:
            return
        self.index += 1
        self.question_visible = False
        self.answer_visible = False
        self.analysis_visible = False
        self._render(auto_play=True)

    def _play_current_audio(self) -> None:
        if not self.questions:
            return
        self.tts_manager.ensure_question(self.index)
        path = self.tts_manager.get_audio_path(self.index)
        if path is None or not path.exists():
            self.audio_status_label.setText("\u5f53\u524d\u9898\u76ee\u8bed\u97f3\u751f\u6210\u4e2d...")
            return
        self.media_player.stop()
        self.media_player.setSource(QUrl.fromLocalFile(str(path)))
        self.media_player.play()
        self.audio_status_label.setText("\u64ad\u653e\u5f53\u524d\u9898\u76ee\u8bed\u97f3")

    def _on_audio_ready(self, index: int, path_str: str) -> None:
        if index != self.index:
            return
        if Path(path_str).exists():
            self.audio_status_label.setText("\u64ad\u653e\u5f53\u524d\u9898\u76ee\u8bed\u97f3")
            self._play_current_audio()

    def _on_audio_failed(self, index: int) -> None:
        if index == self.index:
            self.audio_status_label.setText("\u5f53\u524d\u9898\u76ee\u8bed\u97f3\u751f\u6210\u5931\u8d25")

    def _on_audio_error(self, *_args) -> None:
        self.audio_status_label.setText("\u5f53\u524d\u9898\u76ee\u8bed\u97f3\u64ad\u653e\u5931\u8d25")

    def cleanup(self) -> None:
        self.media_player.stop()
        try:
            self.tts_manager.audio_ready.disconnect(self._on_audio_ready)
            self.tts_manager.audio_failed.disconnect(self._on_audio_failed)
        except TypeError:
            pass

    def paintEvent(self, event) -> None:  # type: ignore[override]
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        if not self._background_pixmap.isNull():
            painter.drawPixmap(self.rect(), self._background_pixmap)
        else:
            painter.fillRect(self.rect(), Qt.GlobalColor.white)
        painter.end()

    def resizeEvent(self, event) -> None:  # type: ignore[override]
        super().resizeEvent(event)
        self._apply_responsive_layout()
