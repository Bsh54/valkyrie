"""Results store — SQLite persistence for docking results."""

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from drugforge.config import DB_PATH
from drugforge.pipeline import PipelineResult


def _get_connection() -> sqlite3.Connection:
    """Get a database connection, creating the DB and table if needed."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE IF NOT EXISTS docking_results (
            id TEXT PRIMARY KEY,
            timestamp TEXT NOT NULL,
            molecule_smiles TEXT NOT NULL,
            target_id TEXT NOT NULL,
            affinity REAL NOT NULL,
            vinardo_score REAL,
            consensus_score REAL,
            pose_sdf TEXT,
            pose_pdbqt TEXT,
            drug_likeness_json TEXT,
            admet_json TEXT,
            is_hit INTEGER,
            comparison_json TEXT,
            verdict TEXT,
            boltz_json TEXT
        )
    """)
    conn.commit()
    return conn


def save_result(result: PipelineResult) -> str:
    """
    Persist a pipeline result to SQLite.

    Returns the generated UUID for retrieval.
    """
    result_id = str(uuid.uuid4())
    timestamp = datetime.now(timezone.utc).isoformat()

    conn = _get_connection()
    try:
        conn.execute(
            """
            INSERT INTO docking_results
            (id, timestamp, molecule_smiles, target_id, affinity,
             vinardo_score, consensus_score,
             pose_sdf, pose_pdbqt, drug_likeness_json, admet_json,
             is_hit, comparison_json, verdict, boltz_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                result_id,
                timestamp,
                result.molecule_smiles,
                result.target_id,
                result.affinity_kcal_mol,
                result.vinardo_score,
                result.consensus_score,
                result.pose_sdf,
                result.pose_pdbqt,
                json.dumps(result.drug_likeness.to_dict()),
                json.dumps(result.admet.to_dict()),
                1 if result.is_hit else 0,
                json.dumps([c.to_dict() for c in result.comparisons]),
                result.verdict,
                json.dumps(result.boltz.to_dict()) if result.boltz else None,
            ),
        )
        conn.commit()
    finally:
        conn.close()

    return result_id


def get_result(result_id: str) -> Optional[dict]:
    """
    Retrieve a stored docking result by ID.

    Returns dict with all fields, or None if not found.
    """
    conn = _get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM docking_results WHERE id = ?", (result_id,)
        ).fetchone()
    finally:
        conn.close()

    if row is None:
        return None

    return {
        "result_id": row["id"],
        "timestamp": row["timestamp"],
        "molecule_smiles": row["molecule_smiles"],
        "target_id": row["target_id"],
        "affinity_kcal_mol": row["affinity"],
        "vinardo_score": row["vinardo_score"],
        "consensus_score": row["consensus_score"],
        "pose_sdf": row["pose_sdf"],
        "pose_pdbqt": row["pose_pdbqt"],
        "drug_likeness": json.loads(row["drug_likeness_json"]),
        "admet": json.loads(row["admet_json"]) if row["admet_json"] else None,
        "is_hit": bool(row["is_hit"]),
        "comparisons": json.loads(row["comparison_json"]),
        "verdict": row["verdict"],
        "boltz": json.loads(row["boltz_json"]) if row["boltz_json"] else None,
    }
