"""Tests for ligand preparation."""

import pytest

from drugforge.ligand_prep import prepare_ligand
from drugforge.errors import LigandPrepError


def test_prepare_pyrimethamine():
    """Pyrimethamine SMILES produces valid 3D mol and PDBQT."""
    smiles = "c1ccc(c(c1)Cl)c2cnc(nc2N)N"
    mol, pdbqt = prepare_ligand(smiles)

    # Mol should have 3D coordinates
    assert mol is not None
    conf = mol.GetConformer()
    assert conf.Is3D()

    # PDBQT should be non-empty and contain ATOM lines
    assert pdbqt
    assert "ATOM" in pdbqt or "HETATM" in pdbqt


def test_prepare_simple_molecule():
    """Simple molecule (ethanol) prepares successfully."""
    mol, pdbqt = prepare_ligand("CCO")
    assert mol is not None
    assert pdbqt


def test_prepare_invalid_smiles_raises():
    """Invalid SMILES raises LigandPrepError."""
    with pytest.raises(LigandPrepError):
        prepare_ligand("not_valid_smiles_xyz")


def test_prepare_empty_raises():
    """Empty SMILES raises LigandPrepError."""
    with pytest.raises(LigandPrepError):
        prepare_ligand("")
