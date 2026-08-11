"""Pipeline behaviour.

Fast tests cover orchestration and failure routing with the docking engine
stubbed. Tests marked slow run AutoDock Vina for real.
"""

from unittest.mock import patch

import pytest
from rdkit import Chem

from drugforge.errors import PipelineError
from drugforge.pipeline.comparison import build_comparisons, overall_verdict
from drugforge.pipeline.runner import run_screening


def test_invalid_molecule_fails_at_the_validation_stage():
    with patch("drugforge.chem.resolver._lookup_pubchem", return_value=None):
        with pytest.raises(PipelineError) as exc_info:
            run_screening("not_a_molecule_zzz", "pf-dhfr")
    assert exc_info.value.stage == "validate"


def test_unknown_target_fails_at_lookup():
    with pytest.raises(PipelineError) as exc_info:
        run_screening("CCO", "no-such-target")
    assert exc_info.value.stage == "target_lookup"


@pytest.mark.parametrize(
    ("consensus", "is_hit", "expected"),
    [
        (1.20, True, "Promising"),
        (1.00, True, "Promising"),
        (0.90, True, "Comparable"),
        (0.50, True, "Weak"),
        (1.50, False, "Discard"),
    ],
)
def test_verdict_thresholds(consensus, is_hit, expected):
    assert overall_verdict(consensus, is_hit) == expected


def test_comparisons_cover_affinity_and_descriptors(drug_likeness):
    class Baseline:
        affinity = -7.9

    baseline = Baseline()
    baseline.drug_likeness = drug_likeness

    comparisons = build_comparisons(-8.3, drug_likeness, baseline)
    metrics = {c.metric for c in comparisons}

    assert "affinity" in metrics
    assert "lipinski_violations" in metrics
    affinity = next(c for c in comparisons if c.metric == "affinity")
    assert affinity.verdict == "better"
    assert affinity.reference_value == -7.9


@pytest.mark.slow
def test_full_screening_produces_a_renderable_pose(clear_reference_cache):
    result = run_screening(
        "pyrimethamine", "pf-dhfr", exhaustiveness=4, with_explanation=False
    )

    assert result.affinity_kcal_mol < 0
    assert result.verdict in {"Promising", "Comparable", "Weak", "Discard"}
    assert result.comparisons

    pose = Chem.MolFromMolBlock(result.pose_sdf, sanitize=False)
    assert pose is not None
    assert pose.GetNumAtoms() > 0
    assert pose.GetNumBonds() > 0
    assert pose.GetConformer().Is3D()


@pytest.mark.slow
def test_scores_are_reported_relative_to_the_reference(clear_reference_cache):
    result = run_screening("CCO", "pf-dhfr", exhaustiveness=4, with_explanation=False)

    assert result.comparisons
    for comparison in result.comparisons:
        assert comparison.reference_value is not None
        assert comparison.ratio >= 0


@pytest.mark.slow
@pytest.mark.property
def test_repeated_docking_is_stable(clear_reference_cache):
    scores = [
        run_screening(
            "pyrimethamine", "pf-dhfr", exhaustiveness=8, with_explanation=False
        ).affinity_kcal_mol
        for _ in range(3)
    ]
    assert max(scores) - min(scores) < 0.5


@pytest.mark.slow
@pytest.mark.property
def test_reference_drug_outranks_an_inert_control(clear_reference_cache):
    reference = run_screening(
        "pyrimethamine", "pf-dhfr", exhaustiveness=8, with_explanation=False
    )
    glucose = run_screening(
        "OCC1OC(O)C(O)C(O)C1O", "pf-dhfr", exhaustiveness=8, with_explanation=False
    )
    assert reference.affinity_kcal_mol < glucose.affinity_kcal_mol
    assert reference.consensus_score > glucose.consensus_score
