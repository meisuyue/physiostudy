from __future__ import annotations

from dataclasses import dataclass


@dataclass
class StudySettings:
    mode: str = "dictation"  # dictation | browse
    auto_show_delay_sec: int = 3
    auto_next_delay_sec: int = 3

