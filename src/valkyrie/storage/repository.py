"""Persistence for screening results."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone

from valkyrie.domain.models import IN_SILICO_DISCLAIMER, ScreeningResult
from valkyrie.storage.database import connect

_COLUMNS = (
    "id, timestamp, molecule_smiles, target_id, affinity, vinardo_score, "
    "consensus_score, pose_sdf, pose_pdbqt, drug_likeness_json, admet_json, "
    "is_hit, hit_reasons_json, comparison_json, verdict, boltz_json, "
    "explanation_json"
)


def save(result: ScreeningResult) -> str:
    """Store a result and return its identifier."""
    result_id = result.result_id or str(uuid.uuid4())
    timestamp = result.timestamp or datetime.now(timezone.utc).isoformat()

    values = (
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
        int(result.is_hit),
        json.dumps(result.hit_failure_reasons),
        json.dumps([c.to_dict() for c in result.comparisons]),
        result.verdict,
        json.dumps(result.boltz.to_dict()) if result.boltz else None,
        json.dumps(result.explanation.to_dict()) if result.explanation else None,
    )

    placeholders = ", ".join("?" * len(values))
    with connect() as connection:
        connection.execute(
            f"INSERT INTO screening_results ({_COLUMNS}) VALUES ({placeholders})",
            values,
        )

    result.result_id = result_id
    result.timestamp = timestamp
    return result_id


def _row_to_dict(row) -> dict:
    def decode(value, fallback):
        return json.loads(value) if value else fallback

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
        "drug_likeness": decode(row["drug_likeness_json"], {}),
        "admet": decode(row["admet_json"], None),
        "is_hit": bool(row["is_hit"]) if row["is_hit"] is not None else None,
        "hit_failure_reasons": decode(row["hit_reasons_json"], []),
        "comparisons": decode(row["comparison_json"], []),
        "verdict": row["verdict"],
        "boltz": decode(row["boltz_json"], None),
        "explanation": decode(row["explanation_json"], None),
        "disclaimer": IN_SILICO_DISCLAIMER,
    }


def get(result_id: str) -> dict | None:
    """Fetch one result by identifier."""
    with connect() as connection:
        row = connection.execute(
            "SELECT * FROM screening_results WHERE id = ?", (result_id,)
        ).fetchone()
    return _row_to_dict(row) if row else None


def latest_for(molecule_smiles: str, target_id: str) -> dict | None:
    """Fetch the most recent result for a molecule and target pair."""
    with connect() as connection:
        row = connection.execute(
            "SELECT * FROM screening_results WHERE molecule_smiles = ? "
            "AND target_id = ? ORDER BY timestamp DESC LIMIT 1",
            (molecule_smiles, target_id),
        ).fetchone()
    return _row_to_dict(row) if row else None
