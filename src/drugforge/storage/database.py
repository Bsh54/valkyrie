"""SQLite connection handling and schema migrations."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager

from drugforge.config import DB_PATH

_SCHEMA = """
CREATE TABLE IF NOT EXISTS screening_results (
    id                 TEXT PRIMARY KEY,
    timestamp          TEXT NOT NULL,
    molecule_smiles    TEXT NOT NULL,
    target_id          TEXT NOT NULL,
    affinity           REAL NOT NULL,
    vinardo_score      REAL,
    consensus_score    REAL,
    pose_sdf           TEXT,
    pose_pdbqt         TEXT,
    drug_likeness_json TEXT,
    admet_json         TEXT,
    is_hit             INTEGER,
    hit_reasons_json   TEXT,
    comparison_json    TEXT,
    verdict            TEXT,
    boltz_json         TEXT,
    explanation_json   TEXT
)
"""

_INDEXES = (
    "CREATE INDEX IF NOT EXISTS idx_results_lookup "
    "ON screening_results (molecule_smiles, target_id, timestamp DESC)",
)

# Columns added after the first release. CREATE TABLE IF NOT EXISTS cannot alter
# an existing table, so missing columns are added explicitly.
_ADDED_COLUMNS = {
    "vinardo_score": "REAL",
    "consensus_score": "REAL",
    "admet_json": "TEXT",
    "is_hit": "INTEGER",
    "hit_reasons_json": "TEXT",
    "boltz_json": "TEXT",
    "explanation_json": "TEXT",
}

_LEGACY_TABLE = "docking_results"


def _table_exists(connection: sqlite3.Connection, name: str) -> bool:
    row = connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?", (name,)
    ).fetchone()
    return row is not None


def _migrate(connection: sqlite3.Connection) -> None:
    if _table_exists(connection, _LEGACY_TABLE) and not _table_exists(
        connection, "screening_results"
    ):
        connection.execute(
            f"ALTER TABLE {_LEGACY_TABLE} RENAME TO screening_results"
        )

    connection.execute(_SCHEMA)

    existing = {
        row["name"] for row in connection.execute("PRAGMA table_info(screening_results)")
    }
    for column, sql_type in _ADDED_COLUMNS.items():
        if column not in existing:
            connection.execute(
                f"ALTER TABLE screening_results ADD COLUMN {column} {sql_type}"
            )

    for statement in _INDEXES:
        connection.execute(statement)


@contextmanager
def connect() -> Iterator[sqlite3.Connection]:
    """Open a migrated connection, committing on success."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(str(DB_PATH))
    connection.row_factory = sqlite3.Row
    try:
        _migrate(connection)
        yield connection
        connection.commit()
    finally:
        connection.close()
