"""Benchmark metrics and artifact loading.

Metrics are pure functions so they can be unit-tested without Vina. Heavy
redocking runs happen offline (see notebooks/ and scripts/); this module only
computes numbers and reads the generated artifacts.
"""

import json
import math
from pathlib import Path
from typing import Optional

from drugforge.config import BENCHMARKS_DIR

SCOPE_STATEMENT = (
    "These are in-silico benchmarks of a docking pipeline, not a clinical or "
    "experimental validation. Docking scores are weak predictors of true binding "
    "affinity. Failures and skipped cases are reported, not hidden."
)

DISCLAIMER = "In-silico benchmark. Not clinical or experimental validation."


def compute_auc(active_scores: list[float], inactive_scores: list[float]) -> Optional[float]:
    """Probability that an active scores better than an inactive.

    Scores are binding energies, so lower is better. Ties count as 0.5.
    Returns None when either group is empty.
    """
    if not active_scores or not inactive_scores:
        return None

    wins = 0.0
    for a in active_scores:
        for i in inactive_scores:
            if a < i:
                wins += 1.0
            elif a == i:
                wins += 0.5
    return round(wins / (len(active_scores) * len(inactive_scores)), 4)


def compute_ef(scores: list[tuple[float, bool]], fraction: float) -> Optional[float]:
    """Enrichment factor at a top fraction of the ranked list.

    `scores` pairs a binding energy with an is_active flag. Lower energy ranks
    first. Returns None when the input is empty or contains no actives.
    """
    if not scores or not 0 < fraction <= 1:
        return None

    total = len(scores)
    n_actives = sum(1 for _, is_active in scores if is_active)
    if n_actives == 0:
        return None

    top_n = max(1, math.ceil(total * fraction))
    ranked = sorted(scores, key=lambda pair: pair[0])
    actives_in_top = sum(1 for _, is_active in ranked[:top_n] if is_active)

    return round((actives_in_top / top_n) / (n_actives / total), 3)


def compute_rmsd(probe, reference) -> Optional[float]:
    """Symmetry-corrected heavy-atom RMSD between two conformers."""
    from rdkit import Chem
    from rdkit.Chem import rdMolAlign

    if probe is None or reference is None:
        return None
    try:
        probe_heavy = Chem.RemoveHs(probe)
        reference_heavy = Chem.RemoveHs(reference)
        return round(rdMolAlign.GetBestRMS(probe_heavy, reference_heavy), 3)
    except Exception:
        return None


def _read_artifact(name: str) -> Optional[dict]:
    path = BENCHMARKS_DIR / f"{name}.json"
    if not path.exists():
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def load_benchmarks() -> dict:
    """Read generated benchmark artifacts. Absent artifacts report not_run."""
    internal = _read_artifact("internal")
    external = _read_artifact("external")
    return {
        "internal": internal,
        "external": external,
        "internal_status": "available" if internal else "not_run",
        "external_status": "available" if external else "not_run",
        "scope_statement": SCOPE_STATEMENT,
        "disclaimer": DISCLAIMER,
    }
