"""Drug-likeness descriptor calculation using RDKit."""

from dataclasses import dataclass, asdict

from rdkit import Chem
from rdkit.Chem import Descriptors, Lipinski


@dataclass
class DrugLikeness:
    """Computed drug-likeness descriptors."""
    molecular_weight: float
    logp: float
    hbd: int  # H-bond donors
    hba: int  # H-bond acceptors
    tpsa: float
    rotatable_bonds: int
    lipinski_violations: int

    def to_dict(self) -> dict:
        return asdict(self)


def compute_druglikeness(mol: Chem.Mol) -> DrugLikeness:
    """
    Compute drug-likeness descriptors from an RDKit Mol.

    Includes Lipinski's Rule of Five + Veber's rotatable bonds + TPSA.

    Args:
        mol: RDKit Mol object (can have Hs or not)

    Returns:
        DrugLikeness dataclass with all computed descriptors.
    """
    # Remove Hs for descriptor calculation (standard practice)
    mol_no_h = Chem.RemoveHs(mol)

    mw = Descriptors.MolWt(mol_no_h)
    logp = Descriptors.MolLogP(mol_no_h)
    hbd = Lipinski.NumHDonors(mol_no_h)
    hba = Lipinski.NumHAcceptors(mol_no_h)
    tpsa = Descriptors.TPSA(mol_no_h)
    rotatable_bonds = Lipinski.NumRotatableBonds(mol_no_h)

    # Count Lipinski violations (Rule of Five)
    violations = 0
    if mw > 500:
        violations += 1
    if logp > 5:
        violations += 1
    if hbd > 5:
        violations += 1
    if hba > 10:
        violations += 1

    return DrugLikeness(
        molecular_weight=round(mw, 2),
        logp=round(logp, 2),
        hbd=hbd,
        hba=hba,
        tpsa=round(tpsa, 2),
        rotatable_bonds=rotatable_bonds,
        lipinski_violations=violations,
    )
