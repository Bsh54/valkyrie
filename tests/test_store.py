"""Tests for the results store (SQLite)."""

import pytest
from unittest.mock import patch
from pathlib import Path
import tempfile

from drugforge.comparator import Comparison
from drugforge.druglikeness import DrugLikeness
from drugforge.pipeline import PipelineResult


@pytest.fixture
def temp_db(tmp_path):
    """Redirect DB to a temp directory."""
    db_path = tmp_path / "test_results.db"
    with patch("drugforge.store.DB_PATH", db_path):
        yield db_path


def _make_fake_result() -> PipelineResult:
    """Create a minimal PipelineResult for testing."""
    return PipelineResult(
        molecule_smiles="CCO",
        target_id="pf-dhfr",
        affinity_kcal_mol=-5.5,
        all_affinities=[-5.5, -5.2, -4.8],
        pose_sdf="fake sdf data",
        pose_pdbqt="fake pdbqt data",
        drug_likeness=DrugLikeness(
            molecular_weight=46.07,
            logp=-0.31,
            hbd=1,
            hba=1,
            tpsa=20.23,
            rotatable_bonds=0,
            lipinski_violations=0,
        ),
        comparisons=[
            Comparison(
                metric="affinity",
                molecule_value=-5.5,
                reference_value=-7.0,
                delta=1.5,
                ratio=0.786,
                verdict="worse",
            )
        ],
        verdict="Weaker",
    )


def test_save_and_retrieve(temp_db):
    """Save a result and retrieve it by ID."""
    from drugforge.store import save_result, get_result

    result = _make_fake_result()
    result_id = save_result(result)

    assert result_id  # non-empty UUID

    retrieved = get_result(result_id)
    assert retrieved is not None
    assert retrieved["molecule_smiles"] == "CCO"
    assert retrieved["affinity_kcal_mol"] == -5.5
    assert retrieved["verdict"] == "Weaker"
    assert retrieved["target_id"] == "pf-dhfr"


def test_retrieve_nonexistent(temp_db):
    """Retrieving a non-existent ID returns None."""
    from drugforge.store import get_result

    result = get_result("nonexistent-uuid")
    assert result is None


def test_save_multiple(temp_db):
    """Multiple saves produce different IDs."""
    from drugforge.store import save_result

    result = _make_fake_result()
    id1 = save_result(result)
    id2 = save_result(result)

    assert id1 != id2
