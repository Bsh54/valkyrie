"""FastAPI application factory."""

from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from drugforge import __version__
from drugforge.config import STATIC_DIR, ensure_directories
from drugforge.domain.models import IN_SILICO_DISCLAIMER
from drugforge.web.routes import benchmarks, compounds, screening, targets

logger = logging.getLogger(__name__)

DESCRIPTION = (
    "Molecular docking for neglected tropical diseases. DrugForge prioritises "
    "candidate molecules; it does not discover or prove drugs, and it never "
    "gives clinical advice."
)


def create_app() -> FastAPI:
    ensure_directories()

    app = FastAPI(title="DrugForge", description=DESCRIPTION, version=__version__)

    app.include_router(targets.router)
    app.include_router(screening.router)
    app.include_router(compounds.router)
    app.include_router(benchmarks.router)

    @app.get("/api/health", tags=["meta"])
    def health() -> dict:
        return {
            "status": "ok",
            "version": __version__,
            "disclaimer": IN_SILICO_DISCLAIMER,
        }

    if STATIC_DIR.is_dir():
        app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")
    else:
        logger.warning("Static directory %s not found; UI disabled", STATIC_DIR)

    return app


app = create_app()
