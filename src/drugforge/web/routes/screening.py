"""Screening submission and stored result retrieval."""

import logging

from fastapi import APIRouter, HTTPException, Response

from drugforge.errors import (
    DockingError,
    LigandPrepError,
    PipelineError,
    ReceptorError,
    TargetNotFoundError,
    ValidationError,
)
from drugforge.pipeline.runner import run_screening
from drugforge.reporting.pdf import build_report
from drugforge.storage import repository
from drugforge.web.schemas import ScreeningRequest

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["screening"])

_STATUS_BY_CAUSE = {
    ValidationError: (422, "invalid_molecule"),
    TargetNotFoundError: (404, "unknown_target"),
    LigandPrepError: (422, "ligand_preparation_failed"),
    ReceptorError: (502, "receptor_unavailable"),
    DockingError: (500, "docking_failed"),
}


def _to_http_error(error: PipelineError) -> HTTPException:
    status, code = _STATUS_BY_CAUSE.get(type(error.cause), (500, "pipeline_failure"))
    return HTTPException(
        status_code=status,
        detail={"error": code, "detail": error.cause.detail, "stage": error.stage},
    )


@router.post("/screenings")
def submit_screening(request: ScreeningRequest) -> dict:
    """Screen a molecule. Synchronous: expect roughly one to two minutes."""
    try:
        result = run_screening(
            molecule_input=request.molecule,
            target_id=request.target_id,
            exhaustiveness=request.exhaustiveness,
        )
    except PipelineError as exc:
        logger.info("Screening rejected at stage %s: %s", exc.stage, exc.cause.detail)
        raise _to_http_error(exc) from exc

    repository.save(result)
    return result.to_dict()


@router.get("/screenings/{result_id}")
def get_screening(result_id: str) -> dict:
    result = repository.get(result_id)
    if result is None:
        raise HTTPException(
            status_code=404,
            detail={"error": "not_found", "detail": f"No result '{result_id}'."},
        )
    return result


@router.get("/screenings/{result_id}/report")
def download_report(result_id: str) -> Response:
    result = repository.get(result_id)
    if result is None:
        raise HTTPException(
            status_code=404,
            detail={"error": "not_found", "detail": f"No result '{result_id}'."},
        )

    filename = f"drugforge_report_{result_id[:8]}.pdf"
    return Response(
        content=build_report(result),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
