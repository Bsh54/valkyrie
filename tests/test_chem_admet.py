"""Descriptors, ADMET alerts and hit determination."""

import pytest
from rdkit import Chem

from drugforge.chem.admet import compute_admet, evaluate_hit, predict_esol
from drugforge.chem.descriptors import compute_drug_likeness
from drugforge.domain.models import DrugLikeness
from tests.conftest import PYRIMETHAMINE_SMILES

RHODANINE = "O=C1CSC(=S)N1"
ACROLEIN = "C=CC=O"


def test_reference_drug_satisfies_lipinski(pyrimethamine):
    result = compute_drug_likeness(pyrimethamine)
    assert result.lipinski_violations == 0
    assert result.molecular_weight < 500
    assert result.hbd <= 5
    assert result.hba <= 10


def test_descriptors_ignore_explicit_hydrogens():
    without = compute_drug_likeness(Chem.MolFromSmiles(PYRIMETHAMINE_SMILES))
    with_hydrogens = compute_drug_likeness(
        Chem.AddHs(Chem.MolFromSmiles(PYRIMETHAMINE_SMILES))
    )
    assert without == with_hydrogens


def test_clean_molecule_passes_admet(pyrimethamine):
    result = compute_admet(pyrimethamine)
    assert result.passes_filter
    assert result.failure_reasons == []
    assert result.pains_alerts == []


def test_known_toxicophore_is_flagged():
    mol = Chem.MolFromSmiles(RHODANINE)
    if mol is None:
        pytest.skip("RDKit build cannot parse rhodanine")
    result = compute_admet(Chem.AddHs(mol))
    assert result.pains_alerts or result.brenk_alerts


def test_reactive_group_is_flagged_and_fails():
    result = compute_admet(Chem.AddHs(Chem.MolFromSmiles(ACROLEIN)))
    assert "Michael acceptor" in result.reactive_groups
    assert not result.passes_filter
    assert any("Michael" in reason for reason in result.failure_reasons)


def test_admet_carries_a_disclaimer(pyrimethamine):
    disclaimer = compute_admet(pyrimethamine).disclaimer
    assert "in-silico" in disclaimer.lower()


def test_absorption_is_classified(pyrimethamine):
    assert compute_admet(pyrimethamine).gi_absorption in {"High", "Low"}


def test_solubility_is_plausible_for_a_small_drug(pyrimethamine):
    assert -6 < predict_esol(Chem.RemoveHs(pyrimethamine)) < 2


def test_hit_requires_both_filters(drug_likeness, clean_admet):
    is_hit, reasons = evaluate_hit(drug_likeness, clean_admet)
    assert is_hit
    assert reasons == []


def test_lipinski_violations_block_a_hit(clean_admet):
    heavy = DrugLikeness(
        molecular_weight=700,
        logp=7.0,
        hbd=8,
        hba=14,
        tpsa=200.0,
        rotatable_bonds=4,
        lipinski_violations=4,
    )
    is_hit, reasons = evaluate_hit(heavy, clean_admet)
    assert not is_hit
    assert any("Lipinski" in reason for reason in reasons)


def test_flexible_molecule_fails_veber(clean_admet, drug_likeness):
    flexible = DrugLikeness(**{**drug_likeness.to_dict(), "rotatable_bonds": 15})
    is_hit, reasons = evaluate_hit(flexible, clean_admet)
    assert not is_hit
    assert any("rotatable" in reason for reason in reasons)


def test_admet_failures_are_surfaced_in_hit_reasons(drug_likeness):
    admet = compute_admet(Chem.AddHs(Chem.MolFromSmiles(ACROLEIN)))
    is_hit, reasons = evaluate_hit(drug_likeness, admet)
    assert not is_hit
    assert reasons
