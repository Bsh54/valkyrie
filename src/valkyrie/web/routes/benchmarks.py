"""Benchmark reporting endpoint.

Serves artifacts produced offline. Nothing is computed per request.
"""

from fastapi import APIRouter

from valkyrie.analytics.benchmarks import load_report

router = APIRouter(prefix="/api/benchmarks", tags=["benchmarks"])


@router.get("")
def get_benchmarks() -> dict:
    return load_report()
