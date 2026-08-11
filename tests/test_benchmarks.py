"""Tests for benchmark metrics and artifact loading."""

from unittest.mock import patch

import pytest
from rdkit import Chem
from rdkit.Chem import AllChem

from drugforge.benchmarks import (
    compute_auc,
    compute_ef,
    compute_rmsd,
    load_benchmarks,
)


def test_auc_perfect_separation():
    assert compute_auc([-9.0, -8.5], [-5.0, -4.0]) == 1.0


def test_auc_reversed():
    assert compute_auc([-4.0, -5.0], [-9.0, -8.5]) == 0.0


def test_auc_all_tied():
    assert compute_auc([-7.0, -7.0], [-7.0, -7.0]) == 0.5


def test_auc_empty_group():
    assert compute_auc([], [-5.0]) is None
    assert compute_auc([-5.0], []) is None


def test_ef_all_actives_in_top_decile():
    scores = [(-10.0 + i * 0.01, True) for i in range(10)]
    scores += [(-1.0 + i * 0.01, False) for i in range(90)]
    assert compute_ef(scores, 0.10) == 10.0


def test_ef_no_enrichment():
    scores = []
    for i in range(100):
        scores.append((float(i), i % 2 == 0))
    ef = compute_ef(scores, 0.10)
    assert 0.8 <= ef <= 1.2


def test_ef_no_actives():
    assert compute_ef([(-5.0, False), (-4.0, False)], 0.1) is None


def test_ef_empty():
    assert compute_ef([], 0.1) is None


def test_ef_invalid_fraction():
    assert compute_ef([(-5.0, True)], 0) is None
    assert compute_ef([(-5.0, True)], 1.5) is None


def _embedded(smiles: str):
    mol = Chem.AddHs(Chem.MolFromSmiles(smiles))
    params = AllChem.ETKDGv3()
    params.randomSeed = 7
    AllChem.EmbedMolecule(mol, params)
    return mol


def test_rmsd_identity_is_zero():
    mol = _embedded("c1ccccc1O")
    assert compute_rmsd(mol, mol) == 0.0


def test_rmsd_handles_none():
    assert compute_rmsd(None, None) is None


def test_load_benchmarks_missing_artifacts(tmp_path):
    with patch("drugforge.benchmarks.BENCHMARKS_DIR", tmp_path):
        data = load_benchmarks()
    assert data["internal"] is None
    assert data["internal_status"] == "not_run"
    assert data["external_status"] == "not_run"
    assert "in-silico" in data["scope_statement"].lower()
    assert data["disclaimer"]


def test_load_benchmarks_reads_artifact(tmp_path):
    import json

    payload = {
        "attempted": 3,
        "evaluated": 2,
        "skipped": 1,
        "results": [
            {"pdb_id": "1ABC", "rmsd": 1.1, "status": "ok"},
            {"pdb_id": "2DEF", "status": "skipped", "reason": "ligand_rebuild_failed"},
        ],
    }
    (tmp_path / "external.json").write_text(json.dumps(payload), encoding="utf-8")

    with patch("drugforge.benchmarks.BENCHMARKS_DIR", tmp_path):
        data = load_benchmarks()

    assert data["external_status"] == "available"
    assert data["external"]["skipped"] == 1
    skipped = [r for r in data["external"]["results"] if r["status"] == "skipped"]
    assert len(skipped) == 1
    assert skipped[0]["reason"] == "ligand_rebuild_failed"


def test_load_benchmarks_corrupt_artifact(tmp_path):
    (tmp_path / "internal.json").write_text("{not json", encoding="utf-8")
    with patch("drugforge.benchmarks.BENCHMARKS_DIR", tmp_path):
        data = load_benchmarks()
    assert data["internal"] is None
    assert data["internal_status"] == "not_run"
