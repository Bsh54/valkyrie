"""HTTP routers grouped by resource."""

from drugforge.web.routes import benchmarks, compounds, screening, targets

__all__ = ["benchmarks", "compounds", "screening", "targets"]
