"""Pose conversion and consensus scoring, without invoking Vina."""

from rdkit import Chem

from drugforge.docking.consensus import compute_consensus
from drugforge.docking.engine import (
    first_model_only,
    parse_first_model,
    pose_to_mol_block,
)

# Ethanol as Vina writes it: columns 78-79 hold AutoDock types, not elements.
POSE_PDBQT = """MODEL 1
ATOM      1  C   UNL     1      -0.888   0.167  -0.027  1.00  0.00     0.034 C
ATOM      2  C   UNL     1       0.466  -0.512  -0.037  1.00  0.00     0.152 C
ATOM      3  O   UNL     1       1.431   0.512   0.038  1.00  0.00    -0.397 OA
ENDMDL
MODEL 2
ATOM      1  C   UNL     1      -1.888   0.167  -0.027  1.00  0.00     0.034 C
ENDMDL
"""

AROMATIC_POSE = """MODEL 1
ATOM      1  C   UNL     1       0.000   1.396   0.000  1.00  0.00     0.000 A
ATOM      2  C   UNL     1       1.209   0.698   0.000  1.00  0.00     0.000 A
ATOM      3  C   UNL     1       1.209  -0.698   0.000  1.00  0.00     0.000 A
ATOM      4  C   UNL     1       0.000  -1.396   0.000  1.00  0.00     0.000 A
ATOM      5  C   UNL     1      -1.209  -0.698   0.000  1.00  0.00     0.000 A
ATOM      6  C   UNL     1      -1.209   0.698   0.000  1.00  0.00     0.000 A
ENDMDL
"""


def test_autodock_types_map_to_real_elements():
    atoms = parse_first_model(POSE_PDBQT)
    assert [atom[0] for atom in atoms] == ["C", "C", "O"]


def test_only_the_first_model_is_parsed():
    assert len(parse_first_model(POSE_PDBQT)) == 3


def test_first_model_only_drops_later_poses():
    single = first_model_only(POSE_PDBQT)
    assert single.count("ATOM") == 3
    assert "MODEL" not in single


def test_pose_converts_to_a_parsable_mol_block():
    block = pose_to_mol_block(POSE_PDBQT)
    mol = Chem.MolFromMolBlock(block, sanitize=False)
    assert mol is not None
    assert mol.GetNumAtoms() == 3
    assert mol.GetNumBonds() == 2
    assert mol.GetConformer().Is3D()


def test_aromatic_carbon_type_is_not_treated_as_an_element():
    mol = Chem.MolFromMolBlock(pose_to_mol_block(AROMATIC_POSE), sanitize=False)
    assert mol is not None
    assert {atom.GetSymbol() for atom in mol.GetAtoms()} == {"C"}
    assert mol.GetNumBonds() == 6


def test_template_recovers_bond_orders():
    block = pose_to_mol_block(POSE_PDBQT, template_smiles="CCO")
    mol = Chem.MolFromMolBlock(block, sanitize=False)
    assert mol is not None
    assert mol.GetNumAtoms() == 3


def test_empty_input_yields_no_block():
    assert pose_to_mol_block("") == ""
    assert pose_to_mol_block("REMARK nothing here") == ""


def test_consensus_matches_the_reference_when_scores_match():
    result = compute_consensus(-8.0, -7.0, -8.0, -7.0)
    assert abs(result.consensus_score - 1.0) < 0.01


def test_stronger_binding_scores_above_the_reference():
    assert compute_consensus(-10.0, -9.0, -8.0, -7.0).consensus_score > 1.0


def test_weaker_binding_scores_below_the_reference():
    assert compute_consensus(-4.0, -3.0, -8.0, -7.0).consensus_score < 1.0


def test_consensus_is_deterministic():
    first = compute_consensus(-8.3, -7.1, -7.9, -6.8)
    second = compute_consensus(-8.3, -7.1, -7.9, -6.8)
    assert first.consensus_score == second.consensus_score


def test_zero_reference_does_not_divide_by_zero():
    result = compute_consensus(-8.0, -7.0, 0.0, 0.0)
    assert result.consensus_score == 1.0


def test_weighting_favours_vina():
    vina_only = compute_consensus(-16.0, -7.0, -8.0, -7.0).consensus_score
    vinardo_only = compute_consensus(-8.0, -14.0, -8.0, -7.0).consensus_score
    assert vina_only > vinardo_only
