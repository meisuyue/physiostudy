from __future__ import annotations

import json
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path
from typing import Dict, List, Set, Tuple

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DICT_DIR = DATA_DIR / "dict"
USER_FILE = DATA_DIR / "users.json"
USER_DATA_DIR = DATA_DIR / "user"


def _ensure_root_dirs() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    USER_DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not USER_FILE.exists():
        USER_FILE.write_text("{}", encoding="utf-8")


@dataclass
class User:
    username: str
    password: str


class UserStore:
    def __init__(self) -> None:
        _ensure_root_dirs()
        self._users: Dict[str, User] = {}
        self._load()

    def _load(self) -> None:
        try:
            data = json.loads(USER_FILE.read_text(encoding="utf-8"))
        except Exception:
            data = {}
        for name, pwd in data.items():
            self._users[name] = User(username=name, password=pwd)

    def _save(self) -> None:
        data = {u.username: u.password for u in self._users.values()}
        USER_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def register(self, username: str, password: str) -> bool:
        if not username or not password:
            return False
        if username in self._users:
            return False
        self._users[username] = User(username=username, password=password)
        self._save()
        UserWordStore(username).ensure_user_dirs()
        return True

    def authenticate(self, username: str, password: str) -> bool:
        user = self._users.get(username)
        if not user:
            return False
        ok = user.password == password
        if ok:
            UserWordStore(username).ensure_user_dirs()
        return ok


@dataclass
class WordEntry:
    key: str
    meaning: str
    abbrev: str
    page: str


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
    """
    在 c_key.json 和 e_key.json 的 key 中进行模糊匹配。
    返回 [(lang, key, meaning, score), ...]，按 score 降序。
    """
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


class UserWordStore:
    def __init__(self, username: str) -> None:
        self.username = username
        self.base = USER_DATA_DIR / username

    def ensure_user_dirs(self) -> None:
        for lang_folder in ("c_key", "e_key"):
            for group in ("past", "important"):
                folder = self.base / lang_folder / group
                folder.mkdir(parents=True, exist_ok=True)
                data_file = folder / "words.json"
                if not data_file.exists():
                    data_file.write_text("[]", encoding="utf-8")

    def _folder(self, lang: str, group: str) -> Path:
        lang_folder = "c_key" if lang == "c" else "e_key"
        return self.base / lang_folder / group

    def _file(self, lang: str, group: str) -> Path:
        self.ensure_user_dirs()
        return self._folder(lang, group) / "words.json"

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
