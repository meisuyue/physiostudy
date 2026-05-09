from __future__ import annotations

import asyncio
import hashlib
import threading
from concurrent.futures import Future, ThreadPoolExecutor
from pathlib import Path
from typing import Dict, List, Set

from PyQt6.QtCore import QObject, pyqtSignal

from .project_paths import TEMP_DIR
from .storage import PaperInfo, PaperQuestion

TEMP_TTS_DIR = TEMP_DIR / "tts"
DEFAULT_EDGE_VOICE = "en-US-JennyNeural"
DEFAULT_EDGE_RATE = "-0%"
TTS_PREROLL_TEXT = "。 "
TTS_ACCENTS: Dict[str, str] = {
    '标准英国话': 'en-GB-LibbyNeural',
    '标准美国话（女）': 'en-US-JennyNeural',
    '标准美国话（男）': 'en-US-AndrewMultilingualNeural',
    '家乡话（中式英语口音）': 'zh-CN-XiaoxiaoNeural',
    '东南亚口音': 'en-SG-WayneNeural',
    '妹有口音': 'zh-CN-liaoning-XiaobeiNeural',
    '机车音': 'zh-TW-HsiaoChenNeural',
    '樱花口音': 'ja-JP-NanamiNeural',
    '舌头非常灵活口音': 'ru-RU-SvetlanaNeural'
}


def ensure_temp_tts_dir() -> Path:
    TEMP_TTS_DIR.mkdir(parents=True, exist_ok=True)
    return TEMP_TTS_DIR


def clear_temp_tts_dir() -> None:
    ensure_temp_tts_dir()
    for path in TEMP_TTS_DIR.iterdir():
        try:
            if path.is_dir():
                for child in sorted(path.rglob("*"), reverse=True):
                    if child.is_file():
                        child.unlink(missing_ok=True)
                    elif child.is_dir():
                        child.rmdir()
                path.rmdir()
            else:
                path.unlink(missing_ok=True)
        except Exception:
            continue


def _build_tts_text(source_text: str | None) -> str:
    core_text = (source_text or "").strip() or "No text."
    return f"{TTS_PREROLL_TEXT}{core_text}"


def _sanitize_prefix(text: str, limit: int) -> str:
    safe = "".join(ch.lower() if ch.isalnum() else "_" for ch in text)[:limit].strip("_")
    return safe or "item"


def _normalize_edge_rate(rate: str | int | None) -> str:
    if isinstance(rate, int):
        return f"{rate:+d}%"
    normalized = str(rate or DEFAULT_EDGE_RATE).strip()
    if not normalized:
        return DEFAULT_EDGE_RATE
    if normalized.endswith("%"):
        if normalized.startswith(("+", "-")):
            return normalized
        try:
            value = int(normalized[:-1])
            return f"{value:+d}%"
        except Exception:
            return DEFAULT_EDGE_RATE
    try:
        value = int(normalized)
        return f"{value:+d}%"
    except Exception:
        return DEFAULT_EDGE_RATE


def _edge_rate_to_pyttsx3_rate(rate: str | int | None) -> int:
    normalized = _normalize_edge_rate(rate)
    try:
        percent = int(normalized.replace("%", ""))
    except Exception:
        percent = 0
    # Base 150, every 10% changes about 10 points.
    return max(80, min(240, 150 + percent))


def _build_tts_output_path(scope_prefix: str, voice: str, rate: str, text: str) -> Path:
    digest = hashlib.md5(text.encode("utf-8")).hexdigest()[:12]
    text_prefix = _sanitize_prefix(text, 36)
    scope_safe = _sanitize_prefix(scope_prefix, 24)
    voice_prefix = _sanitize_prefix(voice, 20)
    rate_prefix = _sanitize_prefix(rate.replace("%", "pct"), 12)
    return ensure_temp_tts_dir() / f"{scope_safe}_{voice_prefix}_{rate_prefix}_{text_prefix}_{digest}.mp3"


