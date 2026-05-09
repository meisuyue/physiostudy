from __future__ import annotations

import time

from PyQt6.QtCore import QDate, QTimer
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QFrame,
    QFormLayout,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QSpinBox,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from .app_config import StudySettings
from .dialogs.help_dialog import HelpCenterDialog
from .dialogs.search_dialog import SearchDialog
from .pages.learn_hub_page import LearnHubPage
from .pages.paper_loading_page import PaperLoadingPage
from .pages.paper_select_page import PaperSelectPage
from .pages.paper_test_page import PaperTestPage
from .pages.study_page import StudyPage
from .pages.welcome_page import WelcomePage
from .project_paths import DATA_DIR
from .storage import (
    PaperQuestion,
    UserWordStore,
    WordEntry,
    extract_default_papers_archive,
    has_default_papers_archive,
    list_papers,
    load_random_quote,
    load_roots_affixes,
    load_paper_questions,
    load_random_questions_from_all_papers,
    load_word_list,
    remove_default_papers_archive,
)
from .tts_service import TTS_ACCENTS, PaperTtsManager, clear_temp_tts_dir, ensure_temp_tts_dir


ICON_PATH = DATA_DIR / "icons" / "default" / "logo.png"
CONTACT_ICON_PATH = DATA_DIR / "icons" / "default" / "contact.png"


