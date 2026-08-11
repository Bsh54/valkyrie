"""Comparison of a candidate against the target's reference drug.

Every reported number is relative to a known active, so a score is never shown
without the baseline that makes it interpretable.
"""

from __future__ import annotations

import logging
from pathlib import Path

from drugforge.chem.descriptors import compute_drug_likeness
from drugforge.chem.ligand import prepare_ligand
from drugforge.docking.engine import dock
from drugforge.docking.rescoring import rescore_vinardo
from drugforge.domain.models import Comparison, DockingResult, DrugLikeness, Target

logger = logging.getLogger(__name__)

PROMISING_RATIO = 1.0
COMPARABLE_RATIO = 0.8

_LOWER_IS_BETTER = {"affinity", "lipinski_violations"}

_reference_cache: dict[str, ReferenceBaseline] = {}


class ReferenceBaseline:
    """Docked reference drug for one target, computed once per process."""

    def __init__(
        self, docking: DockingResult, vinardo: float, drug_likeness: DrugLikeness
    ):
        self.docking = docking
        self.vinardo = vinardo
        self.drug_likeness = drug_likeness

    @property
    def affinity(self) -> float:
        return self.docking.best_affinity


def reference_baseline(
    target: Target, receptor_path: Path, exhaustiveness: int
) -> ReferenceBaseline:
    """Dock the reference drug, reusing the result for later comparisons."""
    cached = _reference_cache.get(target.id)
    if cached is not None:
        return cached

    logger.info("Docking reference drug %s for %s", target.reference.name, target.id)
    mol, ligand_pdbqt = prepare_ligand(target.reference.smiles)
    docking = dock(
        ligand_pdbqt=ligand_pdbqt,
        receptor_pdbqt_path=receptor_path,
        box=target.box,
        exhaustiveness=exhaustiveness,
        template_smiles=target.reference.smiles,
    )
    vinardo = rescore_vinardo(docking.best_pose_pdbqt, receptor_path, target.box)

    baseline = ReferenceBaseline(docking, vinardo, compute_drug_likeness(mol))
    _reference_cache[target.id] = baseline
    return baseline


def clear_reference_cache() -> None:
    _reference_cache.clear()


def _verdict_for(metric: str, value: float, reference: float) -> str:
    if metric not in _LOWER_IS_BETTER:
        return "comparable"
    if value < reference:
        return "better"
    if value == reference:
        return "comparable"
    return "worse"


def _comparison(metric: str, value: float, reference: float) -> Comparison:
    return Comparison(
        metric=metric,
        molecule_value=value,
        reference_value=reference,
        delta=round(value - reference, 3),
        ratio=round(abs(value / reference), 3) if reference else 1.0,
        verdict=_verdict_for(metric, value, reference),
    )


def overall_verdict(consensus_score: float, is_hit: bool) -> str:
    """Translate the consensus ratio into a single user-facing label."""
    if not is_hit:
        return "Discard"
    if consensus_score >= PROMISING_RATIO:
        return "Promising"
    if consensus_score >= COMPARABLE_RATIO:
        return "Comparable"
    return "Weak"


def build_comparisons(
    affinity: float, drug_likeness: DrugLikeness, baseline: ReferenceBaseline
) -> list[Comparison]:
    """Compare affinity and every descriptor against the reference drug."""
    reference = baseline.drug_likeness
    pairs: list[tuple[str, float, float]] = [
        ("affinity", affinity, baseline.affinity),
        ("molecular_weight", drug_likeness.molecular_weight, reference.molecular_weight),
        ("logp", drug_likeness.logp, reference.logp),
        ("hbd", float(drug_likeness.hbd), float(reference.hbd)),
        ("hba", float(drug_likeness.hba), float(reference.hba)),
        ("tpsa", drug_likeness.tpsa, reference.tpsa),
        (
            "rotatable_bonds",
            float(drug_likeness.rotatable_bonds),
            float(reference.rotatable_bonds),
        ),
        (
            "lipinski_violations",
            float(drug_likeness.lipinski_violations),
            float(reference.lipinski_violations),
        ),
    ]
    return [_comparison(metric, value, ref) for metric, value, ref in pairs]