def _generate_with_edge_tts(text: str, output_path: Path, voice: str, rate: str) -> None:
    import edge_tts

    if output_path.exists():
        output_path.unlink()
    communicate = edge_tts.Communicate(
        text=text,
        voice=voice,
        rate=_normalize_edge_rate(rate),
    )
    asyncio.run(communicate.save(str(output_path)))


_PYTTSX3_LOCK = threading.Lock()


def _generate_with_pyttsx3(text: str, output_path: Path, rate: str | int | None = None) -> None:
    import pyttsx3

    with _PYTTSX3_LOCK:
        if output_path.exists():
            output_path.unlink()
        engine = pyttsx3.init()
        engine.setProperty("rate", _edge_rate_to_pyttsx3_rate(rate))
        engine.save_to_file(text, str(output_path))
        engine.runAndWait()
        engine.stop()


class TextTtsManager(QObject):
    audio_ready = pyqtSignal(str, str)
    audio_failed = pyqtSignal(str)

    _generation_completed = pyqtSignal(str, str)
    _generation_failed = pyqtSignal(str)

    def __init__(
        self,
        scope_prefix: str,
        edge_voice: str = DEFAULT_EDGE_VOICE,
        edge_rate: str = DEFAULT_EDGE_RATE,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self.scope_prefix = scope_prefix
        self.edge_voice = edge_voice
        self.edge_rate = _normalize_edge_rate(edge_rate)
        self._executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="text-tts")
        self._submitted: Set[str] = set()
        self._failed: Set[str] = set()
        self._audio_paths: Dict[str, Path] = {}
        self._shutdown = False

        self._generation_completed.connect(self._on_generation_completed)
        self._generation_failed.connect(self._on_generation_failed)

    def ensure_text(self, text: str) -> None:
        normalized = (text or "").strip()
        if self._shutdown or not normalized:
            return
        if normalized in self._submitted and normalized not in self._failed:
            return
        self._failed.discard(normalized)
        self._submitted.add(normalized)
        future = self._executor.submit(self._generate_audio_for_text, normalized)
        future.add_done_callback(lambda done, source=normalized: self._handle_future(source, done))

    def get_audio_path(self, text: str) -> Path | None:
        return self._audio_paths.get((text or "").strip())

    def shutdown(self) -> None:
        self._shutdown = True
        self._executor.shutdown(wait=False, cancel_futures=True)

    def _handle_future(self, source_text: str, future: Future[Path]) -> None:
        if self._shutdown:
            return
        try:
            path = future.result()
        except Exception:
            self._generation_failed.emit(source_text)
            return
        self._generation_completed.emit(source_text, str(path))

    def _on_generation_completed(self, source_text: str, path_str: str) -> None:
        if self._shutdown:
            return
        self._audio_paths[source_text] = Path(path_str)
        self.audio_ready.emit(source_text, path_str)

    def _on_generation_failed(self, source_text: str) -> None:
        if self._shutdown:
            return
        self._failed.add(source_text)
        self.audio_failed.emit(source_text)

    def _generate_audio_for_text(self, source_text: str) -> Path:
        ensure_temp_tts_dir()
        text = _build_tts_text(source_text)
        output_path = _build_tts_output_path(self.scope_prefix, self.edge_voice, self.edge_rate, text)
        if output_path.exists() and output_path.stat().st_size > 0:
            return output_path

        try:
            _generate_with_edge_tts(text, output_path, self.edge_voice, self.edge_rate)
        except Exception:
            _generate_with_pyttsx3(text, output_path, self.edge_rate)

        if not output_path.exists() or output_path.stat().st_size <= 0:
            raise RuntimeError(f"Failed to create TTS audio for text: {source_text}")
        return output_path


