"""Rebuild molecules from bare element and coordinate lists.

PDB and PDBQT records carry coordinates but no bond table, so connectivity is
perceived from interatomic distances.
"""

from __future__ import annotations

import logging

from rdkit import Chem

logger = logging.getLogger(__name__)

Atom = tuple[str, float, float, float]


def build_mol_from_atoms(atoms: list[Atom]) -> Chem.Mol | None:
    """Create a molecule with a 3D conformer and perceived connectivity."""
    if not atoms:
        return None

    from rdkit.Chem import rdDetermineBonds
    from rdkit.Geometry import Point3D

    editable = Chem.RWMol()
    for element, _, _, _ in atoms:
        editable.AddAtom(Chem.Atom(element))

    conformer = Chem.Conformer(editable.GetNumAtoms())
    for index, (_, x, y, z) in enumerate(atoms):
        conformer.SetAtomPosition(index, Point3D(x, y, z))
    conformer.Set3D(True)
    editable.AddConformer(conformer)

    mol = editable.GetMol()
    try:
        rdDetermineBonds.DetermineConnectivity(mol)
    except Exception as exc:
        logger.warning("Bond perception failed: %s", exc)
        return None
    return mol


def apply_template(mol: Chem.Mol, template_smiles: str) -> Chem.Mol:
    """Recover bond orders from a SMILES template when heavy atoms match."""
    from rdkit.Chem import AllChem

    template = Chem.MolFromSmiles(template_smiles)
    if template is None:
        return mol
    try:
        heavy = Chem.RemoveHs(mol, sanitize=False)
        if heavy.GetNumAtoms() != template.GetNumAtoms():
            return mol
        return AllChem.AssignBondOrdersFromTemplate(template, heavy)
    except Exception:
        return mol


def to_mol_block(mol: Chem.Mol | None) -> str:
    """Serialise to an SDF mol block, tolerating imperfect valences."""
    if mol is None:
        return ""
    Chem.SanitizeMol(mol, catchErrors=True)
    try:
        return Chem.MolToMolBlock(mol, kekulize=False)
    except Exception as exc:
        logger.warning("Could not write mol block: %s", exc)
        return ""
