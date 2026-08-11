"""Ligand and receptor preparation."""

from unittest.mock import MagicMock, patch

import pytest

from drugforge.chem.ligand import prepare_ligand
from drugforge.chem.receptor import (
    get_receptor_pdbqt,
    prepare_receptor,
    strip_solvent_and_ligands,
)
from drugforge.domain.targets import get_target
from drugforge.errors import LigandPrepError, ReceptorError
from tests.conftest import PYRIMETHAMINE_SMILES

SAMPLE_PDB = """HEADER    TEST
ATOM      1  N   ALA A   1      10.000  15.000  25.000  1.00  0.00           N
ATOM      2  CA  ALA A   1      11.000  15.000  25.000  1.00  0.00           C
ATOM      3  C   ALA A   1      12.000  15.000  25.000  1.00  0.00           C
ATOM      4  O   ALA A   1      12.500  16.000  25.000  1.00  0.00           O
ATOM      5  O   HOH A   2      20.000  20.000  20.000  1.00  0.00           O
HETATM    6  C1  LIG A 201      18.000  15.000  25.000  1.00  0.00           C
TER
END
"""


def test_prepared_ligand_is_three_dimensional():
    mol, pdbqt = prepare_ligand(PYRIMETHAMINE_SMILES)
    assert mol.GetConformer().Is3D()
    assert "ATOM" in pdbqt or "HETATM" in pdbqt


def test_small_molecule_prepares():
    mol, pdbqt = prepare_ligand("CCO")
    assert mol.GetNumAtoms() > 0
    assert pdbqt


@pytest.mark.parametrize("value", ["", "   ", "not_valid_smiles_zzz"])
def test_unusable_input_raises_ligand_error(value):
    with pytest.raises(LigandPrepError):
        prepare_ligand(value)


def test_stripping_removes_solvent_and_heteroatoms():
    cleaned = strip_solvent_and_ligands(SAMPLE_PDB)
    assert "HOH" not in cleaned
    assert "LIG" not in cleaned
    assert "ALA" in cleaned


def test_structure_without_protein_is_rejected():
    with pytest.raises(ReceptorError):
        strip_solvent_and_ligands("HEADER ONLY\nEND\n")


@patch("drugforge.chem.receptor.subprocess.run")
def test_receptor_preparation_invokes_open_babel(mock_run, tmp_path):
    mock_run.return_value = MagicMock(returncode=0, stderr="")
    pdb_path = tmp_path / "test.pdb"
    pdb_path.write_text(SAMPLE_PDB)
    pdbqt_path = tmp_path / "test.pdbqt"
    pdbqt_path.write_text("ATOM placeholder")

    prepare_receptor(pdb_path, pdbqt_path)

    assert mock_run.call_args[0][0][0] == "obabel"
    assert (tmp_path / "test_clean.pdb").exists()


@patch("drugforge.chem.receptor.subprocess.run")
def test_open_babel_failure_is_reported(mock_run, tmp_path):
    mock_run.return_value = MagicMock(returncode=1, stderr="boom")
    pdb_path = tmp_path / "test.pdb"
    pdb_path.write_text(SAMPLE_PDB)

    with pytest.raises(ReceptorError):
        prepare_receptor(pdb_path, tmp_path / "missing.pdbqt")


@patch("drugforge.chem.receptor.download_structure")
def test_cached_receptor_skips_download(mock_download, tmp_path, monkeypatch):
    monkeypatch.setattr("drugforge.chem.receptor.RECEPTOR_CACHE_DIR", tmp_path)
    target = get_target("pf-dhfr")

    cache_dir = tmp_path / target.pdb_id
    cache_dir.mkdir()
    pdbqt_path = cache_dir / f"{target.pdb_id}_receptor.pdbqt"
    pdbqt_path.write_text("ATOM cached")

    assert get_receptor_pdbqt(target) == pdbqt_path
    mock_download.assert_not_called()
