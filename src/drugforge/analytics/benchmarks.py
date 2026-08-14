"""Benchmark metrics and artifact access.

Metrics are pure functions so they can be tested without a docking engine. The
expensive runs happen offline and only their JSON artifacts are read here, which
keeps the web host free of heavy computation.
"""

from __future__ import annotations

import json
import math

from drugforge.config import BENCHMARKS_DIR

SCOPE_STATEMENT = (
    "These are in-silico benchmarks of a docking pipeline, not a clinical or "
    "experimental validation. Docking scores are weak predictors of true binding "
    "affinity. Failures and skipped cases are reported, not hidden."
)

DISCLAIMER = "In-silico benchmark. Not a clinical or experimental validation."

RMSD_SUCCESS_THRESHOLD = 2.0


def compute_auc(
    active_scores: list[float], inactive_scores: list[float]
) -> float | None:
    """Probability that an active outranks an inactive; ties count as a half."""
    if not active_scores or not inactive_scores:
        return None

    wins = 0.0
    for active in active_scores:
        for inactive in inactive_scores:
            if active < inactive:
                wins += 1.0
            elif active == inactive:
                wins += 0.5
    return round(wins / (len(active_scores) * len(inactive_scores)), 4)


def compute_enrichment_factor(
    scores: list[tuple[float, bool]], fraction: float
) -> float | None:
    """Enrichment factor over the best-scoring fraction of a ranked list."""
    if not scores or not 0 < fraction <= 1:
        return None

    total = len(scores)
    actives = sum(1 for _, is_active in scores if is_active)
    if actives == 0:
        return None

    top_n = max(1, math.ceil(total * fraction))
    ranked = sorted(scores, key=lambda pair: pair[0])
    found = sum(1 for _, is_active in ranked[:top_n] if is_active)

    return round((found / top_n) / (actives / total), 3)


def compute_rmsd(probe, reference) -> float | None:
    """Symmetry-corrected heavy-atom RMSD between two poses."""
    if probe is None or reference is None:
        return None

    from rdkit import Chem
    from rdkit.Chem import rdMolAlign

    try:
        return round(
            rdMolAlign.GetBestRMS(Chem.RemoveHs(probe), Chem.RemoveHs(reference)), 3
        )
    except Exception:
        return None


def _read_artifact(name: str) -> dict | None:
    path = BENCHMARKS_DIR / f"{name}.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def load_report() -> dict:
    """Read generated artifacts, reporting absent ones as not run.

    Aggregates one internal report per target: the primary ``internal.json`` plus
    any ``internal_<target_id>.json`` files, so the page can switch between targets.
    """
    external = _read_artifact("external")

    reports: list[dict] = []
    primary = _read_artifact("internal")
    if primary:
        reports.append(primary)
    for path in sorted(BENCHMARKS_DIR.glob("internal_*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if any(r.get("target_id") == data.get("target_id") for r in reports):
            continue
        reports.append(data)

    targets = [
        {
            "target_id": r.get("target_id"),
            "target_name": r.get("target_name"),
            "pdb_id": r.get("pdb_id"),
            "reference_drug": r.get("reference_drug"),
            "internal": r,
        }
        for r in reports
    ]

    return {
        # Backward-compatible primary target at the top level.
        "internal": primary,
        "internal_status": "available" if primary else "not_run",
        # All targets for the switcher.
        "targets": targets,
        "external": external,
        "external_status": "available" if external else "not_run",
        "scope_statement": SCOPE_STATEMENT,
        "disclaimer": DISCLAIMER,
    }
