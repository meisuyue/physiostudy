from __future__ import annotations

from pathlib import Path

from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QSpinBox,
    QStackedWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app_config import StudySettings
from pages.study_page import StudyPage
from pages.welcome_page import WelcomePage
from storage import UserWordStore, WordEntry, load_word_list, search_word_meanings


BASE_DIR = Path(__file__).resolve().parent
ICON_PATH = BASE_DIR / "data" / "icons" / "default" / "logo.png"


class SettingsDialog(QDialog):
    def __init__(self, settings: StudySettings, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("学习设置")
        self.setModal(True)
        self.resize(420, 260)

        self.rb_dictation = QRadioButton("默写模式")
        self.rb_browse = QRadioButton("阅览模式")
        self.rb_dictation.toggled.connect(self._update_delay_enabled)
        self.rb_browse.toggled.connect(self._update_delay_enabled)

        self.show_delay = QSpinBox()
        self.show_delay.setRange(1, 999)
        self.show_delay.setSuffix(" 秒")

        self.next_delay = QSpinBox()
        self.next_delay.setRange(1, 999)
        self.next_delay.setSuffix(" 秒")

        if settings.mode == "browse":
            self.rb_browse.setChecked(True)
        else:
            self.rb_dictation.setChecked(True)
        self.show_delay.setValue(settings.auto_show_delay_sec)
        self.next_delay.setValue(settings.auto_next_delay_sec)
        self._update_delay_enabled()

        form = QFormLayout()
        mode_row = QHBoxLayout()
        mode_row.addWidget(self.rb_dictation)
        mode_row.addWidget(self.rb_browse)
        form.addRow(QLabel("模式"), mode_row)
        form.addRow(QLabel("自动显示答案延迟"), self.show_delay)
        form.addRow(QLabel("自动下一题延迟"), self.next_delay)

        btn_ok = QPushButton("保存")
        btn_cancel = QPushButton("取消")
        btn_ok.clicked.connect(self.accept)
        btn_cancel.clicked.connect(self.reject)
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_row.addWidget(btn_ok)
        btn_row.addWidget(btn_cancel)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addStretch()
        layout.addLayout(btn_row)

    def _update_delay_enabled(self) -> None:
        enabled = self.rb_browse.isChecked()
        self.show_delay.setEnabled(enabled)
        self.next_delay.setEnabled(enabled)

    def build_settings(self) -> StudySettings:
        mode = "browse" if self.rb_browse.isChecked() else "dictation"
        return StudySettings(
            mode=mode,
            auto_show_delay_sec=self.show_delay.value(),
            auto_next_delay_sec=self.next_delay.value(),
        )


class ReviewLangDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("复习标记单词")
        self.setModal(True)
        self.selected_lang: str | None = None
        self.resize(320, 140)

        tip = QLabel("请选择复习词库：")
        btn_c = QPushButton("中文词库")
        btn_e = QPushButton("英文词库")
        btn_c.clicked.connect(lambda: self._choose("c"))
        btn_e.clicked.connect(lambda: self._choose("e"))

        row = QHBoxLayout()
        row.addWidget(btn_c)
        row.addWidget(btn_e)

        layout = QVBoxLayout(self)
        layout.addWidget(tip)
        layout.addLayout(row)

    def _choose(self, lang: str) -> None:
        self.selected_lang = lang
        self.accept()


class SearchDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("查询单词")
        self.setModal(True)
        self.resize(560, 420)

        self.input_edit = QLineEdit()
        self.input_edit.setPlaceholderText("输入要查询的单词或关键词")

        self.threshold = QSpinBox()
        self.threshold.setRange(1, 100)
        self.threshold.setValue(60)
        self.threshold.setSuffix(" %")

        self.result_box = QTextEdit()
        self.result_box.setReadOnly(True)

        btn_search = QPushButton("查询")
        btn_search.clicked.connect(self._run_search)

        form = QFormLayout()
        form.addRow(QLabel("查询内容"), self.input_edit)
        form.addRow(QLabel("匹配阈值"), self.threshold)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(btn_search)
        layout.addWidget(self.result_box)

    def _run_search(self) -> None:
        query = self.input_edit.text().strip()
        if not query:
            self.result_box.setPlainText("请输入查询内容。")
            return
        threshold = self.threshold.value() / 100.0
        results = search_word_meanings(query, threshold=threshold)
        if not results:
            self.result_box.setPlainText("未找到符合阈值的结果。")
            return

        lines: list[str] = []
        for lang, key, meaning, score in results:
            lang_label = "中文" if lang == "c" else "英文"
            lines.append(f"[{lang_label}] {key} -> {meaning} (匹配度 {score:.2f})")
        self.result_box.setPlainText("\n".join(lines))


class MainWindow(QMainWindow):
    def __init__(self, username: str) -> None:
        super().__init__()
        self.username = username
        self.settings = StudySettings()
        self.user_words = UserWordStore(username)
        self.user_words.ensure_user_dirs()

        self.setWindowTitle("PhysioWords")
        self.resize(1100, 780)
        if ICON_PATH.exists():
            self.setWindowIcon(QIcon(str(ICON_PATH)))

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        self.welcome = WelcomePage(username=username)
        self.welcome.cn_clicked.connect(lambda: self._start_normal_study("c"))
        self.welcome.en_clicked.connect(lambda: self._start_normal_study("e"))
        self.welcome.settings_clicked.connect(self._open_settings)
        self.welcome.review_marked_clicked.connect(self._open_review_selector)
        self.welcome.search_clicked.connect(self._open_search)
        self.stack.addWidget(self.welcome)

    def _open_settings(self) -> None:
        dialog = SettingsDialog(self.settings, self)
        if dialog.exec():
            self.settings = dialog.build_settings()

    def _open_review_selector(self) -> None:
        dialog = ReviewLangDialog(self)
        if not dialog.exec() or not dialog.selected_lang:
            return
        self._start_important_review(dialog.selected_lang)

    def _open_search(self) -> None:
        dialog = SearchDialog(self)
        dialog.exec()

    def _start_normal_study(self, lang: str) -> None:
        all_words = load_word_list(lang)
        past = self.user_words.get_past(lang)
        words = [w for w in all_words if w.key not in past]
        if not words:
            QMessageBox.information(self, "提示", "该词库没有未学习单词了。")
            return
        self._open_study_page(words, lang)

    def _start_important_review(self, lang: str) -> None:
        all_words = load_word_list(lang)
        important = self.user_words.get_important(lang)
        words = [w for w in all_words if w.key in important]
        if not words:
            QMessageBox.information(self, "提示", "还没有标记单词，请先在学习页点击“保存该单词”。")
            return
        self._open_study_page(words, lang)

    def _open_study_page(self, words: list[WordEntry], lang: str) -> None:
        page = StudyPage(
            words=words,
            lang=lang,
            settings=self.settings,
            mark_past=lambda key: self.user_words.mark_past(lang, key),
            mark_important=lambda key: self.user_words.mark_important(lang, key),
        )
        page.back_home_clicked.connect(self._go_home)

        if self.stack.count() > 1:
            old = self.stack.widget(1)
            self.stack.removeWidget(old)
            if old is not None:
                old.deleteLater()
        self.stack.addWidget(page)
        self.stack.setCurrentWidget(page)

    def _go_home(self) -> None:
        self.stack.setCurrentWidget(self.welcome)
