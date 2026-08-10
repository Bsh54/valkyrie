"""Tests for the pipeline orchestrator."""

import pytest

from drugforge.pipeline import run_docking_pipeline, PipelineResult
from drugforge.errors import PipelineError


@pytest.mark.slow
def test_pipeline_end_to_end():
    """Full pipeline with pyrimethamine on pf-dhfr should succeed."""
    result = run_docking_pipeline(
        molecule_input="pyrimethamine",
        target_id="pf-dhfr",
        exhaustiveness=4,
    )

    assert isinstance(result, PipelineResult)
    assert result.affinity_kcal_mol < 0
    assert result.molecule_smiles
    assert result.target_id == "pf-dhfr"
    assert result.pose_sdf
    assert result.pose_pdbqt
    assert result.drug_likeness is not None
    assert len(result.comparisons) > 0
    assert result.verdict in ("Promising", "Comparable", "Weaker")


def test_pipeline_invalid_molecule():
    """Invalid molecule input should raise PipelineError at validate stage."""
    with pytest.raises(PipelineError) as exc_info:
        run_docking_pipeline(
            molecule_input="not_a_valid_molecule_xyz!!!",
            target_id="pf-dhfr",
            exhaustiveness=4,
        )
    assert exc_info.value.stage == "validate"


def test_pipeline_unknown_target():
    """Unknown target should raise PipelineError at target_lookup stage."""
    with pytest.raises(PipelineError) as exc_info:
        run_docking_pipeline(
            molecule_input="CCO",
            target_id="nonexistent-target",
            exhaustiveness=4,
        )
    assert exc_info.value.stage == "target_lookup"


@pytest.mark.slow
def test_pipeline_result_to_dict():
    """PipelineResult.to_dict() should return a complete dict."""
    result = run_docking_pipeline(
        molecule_input="CCO",
        target_id="pf-dhfr",
        exhaustiveness=4,
    )
    d = result.to_dict()

    assert "molecule_smiles" in d
    assert "affinity_kcal_mol" in d
    assert "pose_sdf" in d
    assert "drug_likeness" in d
    assert "comparisons" in d
    assert "verdict" in d
