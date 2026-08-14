"""In-process docking job queue.

A synchronous docking held an HTTP request open for one to two minutes, which the
proxy timed out (504) and let concurrent users starve each other on a small CPU
budget. Jobs decouple submission from execution: the POST returns immediately with
a job id, a single background worker runs the heavy dockings one at a time, and the
browser polls for the outcome. Serialising the work also removes multi-user CPU
contention: requests wait in a fair queue instead of fighting for cores.
"""

from __future__ import annotations

import logging
import queue
import threading
import uuid

from drugforge.errors import PipelineError
from drugforge.pipeline.runner import run_screening
from drugforge.storage import repository

logger = logging.getLogger(__name__)

_MAX_REMEMBERED = 500

_jobs: dict[str, dict] = {}
_order: list[str] = []
_cancelled: set[str] = set()
_lock = threading.Lock()
_queue: "queue.Queue[tuple[str, str, str, int]]" = queue.Queue()


def submit(molecule: str, target_id: str, exhaustiveness: int) -> str:
    """Enqueue a docking and return its job id immediately."""
    job_id = uuid.uuid4().hex
    with _lock:
        _jobs[job_id] = {
            "status": "queued",
            "position": _queue.qsize(),
            "result_id": None,
            "error": None,
        }
        _order.append(job_id)
        _prune()
    _queue.put((job_id, molecule, target_id, exhaustiveness))
    return job_id


def cancel(job_id: str) -> bool:
    """Request cancellation. A queued job is skipped before it runs (freeing the
    CPU); a job already running in-process finishes but is marked cancelled so the
    browser stops waiting on it."""
    with _lock:
        job = _jobs.get(job_id)
        if job is None or job["status"] in ("done", "error", "cancelled"):
            return False
        _cancelled.add(job_id)
        if job["status"] == "queued":
            job["status"] = "cancelled"
        return True


def get(job_id: str) -> dict | None:
    with _lock:
        job = _jobs.get(job_id)
        return dict(job) if job else None


def _prune() -> None:
    while len(_order) > _MAX_REMEMBERED:
        oldest = _order.pop(0)
        _jobs.pop(oldest, None)


def _run(job_id: str, molecule: str, target_id: str, exhaustiveness: int) -> None:
    with _lock:
        # Skip work the user already abandoned while it waited in the queue.
        if job_id in _cancelled:
            _cancelled.discard(job_id)
            _jobs[job_id] = {"status": "cancelled", "position": 0, "result_id": None, "error": None}
            return
        if job_id in _jobs:
            _jobs[job_id]["status"] = "running"
    try:
        result = run_screening(
            molecule_input=molecule,
            target_id=target_id,
            exhaustiveness=exhaustiveness,
        )
        result_id = repository.save(result)
        with _lock:
            _jobs[job_id] = {"status": "done", "position": 0, "result_id": result_id, "error": None}
    except PipelineError as exc:
        detail = getattr(exc.cause, "detail", str(exc.cause))
        with _lock:
            _jobs[job_id] = {"status": "error", "position": 0, "result_id": None,
                             "error": {"stage": exc.stage, "detail": detail}}
    except Exception as exc:  # never let the worker die
        logger.exception("Docking job %s failed", job_id)
        with _lock:
            _jobs[job_id] = {"status": "error", "position": 0, "result_id": None,
                             "error": {"detail": str(exc)}}


def _worker() -> None:
    while True:
        job_id, molecule, target_id, exhaustiveness = _queue.get()
        try:
            _run(job_id, molecule, target_id, exhaustiveness)
        finally:
            _queue.task_done()


_worker_thread = threading.Thread(target=_worker, name="docking-worker", daemon=True)
_worker_thread.start()
