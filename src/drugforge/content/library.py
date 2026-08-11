"""Ethnobotanical compound registry.

Each entry links a traditional preparation to a specific molecule and cites its
source, so a screening result can always be traced back to the knowledge that
motivated it.
"""

from __future__ import annotations

import json
import logging
from functools import lru_cache
from typing import Optional

from drugforge.config import ETHNOBOTANICAL_PATH

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _entries() -> tuple[dict, ...]:
    if not ETHNOBOTANICAL_PATH.exists():
        logger.warning("Missing registry file %s", ETHNOBOTANICAL_PATH)
        return ()
    try:
        return tuple(json.loads(ETHNOBOTANICAL_PATH.read_text(encoding="utf-8")))
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("Could not read %s: %s", ETHNOBOTANICAL_PATH.name, exc)
        return ()


def list_compounds() -> list[dict]:
    return [dict(entry) for entry in _entries()]


def get_compound(compound_id: str) -> Optional[dict]:
    for entry in _entries():
        if entry.get("id") == compound_id:
            return dict(entry)
    return None
