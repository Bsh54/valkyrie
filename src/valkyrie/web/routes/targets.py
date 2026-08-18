"""Target registry endpoints."""

from fastapi import APIRouter, HTTPException

from valkyrie.domain.targets import get_target, list_targets
from valkyrie.errors import TargetNotFoundError

router = APIRouter(prefix="/api/targets", tags=["targets"])


@router.get("")
def get_targets() -> list[dict]:
    return [
        {
            "id": target.id,
            "name": target.name,
            "disease": target.disease,
            "pdb_id": target.pdb_id,
            "reference_drug": target.reference.name,
        }
        for target in list_targets()
    ]


@router.get("/{target_id}")
def get_target_detail(target_id: str) -> dict:
    try:
        target = get_target(target_id)
    except TargetNotFoundError as exc:
        raise HTTPException(status_code=404, detail=exc.detail) from exc

    return {
        "id": target.id,
        "name": target.name,
        "disease": target.disease,
        "pdb_id": target.pdb_id,
        "box": {"center": target.box.center, "size": target.box.size},
        "reference": {
            "name": target.reference.name,
            "smiles": target.reference.smiles,
        },
    }
