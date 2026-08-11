"""Build 3D molecules from raw element/coordinate lists.

PDBQT and PDB HETATM records carry coordinates but no bond table, so
connectivity is inferred from interatomic distances.
"""

import logging
from typing import Optional

from rdkit import Chem

logger = logging.getLogger(__name__)

Atom = tuple[str, float, float, float]


def build_mol_from_atoms(atoms: list[Atom]) -> Optional[Chem.Mol]:
    """Create a molecule with a 3D conformer and perceived connectivity."""
    if not atoms:
        return None

    from rdkit.Chem import rdDetermineBonds
    from rdkit.Geometry import Point3D

    mol = Chem.RWMol()
    for element, _, _, _ in atoms:
        mol.AddAtom(Chem.Atom(element))

    conformer = Chem.Conformer(mol.GetNumAtoms())
    for i, (_, x, y, z) in enumerate(atoms):
        conformer.SetAtomPosition(i, Point3D(x, y, z))
    conformer.Set3D(True)
    mol.AddConformer(conformer)

    result = mol.GetMol()
    try:
        rdDetermineBonds.DetermineConnectivity(result)
    except Exception as e:
        logger.warning(f"Bond perception failed: {e}")
        return None
    return result


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


def to_mol_block(mol: Chem.Mol) -> str:
    """Serialise a molecule to an SDF mol block, tolerating imperfect valences."""
    if mol is None:
        return ""
    Chem.SanitizeMol(mol, catchErrors=True)
    try:
        return Chem.MolToMolBlock(mol, kekulize=False)
    except Exception as e:
        logger.warning(f"Could not write mol block: {e}")
        return ""
