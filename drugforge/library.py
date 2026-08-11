import json
from pathlib import Path
from drugforge.config import DATA_DIR

_ETHNO_PATH = DATA_DIR / "ethnobotanical.json"
_compounds: list[dict] = []


def _load():
    global _compounds
    if _compounds:
        return
    if _ETHNO_PATH.exists():
        with open(_ETHNO_PATH, "r", encoding="utf-8") as f:
            _compounds = json.load(f)


def get_compounds() -> list[dict]:
    _load()
    return _compounds


def get_compound(compound_id: str) -> dict | None:
    _load()
    for c in _compounds:
        if c["id"] == compound_id:
            return c
    return None
