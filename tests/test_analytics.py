"""Benchmark metrics and artifact loading."""

import json

from rdkit import Chem
from rdkit.Chem import AllChem

from valkyrie.analytics.benchmarks import (
    compute_auc,
    compute_enrichment_factor,
    compute_rmsd,
    load_report,
)


def test_auc_is_one_for_perfect_separation():
    assert compute_auc([-9.0, -8.5], [-5.0, -4.0]) == 1.0


def test_auc_is_zero_when_ranking_is_inverted():
    assert compute_auc([-4.0, -5.0], [-9.0, -8.5]) == 0.0


def test_auc_is_one_half_when_everything_ties():
    assert compute_auc([-7.0, -7.0], [-7.0, -7.0]) == 0.5


def test_auc_requires_both_groups():
    assert compute_auc([], [-5.0]) is None
    assert compute_auc([-5.0], []) is None


def test_enrichment_is_maximal_when_actives_lead():
    scores = [(-10.0 + i * 0.01, True) for i in range(10)]
    scores += [(-1.0 + i * 0.01, False) for i in range(90)]
    assert compute_enrichment_factor(scores, 0.10) == 10.0


def test_enrichment_is_about_one_without_signal():
    scores = [(float(i), i % 2 == 0) for i in range(100)]
    assert 0.8 <= compute_enrichment_factor(scores, 0.10) <= 1.2


def test_enrichment_needs_actives_and_a_valid_fraction():
    assert compute_enrichment_factor([(-5.0, False)], 0.1) is None
    assert compute_enrichment_factor([], 0.1) is None
    assert compute_enrichment_factor([(-5.0, True)], 0) is None
    assert compute_enrichment_factor([(-5.0, True)], 1.5) is None


def test_rmsd_of_a_pose_against_itself_is_zero():
    mol = Chem.AddHs(Chem.MolFromSmiles("c1ccccc1O"))
    params = AllChem.ETKDGv3()
    params.randomSeed = 7
    AllChem.EmbedMolecule(mol, params)
    assert compute_rmsd(mol, mol) == 0.0


def test_rmsd_tolerates_missing_input():
    assert compute_rmsd(None, None) is None


def test_missing_artifacts_are_reported_as_not_run(tmp_path, monkeypatch):
    monkeypatch.setattr("valkyrie.analytics.benchmarks.BENCHMARKS_DIR", tmp_path)
    report = load_report()
    assert report["internal"] is None
    assert report["internal_status"] == "not_run"
    assert report["external_status"] == "not_run"
    assert "in-silico" in report["scope_statement"].lower()


def test_skipped_entries_survive_loading(tmp_path, monkeypatch):
    monkeypatch.setattr("valkyrie.analytics.benchmarks.BENCHMARKS_DIR", tmp_path)
    (tmp_path / "external.json").write_text(
        json.dumps(
            {
                "attempted": 3,
                "evaluated": 2,
                "skipped": 1,
                "results": [
                    {"pdb_id": "1ABC", "rmsd": 1.1, "status": "ok"},
                    {
                        "pdb_id": "2DEF",
                        "status": "skipped",
                        "reason": "ligand_rebuild_failed",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    report = load_report()
    assert report["external_status"] == "available"
    skipped = [r for r in report["external"]["results"] if r["status"] == "skipped"]
    assert skipped[0]["reason"] == "ligand_rebuild_failed"


def test_corrupt_artifact_is_treated_as_absent(tmp_path, monkeypatch):
    monkeypatch.setattr("valkyrie.analytics.benchmarks.BENCHMARKS_DIR", tmp_path)
    (tmp_path / "internal.json").write_text("{ not json", encoding="utf-8")
    assert load_report()["internal_status"] == "not_run"