class PaperTtsManager(QObject):
    preload_progress = pyqtSignal(int, int)
    preload_finished = pyqtSignal()
    audio_ready = pyqtSignal(int, str)
    audio_failed = pyqtSignal(int)

    _generation_completed = pyqtSignal(int, str)
    _generation_failed = pyqtSignal(int)

    def __init__(
        self,
        paper: PaperInfo,
        questions: List[PaperQuestion],
        edge_voice: str = DEFAULT_EDGE_VOICE,
        edge_rate: str = DEFAULT_EDGE_RATE,
        preload_count: int = 10,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self.paper = paper
        self.questions = questions
        self.edge_voice = edge_voice
        self.edge_rate = _normalize_edge_rate(edge_rate)
        self.preload_target = min(preload_count, len(questions))
        self._executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="paper-tts")
        self._submitted: Set[int] = set()
        self._finished: Set[int] = set()
        self._failed: Set[int] = set()
        self._audio_paths: Dict[int, Path] = {}
        self._remaining_started = False
        self._preload_emitted = False
        self._shutdown = False

        self._generation_completed.connect(self._on_generation_completed)
        self._generation_failed.connect(self._on_generation_failed)

    def start(self) -> None:
        ensure_temp_tts_dir()
        if not self.questions:
            self.preload_progress.emit(0, 0)
            self.preload_finished.emit()
            return

        for index in range(self.preload_target):
            self.ensure_question(index)
        if self.preload_target == 0:
            self.preload_progress.emit(0, 0)
            self.preload_finished.emit()
            self._start_remaining_generation()

    def ensure_question(self, index: int) -> None:
        if self._shutdown or index < 0 or index >= len(self.questions):
            return
        if index in self._submitted and index not in self._failed:
            return
        self._failed.discard(index)
        self._submitted.add(index)
        future = self._executor.submit(self._generate_audio_for_index, index)
        future.add_done_callback(lambda done, idx=index: self._handle_future(idx, done))

    def get_audio_path(self, index: int) -> Path | None:
        return self._audio_paths.get(index)

    def shutdown(self) -> None:
        self._shutdown = True
        self._executor.shutdown(wait=False, cancel_futures=True)

    def _handle_future(self, index: int, future: Future[Path]) -> None:
        if self._shutdown:
            return
        try:
            path = future.result()
        except Exception:
            self._generation_failed.emit(index)
            return
        self._generation_completed.emit(index, str(path))

    def _on_generation_completed(self, index: int, path_str: str) -> None:
        if self._shutdown:
            return
        path = Path(path_str)
        self._audio_paths[index] = path
        self._finished.add(index)
        self.audio_ready.emit(index, str(path))
        self._update_preload_progress()

    def _on_generation_failed(self, index: int) -> None:
        if self._shutdown:
            return
        self._failed.add(index)
        self._finished.add(index)
        self.audio_failed.emit(index)
        self._update_preload_progress()

    def _update_preload_progress(self) -> None:
        preload_done = len([idx for idx in range(self.preload_target) if idx in self._finished])
        self.preload_progress.emit(preload_done, self.preload_target)
        if not self._preload_emitted and preload_done >= self.preload_target:
            self._preload_emitted = True
            self.preload_finished.emit()
            self._start_remaining_generation()

    def _start_remaining_generation(self) -> None:
        if self._remaining_started or self._shutdown:
            return
        self._remaining_started = True
        for index in range(self.preload_target, len(self.questions)):
            self.ensure_question(index)

    def _generate_audio_for_index(self, index: int) -> Path:
        ensure_temp_tts_dir()
        question = self.questions[index]
        text = _build_tts_text(question.question_en)
        output_path = self._build_output_path(index, text)
        if output_path.exists() and output_path.stat().st_size > 0:
            return output_path

        try:
            _generate_with_edge_tts(text, output_path, self.edge_voice, self.edge_rate)
        except Exception:
            _generate_with_pyttsx3(text, output_path, self.edge_rate)

        if not output_path.exists() or output_path.stat().st_size <= 0:
            raise RuntimeError(f"Failed to create TTS audio for question {index + 1}")
        return output_path

    def _build_output_path(self, index: int, text: str) -> Path:
        paper_prefix = _sanitize_prefix(self.paper.name, 24) or f"paper_{index + 1}"
        return _build_tts_output_path(paper_prefix, self.edge_voice, self.edge_rate, text)