class SettingsDialog(QDialog):
    def __init__(self, settings: StudySettings, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("学习设置")
        self.setModal(True)
        self.resize(420, 260)

        self.rb_dictation = QRadioButton("默写模式")
        self.rb_browse = QRadioButton("浏览模式")
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
        self.setWindowTitle("选择复习词库")
        self.setModal(True)
        self.selected_lang: str | None = None
        self.resize(320, 140)

        tip = QLabel("请选择要复习的词库")
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


class WordDirectionDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("选择学习方向")
        self.setModal(True)
        self.selected_lang: str | None = None
        self.resize(360, 150)

        tip = QLabel("请选择这次单词学习的方向")
        btn_c = QPushButton("中文学英文")
        btn_e = QPushButton("英文学中文")
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


class WordCenterDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("选择单词入口")
        self.setModal(True)
        self.selected_mode: str | None = None
        self.selected_lang: str | None = None
        self.resize(460, 220)

        tip = QLabel("请选择这次要进入的单词模块")
        tip.setStyleSheet("font-size:16px; font-weight:700; color:#3650b7;")

        btn_study_c = QPushButton("中文学习")
        btn_study_e = QPushButton("英文学习")
        btn_review_c = QPushButton("中文复习")
        btn_review_e = QPushButton("英文复习")

        btn_study_c.clicked.connect(lambda: self._choose("study", "c"))
        btn_study_e.clicked.connect(lambda: self._choose("study", "e"))
        btn_review_c.clicked.connect(lambda: self._choose("review", "c"))
        btn_review_e.clicked.connect(lambda: self._choose("review", "e"))

        row1 = QHBoxLayout()
        row1.addWidget(btn_study_c)
        row1.addWidget(btn_study_e)

        row2 = QHBoxLayout()
        row2.addWidget(btn_review_c)
        row2.addWidget(btn_review_e)

        layout = QVBoxLayout(self)
        layout.addWidget(tip)
        layout.addSpacing(8)
        layout.addLayout(row1)
        layout.addLayout(row2)

    def _choose(self, mode: str, lang: str) -> None:
        self.selected_mode = mode
        self.selected_lang = lang
        self.accept()


class TtsAccentDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("选择试题朗读设置")
        self.setModal(True)
        self.resize(460, 230)
        self.selected_label: str | None = None
        self.selected_voice: str | None = None
        self.selected_rate: str | None = None

        tip = QLabel("请选择试题朗读口音与语速")
        tip.setStyleSheet("color:#4a5f72;")

        self.combo = QComboBox()
        self.combo.addItems(TTS_ACCENTS.keys())

        self.rate_spin = QSpinBox()
        self.rate_spin.setRange(-80, 80)
        self.rate_spin.setSingleStep(5)
        self.rate_spin.setValue(0)
        self.rate_spin.setSuffix(" %")

        rate_hint = QLabel("负值更慢，正值更快。推荐范围：-30% 到 +20%")
        rate_hint.setStyleSheet("color:#6e7c95; font-size:12px;")

        btn_ok = QPushButton("开始生成语音")
        btn_cancel = QPushButton("取消")
        btn_ok.clicked.connect(self._accept_selection)
        btn_cancel.clicked.connect(self.reject)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_row.addWidget(btn_ok)
        btn_row.addWidget(btn_cancel)

        layout = QVBoxLayout(self)
        layout.addWidget(tip)
        layout.addWidget(QLabel("口音"))
        layout.addWidget(self.combo)
        layout.addWidget(QLabel("语速"))
        layout.addWidget(self.rate_spin)
        layout.addWidget(rate_hint)
        layout.addStretch()
        layout.addLayout(btn_row)

    def _accept_selection(self) -> None:
        self.selected_label = self.combo.currentText()
        self.selected_voice = TTS_ACCENTS.get(self.selected_label or "")
        if not self.selected_voice:
            QMessageBox.warning(self, "提示", "当前口音无效，请重新选择。")
            return
        self.selected_rate = f"{self.rate_spin.value():+d}%"
        self.accept()


class MainWindow(QMainWindow):
    def __init__(self, username: str) -> None:
        super().__init__()
        self.username = username
        self.settings = StudySettings()
        self.user_words = UserWordStore(username)
        self.user_words.ensure_user_dirs()
        ensure_temp_tts_dir()
        self.current_tts_manager: PaperTtsManager | None = None
        self._usage_last_flush = time.monotonic()
        self._usage_timer = QTimer(self)
        self._usage_timer.timeout.connect(self._flush_usage_time)
        self._usage_timer.start(10000)

        self.setWindowTitle("PhysioStudy")
        self.resize(1100, 780)
        if ICON_PATH.exists():
            self.setWindowIcon(QIcon(str(ICON_PATH)))

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        self.welcome = WelcomePage(username=username, quote_text=load_random_quote())
        self.welcome.home_clicked.connect(self._go_home)
        self.welcome.start_learning_clicked.connect(self._open_learn_hub)
        self.welcome.settings_clicked.connect(self._open_settings)
        self.welcome.help_clicked.connect(self._open_help)
        self.welcome.contact_clicked.connect(self._open_contact)
        self.welcome.exit_clicked.connect(self.close)
        self.stack.addWidget(self.welcome)

    def _open_learn_hub(self) -> None:
        page = LearnHubPage(
            username=self.username,
            usage_seconds_provider=self._get_today_usage_seconds,
            progress_items=self._build_progress_items(),
        )
        page.home_clicked.connect(self._go_home)
        page.settings_clicked.connect(self._open_settings)
        page.help_clicked.connect(self._open_help)
        page.contact_clicked.connect(self._open_contact)
        page.word_study_clicked.connect(self._open_word_center_dialog)
        page.roots_affixes_clicked.connect(self._start_roots_affixes_study)
        page.review_marked_clicked.connect(self._open_word_center_dialog)
        page.search_clicked.connect(self._open_search)
        page.paper_test_clicked.connect(self._open_paper_selector)
        self._set_content_page(page)

    def _open_settings(self) -> None:
        dialog = SettingsDialog(self.settings, self)
        if dialog.exec():
            self.settings = dialog.build_settings()

    def _open_help(self) -> None:
        dialog = HelpCenterDialog(self)
        dialog.exec()

    def _open_contact(self) -> None:
        dialog = QMessageBox(self)
        dialog.setWindowTitle("联系作者")
        dialog.setText("\n\n@author: 安医21本硕陈腾飞\nemail: tengfchen@163.com")
        if CONTACT_ICON_PATH.exists():
            dialog.setIconPixmap(QIcon(str(CONTACT_ICON_PATH)).pixmap(96, 96))
        else:
            dialog.setIcon(QMessageBox.Icon.Information)
        dialog.exec()

    def _open_review_selector(self) -> None:
        dialog = ReviewLangDialog(self)
        if not dialog.exec() or not dialog.selected_lang:
            return
        self._start_important_review(dialog.selected_lang)

    def _open_search(self) -> None:
        dialog = SearchDialog(self)
        dialog.exec()

    def _open_word_study_selector(self) -> None:
        dialog = WordDirectionDialog(self)
        if not dialog.exec() or not dialog.selected_lang:
            return
        self._start_normal_study(dialog.selected_lang)

    def _open_word_center_dialog(self) -> None:
        dialog = WordCenterDialog(self)
        if not dialog.exec() or not dialog.selected_lang or not dialog.selected_mode:
            return
        if dialog.selected_mode == "review":
            self._start_important_review(dialog.selected_lang)
            return
        self._start_normal_study(dialog.selected_lang)

    def _start_normal_study(self, lang: str) -> None:
        self._clear_paper_tts_manager()
        all_words = load_word_list(lang)
        past = self.user_words.get_past(lang)
        words = [w for w in all_words if w.key not in past]
        if not words:
            QMessageBox.information(self, "提示", "该词库没有未学习的单词了。")
            return
        self._open_study_page(words, lang)

    def _start_roots_affixes_study(self) -> None:
        self._clear_paper_tts_manager()
        all_words = load_roots_affixes()
        past = self.user_words.get_past("r")
        words = [w for w in all_words if w.key not in past]
        if not words:
            QMessageBox.information(self, "提示", "词根词缀词库没有未学习的内容了。")
            return
        self._open_study_page(words, "r")

    def _start_important_review(self, lang: str) -> None:
        self._clear_paper_tts_manager()
        all_words = load_word_list(lang)
        important = self.user_words.get_important(lang)
        words = [w for w in all_words if w.key in important]
        if not words:
            QMessageBox.information(self, "提示", "还没有标记单词，请先在学习页保存单词。")
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
        self._set_content_page(page)

    def _open_paper_selector(self) -> None:
        self._clear_paper_tts_manager()
        papers = list_papers()
        if has_default_papers_archive():
            if not self._unlock_default_papers_archive():
                return
            papers = list_papers()
        page = PaperSelectPage(papers)
        page.back_home_clicked.connect(self._go_home)
        page.start_paper_clicked.connect(self._start_paper_test)
        self._set_content_page(page)

    def _unlock_default_papers_archive(self) -> bool:
        prompt_title = "默认试卷密码"
        password, ok = QInputDialog.getText(
            self,
            prompt_title,
            "检测到默认试卷压缩包，请输入密码后解锁试卷：",
            QLineEdit.EchoMode.Password,
        )
        if not ok:
            return False
        if extract_default_papers_archive(password):
            remove_default_papers_archive()
            QMessageBox.information(self, "提示", "默认试卷已成功解压。")
            return True

        QMessageBox.warning(
            self,
            "密码错误",
            "密码错误。请再输入一次；如果再次错误，将删除默认试卷压缩包。",
        )
        password2, ok2 = QInputDialog.getText(
            self,
            prompt_title,
            "第二次输入密码：如果再次错误，将删除默认试卷压缩包。",
            QLineEdit.EchoMode.Password,
        )
        if not ok2:
            return False
        if extract_default_papers_archive(password2):
            remove_default_papers_archive()
            QMessageBox.information(self, "提示", "默认试卷已成功解压。")
            return True

        remove_default_papers_archive()
        QMessageBox.critical(
            self,
            "默认试卷已删除",
            "第二次密码仍然错误，默认试卷压缩包已被删除。",
        )
        return False

    def _start_paper_test(self, filename: str) -> None:
        if filename == PaperSelectPage.RANDOM_ALL_PAPERS_KEY:
            paper, questions = load_random_questions_from_all_papers(sample_size=100)
        else:
            paper, questions = load_paper_questions(filename)
        if paper is None or not questions:
            QMessageBox.warning(self, "提示", "试卷读取失败，或当前试卷没有可用题目。")
            return

        accent_dialog = TtsAccentDialog(self)
        if not accent_dialog.exec() or not accent_dialog.selected_voice:
            return

        self._clear_paper_tts_manager()
        manager = PaperTtsManager(
            paper=paper,
            questions=questions,
            edge_voice=accent_dialog.selected_voice,
            edge_rate=accent_dialog.selected_rate or "-0%",
            preload_count=0,
            parent=self,
        )
        self.current_tts_manager = manager

        loading_page = PaperLoadingPage(paper_name=paper.name)
        loading_page.back_home_clicked.connect(self._go_home)
        loading_page.buffer_finished.connect(
            lambda: self._finish_loading_buffer(paper.name, questions, manager, loading_page)
        )
        self._set_content_page(loading_page)
        manager.start()

    def _finish_loading_buffer(
        self,
        paper_name: str,
        questions: list[PaperQuestion],
        manager: PaperTtsManager,
        loading_page: PaperLoadingPage,
    ) -> None:
        if manager is not self.current_tts_manager:
            return
        if self.stack.currentWidget() is not loading_page:
            return
        self._open_paper_test_page(paper_name, questions, manager)

    def _open_paper_test_page(
        self,
        paper_name: str,
        questions: list[PaperQuestion],
        manager: PaperTtsManager,
    ) -> None:
        if manager is not self.current_tts_manager:
            return

        page = PaperTestPage(paper_name=paper_name, questions=questions, tts_manager=manager)
        page.back_home_clicked.connect(self._go_home)
        page.choose_other_paper_clicked.connect(self._open_paper_selector)
        self._set_content_page(page)

    def _set_content_page(self, page: QWidget) -> None:
        while self.stack.count() > 1:
            old = self.stack.widget(1)
            if old is not None and hasattr(old, "cleanup"):
                old.cleanup()
            self.stack.removeWidget(old)
            if old is not None:
                old.deleteLater()
        self.stack.addWidget(page)
        self.stack.setCurrentWidget(page)

    def _go_home(self) -> None:
        self._flush_usage_time()
        self._clear_paper_tts_manager()
        while self.stack.count() > 1:
            old = self.stack.widget(1)
            if old is not None and hasattr(old, "cleanup"):
                old.cleanup()
            self.stack.removeWidget(old)
            if old is not None:
                old.deleteLater()
        self.stack.setCurrentWidget(self.welcome)

    def _clear_paper_tts_manager(self) -> None:
        if self.current_tts_manager is not None:
            self.current_tts_manager.shutdown()
            self.current_tts_manager = None
        clear_temp_tts_dir()

    def _today_key(self) -> str:
        return QDate.currentDate().toString("yyyy-MM-dd")

    def _flush_usage_time(self) -> None:
        now = time.monotonic()
        elapsed = int(now - self._usage_last_flush)
        if elapsed > 0:
            self.user_words.add_daily_app_seconds(self._today_key(), elapsed)
            self._usage_last_flush = now

    def _get_today_usage_seconds(self) -> int:
        stored = self.user_words.get_daily_app_seconds(self._today_key())
        pending = max(0, int(time.monotonic() - self._usage_last_flush))
        return stored + pending

    def _build_progress_items(self) -> list[dict[str, object]]:
        items: list[dict[str, object]] = []
        for label, lang, loader in (
            ("英文形式学习", "e", load_word_list),
            ("中文形式学习", "c", load_word_list),
            ("词根词缀学习", "r", None),
        ):
            words = load_roots_affixes() if lang == "r" else loader(lang)  # type: ignore[misc]
            learned = self.user_words.get_past(lang)
            completed = sum(1 for word in words if word.key in learned)
            total = len(words)
            percent = int((completed / total) * 100) if total else 0
            items.append(
                {
                    "label": label,
                    "lang": lang,
                    "completed": completed,
                    "total": total,
                    "percent": percent,
                }
            )
        return items

    def closeEvent(self, event) -> None:  # type: ignore[override]
        self._flush_usage_time()
        self._clear_paper_tts_manager()
        super().closeEvent(event)

