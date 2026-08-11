"""Tests for ADMET/toxicity filter."""

import pytest
from rdkit import Chem

from drugforge.admet import compute_admet, is_hit, ADMETResult, _DISCLAIMER
from drugforge.druglikeness import compute_druglikeness


def test_clean_molecule_passes():
    """Pyrimethamine (clean drug) should pass all ADMET filters."""
    mol = Chem.MolFromSmiles("c1ccc(c(c1)Cl)c2cnc(nc2N)N")
    mol = Chem.AddHs(mol)
    result = compute_admet(mol)

    assert result.passes_filter is True
    assert result.failure_reasons == []
    assert result.pains_alerts == []
    assert result.reactive_groups == []


def test_rhodanine_flagged():
    """Rhodanine (known PAINS) should be flagged."""
    # Rhodanine core: 2-thioxo-1,3-thiazolidin-4-one
    rhodanine_smiles = "O=C1CSC(=S)N1"
    mol = Chem.MolFromSmiles(rhodanine_smiles)
    if mol is None:
        pytest.skip("Could not parse rhodanine SMILES")
    mol = Chem.AddHs(mol)
    result = compute_admet(mol)

    # Rhodanine should trigger PAINS or Brenk alerts
    has_alert = len(result.pains_alerts) > 0 or len(result.brenk_alerts) > 0
    assert has_alert, f"Rhodanine not flagged. PAINS: {result.pains_alerts}, Brenk: {result.brenk_alerts}"


def test_michael_acceptor_flagged():
    """Molecule with Michael acceptor should be flagged."""
    # Acrolein: simplest Michael acceptor
    mol = Chem.MolFromSmiles("C=CC=O")
    mol = Chem.AddHs(mol)
    result = compute_admet(mol)

    assert "Michael acceptor" in result.reactive_groups
    assert result.passes_filter is False


def test_disclaimer_present():
    """Every ADMET result must carry the in-silico disclaimer."""
    mol = Chem.MolFromSmiles("CCO")
    mol = Chem.AddHs(mol)
    result = compute_admet(mol)

    assert result.disclaimer
    assert "in-silico" in result.disclaimer


def test_esol_computed():
    """ESOL logS should be a reasonable float."""
    mol = Chem.MolFromSmiles("c1ccc(c(c1)Cl)c2cnc(nc2N)N")
    mol = Chem.AddHs(mol)
    result = compute_admet(mol)

    assert isinstance(result.esol_logs, float)
    # Pyrimethamine should be moderately soluble
    assert -6 < result.esol_logs < 2


def test_gi_absorption():
    """GI absorption prediction should return High or Low."""
    mol = Chem.MolFromSmiles("CCO")
    mol = Chem.AddHs(mol)
    result = compute_admet(mol)

    assert result.gi_absorption in ("High", "Low")


def test_is_hit_clean_molecule():
    """Clean drug-like molecule is a hit."""
    mol = Chem.MolFromSmiles("c1ccc(c(c1)Cl)c2cnc(nc2N)N")
    mol = Chem.AddHs(mol)
    dl = compute_druglikeness(mol)
    admet = compute_admet(mol)

    hit, reasons = is_hit(dl, admet)
    assert hit is True
    assert reasons == []


def test_is_hit_lipinski_violator():
    """Molecule with >1 Lipinski violations is not a hit."""
    from drugforge.druglikeness import DrugLikeness

    fake_dl = DrugLikeness(
        molecular_weight=600, logp=6.0, hbd=6, hba=11,
        tpsa=50.0, rotatable_bonds=5, lipinski_violations=3,
    )
    mol = Chem.MolFromSmiles("CCO")
    mol = Chem.AddHs(mol)
    admet = compute_admet(mol)

    hit, reasons = is_hit(fake_dl, admet)
    assert hit is False
    assert any("Lipinski" in r for r in reasons)
