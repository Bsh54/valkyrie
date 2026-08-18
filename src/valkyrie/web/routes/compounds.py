"""Ethnobotanical compound library endpoints."""

from fastapi import APIRouter, HTTPException

from valkyrie.content.library import get_compound, list_compounds
from valkyrie.domain.models import IN_SILICO_DISCLAIMER

router = APIRouter(prefix="/api/compounds", tags=["compounds"])


@router.get("")
def get_compounds() -> dict:
    return {
        "framing": "Traditional knowledge to in-silico molecular validation.",
        "disclaimer": IN_SILICO_DISCLAIMER,
        "compounds": list_compounds(),
    }


@router.get("/{compound_id}")
def get_compound_detail(compound_id: str) -> dict:
    compound = get_compound(compound_id)
    if compound is None:
        raise HTTPException(status_code=404, detail=f"No compound '{compound_id}'.")
    return {**compound, "disclaimer": IN_SILICO_DISCLAIMER}
