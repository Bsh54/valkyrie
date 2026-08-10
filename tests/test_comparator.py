"""Tests for the reference comparator."""

import pytest

from drugforge.comparator import compare_to_reference, Comparison, _compute_verdict_badge


def test_verdict_badge_promising():
    """Ratio <= 1.0 should give 'Promising'."""
    assert _compute_verdict_badge(0.8) == "Promising"
    assert _compute_verdict_badge(1.0) == "Promising"


def test_verdict_badge_comparable():
    """Ratio 1.0-1.5 should give 'Comparable'."""
    assert _compute_verdict_badge(1.2) == "Comparable"
    assert _compute_verdict_badge(1.5) == "Comparable"


def test_verdict_badge_weaker():
    """Ratio > 1.5 should give 'Weaker'."""
    assert _compute_verdict_badge(2.0) == "Weaker"
    assert _compute_verdict_badge(5.0) == "Weaker"


@pytest.mark.slow
def test_self_comparison():
    """Docking reference drug vs itself should give ratio near 1.0."""
    from drugforge.docking import dock
    from drugforge.druglikeness import compute_druglikeness
    from drugforge.ligand_prep import prepare_ligand
    from drugforge.receptor import get_receptor_pdbqt
    from drugforge.targets import get_target

    target = get_target("pf-dhfr")
    mol, ligand_pdbqt = prepare_ligand(target.reference.smiles)
    receptor_path = get_receptor_pdbqt(target)

    docking_result = dock(
        ligand_pdbqt=ligand_pdbqt,
        receptor_pdbqt_path=receptor_path,
        box=target.box,
        exhaustiveness=4,
    )
    drug_likeness = compute_druglikeness(mol)

    comparisons, verdict = compare_to_reference(
        mol_docking=docking_result,
        mol_druglikeness=drug_likeness,
        target=target,
    )

    assert len(comparisons) > 0
    assert verdict in ("Promising", "Comparable")

    # Affinity comparison should have ratio near 1.0
    aff_comp = next(c for c in comparisons if c.metric == "affinity")
    assert 0.5 < aff_comp.ratio < 2.0
