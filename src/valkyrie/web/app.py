"""FastAPI application factory."""

from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from valkyrie import __version__
from valkyrie.config import STATIC_DIR, ensure_directories
from valkyrie.domain.models import IN_SILICO_DISCLAIMER
from valkyrie.web.routes import benchmarks, compounds, screening, targets

logger = logging.getLogger(__name__)

DESCRIPTION = (
    "Molecular docking for neglected tropical diseases. Valkyrie prioritises "
    "candidate molecules; it does not discover or prove drugs, and it never "
    "gives clinical advice."
)

# Client-side routes rendered by the SPA shell. Each one serves index.html and
# lets the router in app.js resolve the actual page from location.pathname.
_SPA_ROUTES = ("/", "/lab", "/library", "/benchmarks", "/result/{result_id}")


def create_app() -> FastAPI:
    ensure_directories()

    app = FastAPI(title="Valkyrie", description=DESCRIPTION, version=__version__)

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
        index_path = STATIC_DIR / "index.html"
        for route in _SPA_ROUTES:
            app.get(route, include_in_schema=False)(
                lambda: FileResponse(index_path)
            )

        for asset_dir in ("js", "css"):
            asset_path = STATIC_DIR / asset_dir
            if asset_path.is_dir():
                app.mount(
                    f"/{asset_dir}", StaticFiles(directory=str(asset_path)), name=asset_dir
                )
    else:
        logger.warning("Static directory %s not found; UI disabled", STATIC_DIR)

    return app


app = create_app()
