"""Reference comparator — compare molecule results to the target's reference drug."""

import logging
from dataclasses import dataclass, asdict
from typing import Optional

from rdkit import Chem

from drugforge.docking import DockingResult, dock
from drugforge.druglikeness import DrugLikeness, compute_druglikeness
from drugforge.ligand_prep import prepare_ligand
from drugforge.receptor import get_receptor_pdbqt
from drugforge.targets import Target

logger = logging.getLogger(__name__)


@dataclass
class Comparison:
    """Side-by-side comparison of a single metric."""
    metric: str
    molecule_value: float
    reference_value: float
    delta: float
    ratio: float
    verdict: str  # "better" | "comparable" | "worse"

    def to_dict(self) -> dict:
        return asdict(self)


# Cache reference docking results to avoid redundant computation
_reference_cache: dict[str, tuple[DockingResult, DrugLikeness]] = {}


def _get_reference_results(target: Target) -> tuple[DockingResult, DrugLikeness]:
    """Dock the reference drug and compute its drug-likeness. Cache result."""
    if target.id in _reference_cache:
        return _reference_cache[target.id]

    logger.info(f"Docking reference drug '{target.reference.name}' for target '{target.id}'")

    # Prepare reference ligand
    ref_mol, ref_pdbqt = prepare_ligand(target.reference.smiles)

    # Get receptor
    receptor_path = get_receptor_pdbqt(target)

    # Dock reference
    ref_docking = dock(
        ligand_pdbqt=ref_pdbqt,
        receptor_pdbqt_path=receptor_path,
        box=target.box,
        exhaustiveness=8,
    )

    # Drug-likeness of reference
    ref_druglikeness = compute_druglikeness(ref_mol)

    _reference_cache[target.id] = (ref_docking, ref_druglikeness)
    return (ref_docking, ref_druglikeness)


def _verdict_for_metric(
    metric: str, molecule_value: float, reference_value: float
) -> str:
    """Determine verdict for a single metric comparison."""
    if reference_value == 0:
        return "comparable"

    ratio = abs(molecule_value / reference_value) if reference_value != 0 else 1.0

    if metric == "affinity":
        # Lower (more negative) is better
        if molecule_value <= reference_value:
            return "better"
        elif molecule_value <= reference_value * 1.5:
            return "comparable"
        else:
            return "worse"
    elif metric == "lipinski_violations":
        # Fewer is better
        if molecule_value < reference_value:
            return "better"
        elif molecule_value == reference_value:
            return "comparable"
        else:
            return "worse"
    else:
        # For descriptors, being in Lipinski range is "comparable"
        return "comparable"


def _compute_verdict_badge(affinity_ratio: float) -> str:
    """Derive overall verdict badge from affinity ratio."""
    if affinity_ratio <= 1.0:
        return "Promising"
    elif affinity_ratio <= 1.5:
        return "Comparable"
    else:
        return "Weaker"


def compare_to_reference(
    mol_docking: DockingResult,
    mol_druglikeness: DrugLikeness,
    target: Target,
) -> tuple[list[Comparison], str]:
    """
    Compare molecule results against the target's reference drug.

    Returns:
        tuple of (list of Comparison objects, verdict badge string)
    """
    ref_docking, ref_druglikeness = _get_reference_results(target)

    comparisons = []

    # Affinity comparison
    mol_aff = mol_docking.best_affinity
    ref_aff = ref_docking.best_affinity
    aff_delta = mol_aff - ref_aff
    aff_ratio = abs(mol_aff / ref_aff) if ref_aff != 0 else 1.0
    comparisons.append(Comparison(
        metric="affinity",
        molecule_value=mol_aff,
        reference_value=ref_aff,
        delta=round(aff_delta, 3),
        ratio=round(aff_ratio, 3),
        verdict=_verdict_for_metric("affinity", mol_aff, ref_aff),
    ))

    # Drug-likeness comparisons
    descriptor_pairs = [
        ("molecular_weight", mol_druglikeness.molecular_weight, ref_druglikeness.molecular_weight),
        ("logp", mol_druglikeness.logp, ref_druglikeness.logp),
        ("hbd", float(mol_druglikeness.hbd), float(ref_druglikeness.hbd)),
        ("hba", float(mol_druglikeness.hba), float(ref_druglikeness.hba)),
        ("tpsa", mol_druglikeness.tpsa, ref_druglikeness.tpsa),
        ("rotatable_bonds", float(mol_druglikeness.rotatable_bonds), float(ref_druglikeness.rotatable_bonds)),
        ("lipinski_violations", float(mol_druglikeness.lipinski_violations), float(ref_druglikeness.lipinski_violations)),
    ]

    for metric, mol_val, ref_val in descriptor_pairs:
        delta = mol_val - ref_val
        ratio = abs(mol_val / ref_val) if ref_val != 0 else 1.0
        comparisons.append(Comparison(
            metric=metric,
            molecule_value=mol_val,
            reference_value=ref_val,
            delta=round(delta, 3),
            ratio=round(ratio, 3),
            verdict=_verdict_for_metric(metric, mol_val, ref_val),
        ))

    # Overall verdict badge based on affinity ratio
    # For affinity: ratio of absolute values (both negative, so use abs)
    # molecule/reference where closer to or better than 1.0 is good
    if ref_aff != 0:
        badge_ratio = mol_aff / ref_aff  # both negative, so >1 means molecule is worse
    else:
        badge_ratio = 1.0

    verdict_badge = _compute_verdict_badge(badge_ratio)

    return (comparisons, verdict_badge)
