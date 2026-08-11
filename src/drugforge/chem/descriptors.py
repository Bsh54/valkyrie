"""Drug-likeness descriptors (Lipinski rule of five plus Veber)."""

from rdkit import Chem
from rdkit.Chem import Descriptors, Lipinski

from drugforge.domain.models import DrugLikeness

MAX_MOLECULAR_WEIGHT = 500
MAX_LOGP = 5
MAX_HBD = 5
MAX_HBA = 10
MAX_ROTATABLE_BONDS = 10


def compute_drug_likeness(mol: Chem.Mol) -> DrugLikeness:
    """Compute descriptors on the heavy-atom form of a molecule."""
    heavy = Chem.RemoveHs(mol)

    molecular_weight = Descriptors.MolWt(heavy)
    logp = Descriptors.MolLogP(heavy)
    hbd = Lipinski.NumHDonors(heavy)
    hba = Lipinski.NumHAcceptors(heavy)

    violations = sum(
        (
            molecular_weight > MAX_MOLECULAR_WEIGHT,
            logp > MAX_LOGP,
            hbd > MAX_HBD,
            hba > MAX_HBA,
        )
    )

    return DrugLikeness(
        molecular_weight=round(molecular_weight, 2),
        logp=round(logp, 2),
        hbd=hbd,
        hba=hba,
        tpsa=round(Descriptors.TPSA(heavy), 2),
        rotatable_bonds=Lipinski.NumRotatableBonds(heavy),
        lipinski_violations=violations,
    )
