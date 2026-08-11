"""FastAPI application — REST API for DrugForge docking engine."""

import logging
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from drugforge.config import DEFAULT_EXHAUSTIVENESS, MAX_EXHAUSTIVENESS, MIN_EXHAUSTIVENESS, STATIC_DIR
from drugforge.errors import (
    DockingError,
    LigandPrepError,
    PipelineError,
    ReceptorError,
    TargetNotFoundError,
    ValidationError,
)
from drugforge.library import get_compounds, get_compound
from drugforge.pipeline import run_docking_pipeline
from drugforge.store import get_result, save_result
from drugforge.targets import TARGETS, get_target

logger = logging.getLogger(__name__)

app = FastAPI(
    title="DrugForge",
    description=(
        "Molecular docking engine for neglected tropical diseases. "
        "DrugForge PRIORITIZES candidate molecules — it does not discover or "
        "prove drugs and never gives clinical advice."
    ),
    version="0.1.0",
)


# ---------------------------------------------------------------------------
# Request/Response models
# ---------------------------------------------------------------------------

class DockRequest(BaseModel):
    molecule: str = Field(..., description="Molecule name or SMILES string")
    target_id: str = Field(..., description="Target identifier (e.g. 'pf-dhfr')")
    exhaustiveness: int = Field(
        default=DEFAULT_EXHAUSTIVENESS,
        ge=MIN_EXHAUSTIVENESS,
        le=MAX_EXHAUSTIVENESS,
        description="Vina search exhaustiveness (1-32)",
    )


class ErrorResponse(BaseModel):
    error: str
    detail: str
    stage: Optional[str] = None


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/api/targets")
def list_targets():
    """List all available docking targets."""
    return [
        {
            "id": t.id,
            "name": t.name,
            "disease": t.disease,
            "pdb_id": t.pdb_id,
            "reference_drug": t.reference.name,
        }
        for t in TARGETS.values()
    ]


@app.get("/api/targets/{target_id}")
def get_target_detail(target_id: str):
    """Get detailed information about a specific target."""
    try:
        target = get_target(target_id)
    except TargetNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.detail)

    return {
        "id": target.id,
        "name": target.name,
        "disease": target.disease,
        "pdb_id": target.pdb_id,
        "box": {
            "center": [target.box.center_x, target.box.center_y, target.box.center_z],
            "size": [target.box.size_x, target.box.size_y, target.box.size_z],
        },
        "reference": {
            "name": target.reference.name,
            "smiles": target.reference.smiles,
        },
    }


@app.post("/api/dock")
def dock_molecule(request: DockRequest):
    """
    Submit a molecule for docking against a target.

    This is a synchronous endpoint — it blocks until Vina completes (~10-60s).
    Returns the full docking result including affinity, poses, drug-likeness,
    and comparison to the reference drug.
    """
    try:
        result = run_docking_pipeline(
            molecule_input=request.molecule,
            target_id=request.target_id,
            exhaustiveness=request.exhaustiveness,
        )
    except PipelineError as e:
        if isinstance(e.cause, ValidationError):
            raise HTTPException(
                status_code=422,
                detail={
                    "error": "invalid_molecule",
                    "detail": e.cause.detail,
                    "stage": e.stage,
                },
            )
        elif isinstance(e.cause, TargetNotFoundError):
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "unknown_target",
                    "detail": e.cause.detail,
                    "stage": e.stage,
                },
            )
        elif isinstance(e.cause, (LigandPrepError, ReceptorError, DockingError)):
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "pipeline_failure",
                    "detail": e.cause.detail,
                    "stage": e.stage,
                },
            )
        else:
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "pipeline_failure",
                    "detail": e.detail,
                    "stage": e.stage,
                },
            )

    # Save result
    result_id = save_result(result)

    # Build response
    response = result.to_dict()
    response["result_id"] = result_id

    return response


@app.get("/api/result/{result_id}")
def get_stored_result(result_id: str):
    """Retrieve a previously stored docking result."""
    result = get_result(result_id)
    if result is None:
        raise HTTPException(
            status_code=404,
            detail={"error": "not_found", "detail": f"Result '{result_id}' not found."},
        )
    return result


@app.get("/api/compounds")
def list_compounds():
    return get_compounds()


@app.get("/api/compounds/{compound_id}")
def get_compound_detail(compound_id: str):
    compound = get_compound(compound_id)
    if compound is None:
        raise HTTPException(status_code=404, detail="Compound not found.")
    return compound


@app.get("/api/result/{result_id}/report")
def get_result_report(result_id: str):
    """Download a PDF report for a stored docking result."""
    from fastapi.responses import Response
    from drugforge.report import generate_report

    result = get_result(result_id)
    if result is None:
        raise HTTPException(
            status_code=404,
            detail={"error": "not_found", "detail": f"Result '{result_id}' not found."},
        )

    pdf_bytes = generate_report(result)
    return Response(
        content=bytes(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="drugforge_report_{result_id[:8]}.pdf"'
        },
    )


# Mount static files (frontend)
if STATIC_DIR.exists():
    app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")
