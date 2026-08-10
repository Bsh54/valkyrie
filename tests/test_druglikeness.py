"""Tests for drug-likeness calculations."""

import pytest
from rdkit import Chem

from drugforge.druglikeness import compute_druglikeness, DrugLikeness


def test_pyrimethamine_passes_lipinski():
    """Pyrimethamine should have 0 Lipinski violations."""
    mol = Chem.MolFromSmiles("c1ccc(c(c1)Cl)c2cnc(nc2N)N")
    mol = Chem.AddHs(mol)
    result = compute_druglikeness(mol)

    assert isinstance(result, DrugLikeness)
    assert result.lipinski_violations == 0
    assert result.molecular_weight > 0
    assert result.molecular_weight < 500  # pyrimethamine MW ~ 248
    assert result.logp < 5
    assert result.hbd <= 5
    assert result.hba <= 10


def test_ethanol_descriptors():
    """Ethanol should have trivially good drug-likeness."""
    mol = Chem.MolFromSmiles("CCO")
    mol = Chem.AddHs(mol)
    result = compute_druglikeness(mol)

    assert result.lipinski_violations == 0
    assert result.molecular_weight < 100
    assert result.rotatable_bonds >= 0


def test_large_molecule_violations():
    """A large molecule should have Lipinski violations."""
    # Cyclosporine A - known Lipinski violator (MW > 1000, many HBD/HBA)
    cyclosporine = (
        "CC[C@H]1C(=O)N(CC(=O)N([C@H](C(=O)N[C@H](C(=O)N([C@H](C(=O)N"
        "[C@H](C(=O)N[C@@H](C(=O)N([C@H](C(=O)N([C@H](C(=O)N([C@H](C(=O)"
        "N1C)C(C)C)C)CC(C)C)C)CC(C)C)C)C)CC(C)C)C(C)C)CC(C)C)C)/C(=C/C)C)C"
    )
    mol = Chem.MolFromSmiles(cyclosporine)
    if mol is None:
        pytest.skip("Could not parse cyclosporine SMILES")
    mol = Chem.AddHs(mol)
    result = compute_druglikeness(mol)

    assert result.lipinski_violations >= 2


def test_to_dict():
    """DrugLikeness.to_dict() returns all fields."""
    mol = Chem.MolFromSmiles("CCO")
    mol = Chem.AddHs(mol)
    result = compute_druglikeness(mol)
    d = result.to_dict()

    assert "molecular_weight" in d
    assert "logp" in d
    assert "hbd" in d
    assert "hba" in d
    assert "tpsa" in d
    assert "rotatable_bonds" in d
    assert "lipinski_violations" in d
