"""Screening submission (queued), job polling and stored result retrieval."""

import logging

from fastapi import APIRouter, HTTPException, Response

from drugforge.reporting.pdf import build_report
from drugforge.storage import repository
from drugforge.web import jobs
from drugforge.web.schemas import ScreeningRequest

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["screening"])


@router.post("/screenings")
def submit_screening(request: ScreeningRequest) -> dict:
    """Queue a docking and return a job id at once; poll GET /api/jobs/{id}."""
    job_id = jobs.submit(
        molecule=request.molecule,
        target_id=request.target_id,
        exhaustiveness=request.exhaustiveness,
    )
    return {"job_id": job_id, "status": "queued"}


@router.get("/jobs/{job_id}")
def get_job(job_id: str) -> dict:
    """Report a docking job: queued, running, done (with result_id) or error."""
    job = jobs.get(job_id)
    if job is None:
        raise HTTPException(
            status_code=404,
            detail={"error": "not_found", "detail": f"No job '{job_id}'."},
        )
    return {"job_id": job_id, **job}


@router.post("/jobs/{job_id}/cancel")
def cancel_job(job_id: str) -> dict:
    """Cancel an abandoned job so a queued docking never wastes the server."""
    return {"job_id": job_id, "cancelled": jobs.cancel(job_id)}


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
