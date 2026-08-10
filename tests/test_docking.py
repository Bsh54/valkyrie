"""Tests for the docking engine (Vina wrapper)."""

import pytest

from drugforge.docking import dock, DockingResult, _pdbqt_to_sdf
from drugforge.ligand_prep import prepare_ligand
from drugforge.receptor import get_receptor_pdbqt
from drugforge.targets import get_target


@pytest.mark.slow
def test_dock_pyrimethamine():
    """Dock pyrimethamine against PfDHFR — should return negative affinity."""
    target = get_target("pf-dhfr")
    smiles = target.reference.smiles

    mol, ligand_pdbqt = prepare_ligand(smiles)
    receptor_path = get_receptor_pdbqt(target)

    result = dock(
        ligand_pdbqt=ligand_pdbqt,
        receptor_pdbqt_path=receptor_path,
        box=target.box,
        exhaustiveness=4,  # lower for test speed
    )

    assert isinstance(result, DockingResult)
    assert result.best_affinity < 0  # binding = negative kcal/mol
    assert len(result.all_affinities) > 0
    assert result.best_pose_pdbqt  # non-empty
    assert result.best_pose_sdf  # non-empty


@pytest.mark.slow
def test_dock_ethanol():
    """Dock ethanol — should dock but with weaker affinity."""
    target = get_target("pf-dhfr")
    mol, ligand_pdbqt = prepare_ligand("CCO")
    receptor_path = get_receptor_pdbqt(target)

    result = dock(
        ligand_pdbqt=ligand_pdbqt,
        receptor_pdbqt_path=receptor_path,
        box=target.box,
        exhaustiveness=4,
    )

    assert isinstance(result, DockingResult)
    assert result.best_affinity < 0  # still binds somewhat


def test_pdbqt_to_sdf_empty():
    """Empty PDBQT produces empty SDF."""
    sdf = _pdbqt_to_sdf("")
    assert sdf == ""


def test_pdbqt_to_sdf_basic():
    """Basic PDBQT atom lines produce non-empty output."""
    pdbqt = (
        "ATOM      1  C1  LIG A   1      10.000  15.000  25.000  1.00  0.00     0.000 C\n"
        "ATOM      2  O1  LIG A   1      11.000  15.000  25.000  1.00  0.00     0.000 OA\n"
    )
    sdf = _pdbqt_to_sdf(pdbqt)
    assert len(sdf) > 0
