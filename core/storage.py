from __future__ import annotations

import hashlib
import json
import random
import sqlite3
import zipfile
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path
from typing import Dict, List, Set, Tuple

from .project_paths import DATA_DIR

DICT_DIR = DATA_DIR / "dict"
ROOT_AFFIX_FILE = DICT_DIR / "roots_affixes.json"
PAPER_DIR = DATA_DIR / "papers"
DEFAULT_PAPERS_ARCHIVE = PAPER_DIR / "ahmu_default_papers.zip"
QUOTE_DIR = DATA_DIR / "quote"
QUOTE_FILE = QUOTE_DIR / "medical_quotes.json"
USER_FILE = DATA_DIR / "users.json"
USER_DATA_DIR = DATA_DIR / "user"
LOGIN_MEMORY_FILE = DATA_DIR / "login_memory.json"
AUTH_DB_FILE = DATA_DIR / "auth.sqlite3"
USAGE_FILE_NAME = "usage_stats.json"


def _ensure_root_dirs() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    USER_DATA_DIR.mkdir(parents=True, exist_ok=True)
    PAPER_DIR.mkdir(parents=True, exist_ok=True)
    QUOTE_DIR.mkdir(parents=True, exist_ok=True)
    if not QUOTE_FILE.exists():
        QUOTE_FILE.write_text(
            json.dumps(
                [
                    "The good physician treats the disease; the great physician treats the patient who has the disease. - William Osler",
                    "Wherever the art of medicine is loved, there is also a love of humanity. - Hippocrates",
                    "Medicine is a science of uncertainty and an art of probability. - William Osler",
                    "The art of medicine consists of amusing the patient while nature cures the disease. - Voltaire",
                    "Let food be thy medicine and medicine be thy food. - Hippocrates",
                    "Cure sometimes, treat often, comfort always. - Edward Livingston Trudeau",
                ],
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
    _ensure_auth_db()


def _connect_auth_db() -> sqlite3.Connection:
    conn = sqlite3.connect(AUTH_DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def _ensure_auth_db() -> None:
    with _connect_auth_db() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                password_hash TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS login_memory (
                slot INTEGER PRIMARY KEY CHECK (slot = 1),
                remember INTEGER NOT NULL DEFAULT 0,
                username TEXT NOT NULL DEFAULT '',
                password TEXT NOT NULL DEFAULT ''
            )
            """
        )
        conn.execute(
            """
            INSERT OR IGNORE INTO login_memory(slot, remember, username, password)
            VALUES (1, 0, '', '')
            """
        )
        _migrate_auth_json_to_sqlite(conn)


def _migrate_auth_json_to_sqlite(conn: sqlite3.Connection) -> None:
    user_count = int(conn.execute("SELECT COUNT(*) FROM users").fetchone()[0])
    if user_count == 0 and USER_FILE.exists():
        try:
            raw_users = json.loads(USER_FILE.read_text(encoding="utf-8"))
        except Exception:
            raw_users = {}
        if isinstance(raw_users, dict):
            for username, password in raw_users.items():
                username_text = str(username).strip()
                password_text = str(password)
                if not username_text or not password_text:
                    continue
                conn.execute(
                    "INSERT OR IGNORE INTO users(username, password_hash) VALUES (?, ?)",
                    (username_text, _hash_password(password_text)),
                )

    memory_row = conn.execute(
        "SELECT remember, username, password FROM login_memory WHERE slot = 1"
    ).fetchone()
    remember = int(memory_row["remember"]) if memory_row else 0
    username = str(memory_row["username"]) if memory_row else ""
    password = str(memory_row["password"]) if memory_row else ""
    if remember == 0 and not username and not password and LOGIN_MEMORY_FILE.exists():
        try:
            raw_memory = json.loads(LOGIN_MEMORY_FILE.read_text(encoding="utf-8"))
        except Exception:
            raw_memory = {}
        conn.execute(
            """
            UPDATE login_memory
            SET remember = ?, username = ?, password = ?
            WHERE slot = 1
            """,
            (
                1 if bool(raw_memory.get("remember", False)) else 0,
                str(raw_memory.get("username", "")),
                str(raw_memory.get("password", "")),
            ),
        )


@dataclass
class User:
    username: str
    password_hash: str


class UserStore:
    def __init__(self) -> None:
        _ensure_root_dirs()

    def register(self, username: str, password: str) -> bool:
        if not username or not password:
            return False
        try:
            with _connect_auth_db() as conn:
                conn.execute(
                    "INSERT INTO users(username, password_hash) VALUES (?, ?)",
                    (username, _hash_password(password)),
                )
        except sqlite3.IntegrityError:
            return False
        UserWordStore(username).ensure_user_dirs()
        return True

    def authenticate(self, username: str, password: str) -> bool:
        with _connect_auth_db() as conn:
            row = conn.execute(
                "SELECT username FROM users WHERE username = ? AND password_hash = ?",
                (username, _hash_password(password)),
            ).fetchone()
        ok = row is not None
        if ok:
            UserWordStore(username).ensure_user_dirs()
        return ok


def load_login_memory() -> tuple[bool, str, str]:
    _ensure_root_dirs()
    with _connect_auth_db() as conn:
        row = conn.execute(
            "SELECT remember, username, password FROM login_memory WHERE slot = 1"
        ).fetchone()
    remember = bool(row["remember"]) if row else False
    username = str(row["username"]) if row else ""
    password = str(row["password"]) if row else ""
    if not remember:
        return False, "", ""
    return True, username, password


def save_login_memory(remember: bool, username: str = "", password: str = "") -> None:
    _ensure_root_dirs()
    with _connect_auth_db() as conn:
        conn.execute(
            """
            UPDATE login_memory
            SET remember = ?, username = ?, password = ?
            WHERE slot = 1
            """,
            (
                1 if remember else 0,
                username if remember else "",
                password if remember else "",
            ),
        )


def load_random_quote() -> str:
    _ensure_root_dirs()
    try:
        raw = json.loads(QUOTE_FILE.read_text(encoding="utf-8-sig"))
    except Exception:
        raw = []
    quotes = [str(item).strip() for item in raw if str(item).strip()]
    if not quotes:
        return "Wherever the art of medicine is loved, there is also a love of humanity. - Hippocrates"
    return random.choice(quotes)


@dataclass
class WordEntry:
    key: str
    meaning: str
    abbrev: str
    page: str


@dataclass
class PaperInfo:
    filename: str
    name: str
    title: str
    question_count: int


@dataclass
class PaperQuestion:
    id: int
    question_en: str
    answer_en: str
    analysis_zh: str


def load_word_list(lang: str) -> List[WordEntry]:
    file_map = {
        "c": DICT_DIR / "c_key.json",
        "e": DICT_DIR / "e_key.json",
    }
    path = file_map.get(lang)
    if not path or not path.exists():
        return []
    with path.open("r", encoding="utf-8") as f:
        raw = json.load(f)
    entries: List[WordEntry] = []
    for k, v in raw.items():
        entries.append(
            WordEntry(
                key=str(k),
                meaning=str(v.get("meaning", "")),
                abbrev=str(v.get("abbrev", "")),
                page=str(v.get("page", "")),
            )
        )
    return entries


def load_roots_affixes() -> List[WordEntry]:
    if not ROOT_AFFIX_FILE.exists():
        return []
    try:
        raw = json.loads(ROOT_AFFIX_FILE.read_text(encoding="utf-8-sig"))
    except Exception:
        try:
            raw = json.loads(ROOT_AFFIX_FILE.read_text(encoding="utf-8"))
        except Exception:
            return []

    entries: List[WordEntry] = []
    for key, value in raw.items():
        if not isinstance(value, dict):
            continue
        meaning = str(value.get("meaning", "")).strip()
        example = value.get("example", {})
        example_word = ""
        example_translation = ""
        if isinstance(example, dict):
            example_word = str(example.get("word", "")).strip()
            example_translation = str(example.get("translation", "")).strip()

        parts = [meaning] if meaning else []
        if example_word:
            parts.append(f"Example: {example_word}")
        if example_translation:
            parts.append(f"释义: {example_translation}")

        entries.append(
            WordEntry(
                key=str(key).strip(),
                meaning="\n".join(parts).strip(),
                abbrev="",
                page="",
            )
        )
    return entries


def _load_raw_dict(lang: str) -> Dict[str, Dict[str, str]]:
    file_map = {
        "c": DICT_DIR / "c_key.json",
        "e": DICT_DIR / "e_key.json",
    }
    path = file_map.get(lang)
    if not path or not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def search_word_meanings(query: str, threshold: float = 0.6) -> List[Tuple[str, str, str, float]]:
    q = (query or "").strip()
    if not q:
        return []
    q_lower = q.lower()
    results: List[Tuple[str, str, str, float]] = []
    for lang in ("c", "e"):
        raw = _load_raw_dict(lang)
        for key, value in raw.items():
            key_str = str(key)
            key_lower = key_str.lower()
            score = SequenceMatcher(None, q_lower, key_lower).ratio()
            if q_lower in key_lower:
                score = max(score, 1.0)
            if score >= threshold:
                meaning = str(value.get("meaning", ""))
                results.append((lang, key_str, meaning, score))
    results.sort(key=lambda x: x[3], reverse=True)
    return results


def list_papers() -> List[PaperInfo]:
    _ensure_root_dirs()
    papers: List[PaperInfo] = []
    for path in sorted(PAPER_DIR.glob("*.json")):
        if path.stem.startswith("temp_paper_source"):
            continue
        try:
            raw = json.loads(path.read_text(encoding="utf-8-sig"))
        except Exception:
            continue
        questions = raw.get("questions", [])
        papers.append(
            PaperInfo(
                filename=path.name,
                name=path.stem,
                title=str(raw.get("title", path.stem)),
                question_count=len(questions) if isinstance(questions, list) else 0,
            )
        )
    return papers


def has_default_papers_archive() -> bool:
    _ensure_root_dirs()
    return DEFAULT_PAPERS_ARCHIVE.exists()


def remove_default_papers_archive() -> None:
    try:
        DEFAULT_PAPERS_ARCHIVE.unlink(missing_ok=True)
    except Exception:
        pass


def extract_default_papers_archive(password: str) -> bool:
    _ensure_root_dirs()
    if not DEFAULT_PAPERS_ARCHIVE.exists():
        return False
    pwd = (password or "").encode("utf-8")
    try:
        with zipfile.ZipFile(DEFAULT_PAPERS_ARCHIVE, "r") as zf:
            members = [name for name in zf.namelist() if name.lower().endswith(".json")]
            if not members:
                return False
            # Validate password before extraction.
            zf.read(members[0], pwd=pwd)
            for member in members:
                target_path = PAPER_DIR / Path(member).name
                with zf.open(member, pwd=pwd) as src, target_path.open("wb") as dst:
                    dst.write(src.read())
        return True
    except Exception:
        return False


def load_paper_questions(filename: str) -> Tuple[PaperInfo | None, List[PaperQuestion]]:
    _ensure_root_dirs()
    path = PAPER_DIR / filename
    if path.suffix.lower() != ".json" or not path.exists():
        return None, []

    try:
        raw = json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return None, []

    raw_questions = raw.get("questions", [])
    if not isinstance(raw_questions, list):
        raw_questions = []

    paper = PaperInfo(
        filename=path.name,
        name=path.stem,
        title=str(raw.get("title", path.stem)),
        question_count=len(raw_questions),
    )
    questions: List[PaperQuestion] = []
    for index, item in enumerate(raw_questions, start=1):
        if not isinstance(item, dict):
            continue
        questions.append(
            PaperQuestion(
                id=int(item.get("id", index)),
                question_en=str(item.get("question_en", "")).strip(),
                answer_en=str(item.get("answer_en", "")).strip(),
                analysis_zh=str(item.get("analysis_zh", "无")).strip() or "无",
            )
        )
    return paper, questions


def load_random_questions_from_all_papers(sample_size: int = 100) -> Tuple[PaperInfo | None, List[PaperQuestion]]:
    all_questions: List[PaperQuestion] = []
    for paper in list_papers():
        _, questions = load_paper_questions(paper.filename)
        all_questions.extend(questions)

    if not all_questions:
        return None, []

    selected_count = min(sample_size, len(all_questions))
    sampled_questions = random.sample(all_questions, selected_count)
    questions = [
        PaperQuestion(
            id=index,
            question_en=item.question_en,
            answer_en=item.answer_en,
            analysis_zh=item.analysis_zh,
        )
        for index, item in enumerate(sampled_questions, start=1)
    ]
    paper = PaperInfo(
        filename="__random_all_papers__.json",
        name="所有试题随机抽取",
        title="所有试题随机抽取",
        question_count=len(questions),
    )
    return paper, questions


class UserWordStore:
    def __init__(self, username: str) -> None:
        self.username = username
        self.base = USER_DATA_DIR / username

    def ensure_user_dirs(self) -> None:
        for lang_folder in ("c_key", "e_key", "roots_affixes"):
            for group in ("past", "important"):
                folder = self.base / lang_folder / group
                folder.mkdir(parents=True, exist_ok=True)
                data_file = folder / "words.json"
                if not data_file.exists():
                    data_file.write_text("[]", encoding="utf-8")

    def _folder(self, lang: str, group: str) -> Path:
        lang_folder_map = {
            "c": "c_key",
            "e": "e_key",
            "r": "roots_affixes",
        }
        lang_folder = lang_folder_map.get(lang, "e_key")
        return self.base / lang_folder / group

    def _file(self, lang: str, group: str) -> Path:
        self.ensure_user_dirs()
        return self._folder(lang, group) / "words.json"

    def _usage_file(self) -> Path:
        self.ensure_user_dirs()
        path = self.base / USAGE_FILE_NAME
        if not path.exists():
            path.write_text("{}", encoding="utf-8")
        return path

    def _read_usage(self) -> Dict[str, int]:
        path = self._usage_file()
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            raw = {}
        usage: Dict[str, int] = {}
        for key, value in raw.items():
            try:
                usage[str(key)] = max(0, int(value))
            except Exception:
                continue
        return usage

    def _write_usage(self, usage: Dict[str, int]) -> None:
        self._usage_file().write_text(
            json.dumps(usage, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _read_set(self, lang: str, group: str) -> Set[str]:
        path = self._file(lang, group)
        try:
            arr = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            arr = []
        return {str(x) for x in arr}

    def _write_set(self, lang: str, group: str, values: Set[str]) -> None:
        path = self._file(lang, group)
        path.write_text(
            json.dumps(sorted(values), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def get_past(self, lang: str) -> Set[str]:
        return self._read_set(lang, "past")

    def get_important(self, lang: str) -> Set[str]:
        return self._read_set(lang, "important")

    def mark_past(self, lang: str, word_key: str) -> None:
        values = self._read_set(lang, "past")
        if word_key not in values:
            values.add(word_key)
            self._write_set(lang, "past", values)

    def mark_important(self, lang: str, word_key: str) -> bool:
        values = self._read_set(lang, "important")
        before = len(values)
        values.add(word_key)
        self._write_set(lang, "important", values)
        return len(values) > before

    def get_daily_app_seconds(self, date_key: str) -> int:
        return self._read_usage().get(date_key, 0)

    def add_daily_app_seconds(self, date_key: str, seconds: int) -> None:
        if seconds <= 0:
            return
        usage = self._read_usage()
        usage[date_key] = max(0, int(usage.get(date_key, 0))) + int(seconds)
        self._write_usage(usage)
