"""Tests for consensus scoring: Vinardo rescore + consensus combination."""

import pytest

from drugforge.consensus import compute_consensus, ConsensusResult
from drugforge.rescoring import rescore_vinardo


# ---------------------------------------------------------------------------
# Unit tests (fast)
# ---------------------------------------------------------------------------

def test_consensus_formula_equal_scores():
    """When molecule equals reference, consensus should be ~1.0."""
    result = compute_consensus(
        vina_score=-8.0,
        vinardo_score=-7.0,
        ref_vina=-8.0,
        ref_vinardo=-7.0,
    )
    assert isinstance(result, ConsensusResult)
    assert abs(result.consensus_score - 1.0) < 0.01


def test_consensus_better_than_reference():
    """Molecule with more negative scores gives consensus > 1.0 (ratio of negatives)."""
    result = compute_consensus(
        vina_score=-10.0,
        vinardo_score=-9.0,
        ref_vina=-8.0,
        ref_vinardo=-7.0,
    )
    # -10/-8 = 1.25, -9/-7 = 1.286 → consensus > 1.0 means stronger binding
    assert result.consensus_score > 1.0


def test_consensus_worse_than_reference():
    """Molecule with less negative scores gives consensus < 1.0."""
    result = compute_consensus(
        vina_score=-4.0,
        vinardo_score=-3.0,
        ref_vina=-8.0,
        ref_vinardo=-7.0,
    )
    # -4/-8 = 0.5, -3/-7 = 0.43 → consensus < 1.0 means weaker binding
    assert result.consensus_score < 1.0


def test_consensus_result_fields():
    """ConsensusResult has all required fields."""
    result = compute_consensus(
        vina_score=-7.5,
        vinardo_score=-6.5,
        ref_vina=-8.0,
        ref_vinardo=-7.0,
    )
    assert hasattr(result, "vina_score")
    assert hasattr(result, "vinardo_score")
    assert hasattr(result, "consensus_score")


# ---------------------------------------------------------------------------
# Property-based tests (slow — require Vina)
# ---------------------------------------------------------------------------

@pytest.mark.slow
@pytest.mark.property
def test_consensus_determinism():
    """Docking same molecule N times must yield consensus scores within epsilon."""
    from drugforge.pipeline import run_docking_pipeline

    EPSILON = 0.1  # allow small variance from Vina non-determinism

    scores = []
    for _ in range(3):
        result = run_docking_pipeline(
            molecule_input="pyrimethamine",
            target_id="pf-dhfr",
            exhaustiveness=8,
        )
        scores.append(result.consensus_score)

    score_range = max(scores) - min(scores)
    assert score_range < EPSILON, (
        f"Consensus not stable: {scores}, range={score_range} >= {EPSILON}"
    )


@pytest.mark.slow
@pytest.mark.property
def test_active_outranks_inert_after_consensus():
    """Pyrimethamine must have better consensus than glucose after rescoring."""
    from drugforge.pipeline import run_docking_pipeline

    active = run_docking_pipeline(
        molecule_input="pyrimethamine",
        target_id="pf-dhfr",
        exhaustiveness=8,
    )
    inert = run_docking_pipeline(
        molecule_input="glucose",
        target_id="pf-dhfr",
        exhaustiveness=8,
    )

    # Higher consensus = better binding (ratio of negatives)
    assert active.consensus_score > inert.consensus_score, (
        f"Active ({active.consensus_score}) should outrank inert "
        f"({inert.consensus_score}) by consensus"
    )
