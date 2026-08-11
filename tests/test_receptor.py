"""Tests for the receptor manager."""

import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

from drugforge.receptor import get_receptor_pdbqt, _prepare_receptor_pdbqt
from drugforge.targets import get_target
from drugforge.errors import ReceptorError


SAMPLE_PDB = """HEADER    TEST
ATOM      1  N   ALA A   1      10.000  15.000  25.000  1.00  0.00           N
ATOM      2  CA  ALA A   1      11.000  15.000  25.000  1.00  0.00           C
ATOM      3  C   ALA A   1      12.000  15.000  25.000  1.00  0.00           C
ATOM      4  O   ALA A   1      12.500  16.000  25.000  1.00  0.00           O
HETATM    5  O   HOH A 101      20.000  20.000  20.000  1.00  0.00           O
HETATM    6  C1  LIG A 201      18.000  15.000  25.000  1.00  0.00           C
TER
END
"""


@patch("drugforge.receptor.subprocess.run")
def test_prepare_receptor_strips_water_and_heteroatoms(mock_run, tmp_path):
    """Preparation should strip water and heteroatoms in the cleaned PDB."""
    mock_run.return_value = MagicMock(returncode=0, stderr="")
    pdb_file = tmp_path / "test.pdb"
    pdb_file.write_text(SAMPLE_PDB)
    pdbqt_file = tmp_path / "test.pdbqt"
    pdbqt_file.write_text("ATOM fake pdbqt")  # mock obabel output

    _prepare_receptor_pdbqt(pdb_file, pdbqt_file)

    # Check the cleaned PDB was written without HETATM/HOH
    clean_pdb = tmp_path / "test_clean.pdb"
    content = clean_pdb.read_text()
    assert "HOH" not in content
    assert "LIG" not in content
    assert "ALA" in content


@patch("drugforge.receptor.subprocess.run")
def test_prepare_receptor_calls_obabel(mock_run, tmp_path):
    """Preparation should invoke obabel for PDB to PDBQT conversion."""
    mock_run.return_value = MagicMock(returncode=0, stderr="")
    pdb_file = tmp_path / "test.pdb"
    pdb_file.write_text(SAMPLE_PDB)
    pdbqt_file = tmp_path / "test.pdbqt"
    pdbqt_file.write_text("ATOM fake pdbqt")  # simulate obabel output

    _prepare_receptor_pdbqt(pdb_file, pdbqt_file)

    mock_run.assert_called_once()
    args = mock_run.call_args[0][0]
    assert args[0] == "obabel"


@patch("drugforge.receptor._download_pdb")
def test_get_receptor_caches(mock_download, tmp_path):
    """Second call should use cached file, not download again."""
    target = get_target("pf-dhfr")

    with patch("drugforge.receptor.RECEPTOR_CACHE_DIR", tmp_path):
        # Create fake cached PDBQT
        cache_dir = tmp_path / target.pdb_id
        cache_dir.mkdir()
        pdbqt_path = cache_dir / f"{target.pdb_id}_receptor.pdbqt"
        pdbqt_path.write_text("ATOM fake content")

        result = get_receptor_pdbqt(target)
        assert result == pdbqt_path
        mock_download.assert_not_called()


def test_prepare_empty_pdb_raises(tmp_path):
    """Empty PDB file should raise ReceptorError."""
    pdb_file = tmp_path / "empty.pdb"
    pdb_file.write_text("HEADER EMPTY\nEND\n")
    pdbqt_file = tmp_path / "empty.pdbqt"

    with pytest.raises(ReceptorError):
        _prepare_receptor_pdbqt(pdb_file, pdbqt_file)
