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


def test_prepare_receptor_strips_water_and_heteroatoms(tmp_path):
    """Preparation should strip water and heteroatoms."""
    pdb_file = tmp_path / "test.pdb"
    pdb_file.write_text(SAMPLE_PDB)
    pdbqt_file = tmp_path / "test.pdbqt"

    _prepare_receptor_pdbqt(pdb_file, pdbqt_file)

    content = pdbqt_file.read_text()
    assert "HOH" not in content
    assert "LIG" not in content
    assert "ALA" in content


def test_prepare_receptor_produces_pdbqt(tmp_path):
    """Prepared file should contain ATOM records."""
    pdb_file = tmp_path / "test.pdb"
    pdb_file.write_text(SAMPLE_PDB)
    pdbqt_file = tmp_path / "test.pdbqt"

    _prepare_receptor_pdbqt(pdb_file, pdbqt_file)

    content = pdbqt_file.read_text()
    assert pdbqt_file.exists()
    assert len(content) > 0
    # Should have atom-type info appended
    lines = [l for l in content.splitlines() if l.startswith("ATOM")]
    assert len(lines) == 4


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
