from __future__ import annotations

from pathlib import Path


CORE_DIR = Path(__file__).resolve().parent
ROOT_DIR = CORE_DIR.parent
DATA_DIR = ROOT_DIR / "data"
TEMP_DIR = ROOT_DIR / "temp"
