"""Open ethnobotanical + molecular dataset (JSON and CSV, CC-BY-4.0).

A reusable, cited dataset that bridges African medicinal-plant knowledge to the
disease protein targets Valkyrie screens against. Generated from the same data the
app uses, so the download always matches what is shown.
"""

from __future__ import annotations

import csv
import io
from datetime import datetime, timezone

from fastapi import APIRouter, Response

from valkyrie.content import library
from valkyrie.domain.models import IN_SILICO_DISCLAIMER
from valkyrie.domain.targets import list_targets

router = APIRouter(prefix="/api", tags=["dataset"])

LICENSE = "CC-BY-4.0"


def _targets() -> list[dict]:
    return [
        {
            "id": target.id,
            "name": target.name,
            "disease": target.disease,
            "pdb_id": target.pdb_id,
            "reference_drug": target.reference.name,
            "reference_smiles": target.reference.smiles,
        }
        for target in list_targets()
    ]


def _compound_rows() -> list[dict]:
    rows = []
    for compound in library.list_compounds():
        plant = compound.get("plant") or {}
        use = compound.get("traditional_use") or {}
        rows.append(
            {
                "compound": compound.get("compound_name", ""),
                "smiles": compound.get("smiles", ""),
                "plant_scientific_name": plant.get("scientific_name", ""),
                "plant_local_name": plant.get("local_name", ""),
                "plant_family": plant.get("family", ""),
                "traditional_disease": use.get("disease", ""),
                "region": use.get("region", ""),
                "people": use.get("people", ""),
                "preparation": use.get("preparation", ""),
                "part_used": use.get("part_used", ""),
                "source": compound.get("source", ""),
            }
        )
    return rows


@router.get("/dataset")
def get_dataset() -> dict:
    return {
        "license": LICENSE,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "disclaimer": IN_SILICO_DISCLAIMER,
        "description": (
            "Open dataset bridging African medicinal-plant knowledge to validated "
            "disease protein targets: each plant compound with its traditional use, "
            "region, people, preparation, source and SMILES, plus the docking targets."
        ),
        "targets": _targets(),
        "compounds": _compound_rows(),
    }


@router.get("/dataset.csv")
def get_dataset_csv() -> Response:
    rows = _compound_rows()
    buffer = io.StringIO()
    if rows:
        writer = csv.DictWriter(buffer, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    return Response(
        content=buffer.getvalue(),
        media_type="text/csv",
        headers={
            "Content-Disposition": 'attachment; filename="valkyrie_ethnobotanical_dataset.csv"'
        },
    )
