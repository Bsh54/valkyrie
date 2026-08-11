"""Tests for the FastAPI application."""

import pytest
from unittest.mock import patch, MagicMock

from fastapi.testclient import TestClient

from drugforge.api import app
from drugforge.comparator import Comparison
from drugforge.druglikeness import DrugLikeness
from drugforge.errors import PipelineError, ValidationError, TargetNotFoundError
from drugforge.pipeline import PipelineResult


client = TestClient(app)


def test_list_targets():
    """GET /api/targets returns target list."""
    response = client.get("/api/targets")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert data[0]["id"] == "pf-dhfr"
    assert data[0]["disease"] == "malaria"


def test_get_target_detail():
    """GET /api/targets/pf-dhfr returns full target info."""
    response = client.get("/api/targets/pf-dhfr")
    assert response.status_code == 200
    data = response.json()
    assert data["pdb_id"] == "1J3I"
    assert "box" in data
    assert "reference" in data


def test_get_target_unknown():
    """GET /api/targets/unknown returns 404."""
    response = client.get("/api/targets/nonexistent")
    assert response.status_code == 404


@patch("drugforge.api.run_docking_pipeline")
@patch("drugforge.api.save_result")
def test_dock_success(mock_save, mock_pipeline):
    """POST /api/dock with valid input returns docking result."""
    from drugforge.admet import ADMETResult
    mock_save.return_value = "test-uuid-123"
    mock_pipeline.return_value = PipelineResult(
        molecule_smiles="CCO",
        target_id="pf-dhfr",
        affinity_kcal_mol=-5.5,
        vinardo_score=-4.8,
        consensus_score=1.2,
        all_affinities=[-5.5, -5.2],
        pose_sdf="sdf data",
        pose_pdbqt="pdbqt data",
        drug_likeness=DrugLikeness(
            molecular_weight=46.07, logp=-0.31, hbd=1, hba=1,
            tpsa=20.23, rotatable_bonds=0, lipinski_violations=0,
        ),
        admet=ADMETResult(
            esol_logs=-1.0, gi_absorption="High",
            pains_alerts=[], brenk_alerts=[], nih_alerts=[],
            reactive_groups=[], passes_filter=True, failure_reasons=[],
        ),
        is_hit=True,
        hit_failure_reasons=[],
        comparisons=[Comparison(
            metric="affinity", molecule_value=-5.5,
            reference_value=-7.0, delta=1.5, ratio=0.786, verdict="worse",
        )],
        verdict="Weaker",
    )

    response = client.post("/api/dock", json={
        "molecule": "ethanol",
        "target_id": "pf-dhfr",
    })
    assert response.status_code == 200
    data = response.json()
    assert data["result_id"] == "test-uuid-123"
    assert data["affinity_kcal_mol"] == -5.5


@patch("drugforge.api.run_docking_pipeline")
def test_dock_invalid_molecule(mock_pipeline):
    """POST /api/dock with invalid molecule returns 422."""
    mock_pipeline.side_effect = PipelineError(
        stage="validate",
        cause=ValidationError("Could not resolve 'xyz' as a compound name or SMILES string.")
    )

    response = client.post("/api/dock", json={
        "molecule": "xyz",
        "target_id": "pf-dhfr",
    })
    assert response.status_code == 422


@patch("drugforge.api.run_docking_pipeline")
def test_dock_unknown_target(mock_pipeline):
    """POST /api/dock with unknown target returns 404."""
    mock_pipeline.side_effect = PipelineError(
        stage="target_lookup",
        cause=TargetNotFoundError("Unknown target 'fake'")
    )

    response = client.post("/api/dock", json={
        "molecule": "CCO",
        "target_id": "fake",
    })
    assert response.status_code == 404


def test_get_result_not_found():
    """GET /api/result/nonexistent returns 404."""
    response = client.get("/api/result/nonexistent-uuid")
    assert response.status_code == 404
