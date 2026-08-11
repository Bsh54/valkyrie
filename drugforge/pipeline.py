"""Pipeline orchestrator — ties all docking stages together."""

import logging
from dataclasses import dataclass, field
from typing import Optional

from drugforge.comparator import Comparison, compare_to_reference
from drugforge.consensus import ConsensusResult, compute_consensus
from drugforge.docking import DockingResult, dock
from drugforge.druglikeness import DrugLikeness, compute_druglikeness
from drugforge.admet import ADMETResult, compute_admet, is_hit
from drugforge.boltz import BoltzResult, call_boltz_api, should_run_boltz
from drugforge.errors import (
    DrugForgeError,
    PipelineError,
    ValidationError,
)
from drugforge.ligand_prep import prepare_ligand
from drugforge.receptor import get_receptor_pdbqt
from drugforge.rescoring import rescore_vinardo
from drugforge.targets import get_target
from drugforge.validator import validate_molecule

logger = logging.getLogger(__name__)


@dataclass
class PipelineResult:
    """Complete result of a docking pipeline run."""
    molecule_smiles: str
    target_id: str
    affinity_kcal_mol: float
    vinardo_score: float
    consensus_score: float
    all_affinities: list[float]
    pose_sdf: str
    pose_pdbqt: str
    drug_likeness: DrugLikeness
    admet: ADMETResult
    is_hit: bool
    hit_failure_reasons: list[str]
    comparisons: list[Comparison]
    verdict: str
    boltz: Optional[BoltzResult] = None

    def to_dict(self) -> dict:
        return {
            "molecule_smiles": self.molecule_smiles,
            "target_id": self.target_id,
            "affinity_kcal_mol": self.affinity_kcal_mol,
            "vinardo_score": self.vinardo_score,
            "consensus_score": self.consensus_score,
            "all_affinities": self.all_affinities,
            "pose_sdf": self.pose_sdf,
            "pose_pdbqt": self.pose_pdbqt,
            "drug_likeness": self.drug_likeness.to_dict(),
            "admet": self.admet.to_dict(),
            "is_hit": self.is_hit,
            "hit_failure_reasons": self.hit_failure_reasons,
            "comparisons": [c.to_dict() for c in self.comparisons],
            "verdict": self.verdict,
            "boltz": self.boltz.to_dict() if self.boltz else None,
        }


def run_docking_pipeline(
    molecule_input: str,
    target_id: str,
    exhaustiveness: int = 8,
) -> PipelineResult:
    """
    Execute the full docking pipeline synchronously.

    Stages:
    1. Validate & resolve molecule input → canonical SMILES
    2. Prepare ligand (3D embed + PDBQT)
    3. Prepare/fetch receptor PDBQT
    4. Dock with Vina
    5. Compute drug-likeness
    6. Compare to reference drug
    7. Return assembled result

    Raises:
        PipelineError wrapping the stage-specific error on failure.
    """
    # Stage 1: Validate
    try:
        smiles = validate_molecule(molecule_input)
    except DrugForgeError as e:
        raise PipelineError(stage="validate", cause=e)

    # Stage 2: Get target
    try:
        target = get_target(target_id)
    except DrugForgeError as e:
        raise PipelineError(stage="target_lookup", cause=e)

    # Stage 3: Prepare ligand
    try:
        mol, ligand_pdbqt = prepare_ligand(smiles)
    except DrugForgeError as e:
        raise PipelineError(stage="ligand_prep", cause=e)

    # Stage 4: Prepare receptor
    try:
        receptor_path = get_receptor_pdbqt(target)
    except DrugForgeError as e:
        raise PipelineError(stage="receptor_prep", cause=e)

    # Stage 5: Dock
    try:
        docking_result = dock(
            ligand_pdbqt=ligand_pdbqt,
            receptor_pdbqt_path=receptor_path,
            box=target.box,
            exhaustiveness=exhaustiveness,
        )
    except DrugForgeError as e:
        raise PipelineError(stage="docking", cause=e)

    # Stage 5b: Vinardo rescoring
    try:
        vinardo_score = rescore_vinardo(
            ligand_pdbqt=docking_result.best_pose_pdbqt,
            receptor_pdbqt_path=receptor_path,
            box=target.box,
        )
    except DrugForgeError as e:
        # Non-fatal: if rescoring fails, use Vina score as fallback
        logger.warning(f"Vinardo rescoring failed, using Vina score: {e}")
        vinardo_score = docking_result.best_affinity

    # Stage 5c: Get reference scores for consensus normalization
    try:
        from drugforge.comparator import _get_reference_results
        ref_docking, _ = _get_reference_results(target)
        ref_vina = ref_docking.best_affinity
        # Rescore reference pose with Vinardo
        ref_vinardo = rescore_vinardo(
            ligand_pdbqt=ref_docking.best_pose_pdbqt,
            receptor_pdbqt_path=receptor_path,
            box=target.box,
        )
    except Exception:
        ref_vina = docking_result.best_affinity
        ref_vinardo = vinardo_score

    # Stage 5d: Compute consensus
    consensus_result = compute_consensus(
        vina_score=docking_result.best_affinity,
        vinardo_score=vinardo_score,
        ref_vina=ref_vina,
        ref_vinardo=ref_vinardo,
    )

    # Stage 6: Drug-likeness
    try:
        drug_likeness = compute_druglikeness(mol)
    except Exception as e:
        from drugforge.errors import DrugForgeError as DFE

        cause = DFE(f"Drug-likeness computation failed: {e}")
        raise PipelineError(stage="druglikeness", cause=cause)

    # Stage 7: Compare to reference
    try:
        comparisons, verdict = compare_to_reference(
            mol_docking=docking_result,
            mol_druglikeness=drug_likeness,
            target=target,
        )
    except DrugForgeError as e:
        raise PipelineError(stage="comparison", cause=e)
    except Exception as e:
        from drugforge.errors import DrugForgeError as DFE

        cause = DFE(f"Comparison failed: {e}")
        raise PipelineError(stage="comparison", cause=cause)

    # Stage 8: ADMET filter
    try:
        admet_result = compute_admet(mol)
        hit, hit_failure_reasons = is_hit(drug_likeness, admet_result)
    except Exception as e:
        logger.warning(f"ADMET computation failed (non-fatal): {e}")
        admet_result = ADMETResult(
            esol_logs=0.0, gi_absorption="Unknown",
            pains_alerts=[], brenk_alerts=[], nih_alerts=[],
            reactive_groups=[], passes_filter=True, failure_reasons=[],
        )
        hit, hit_failure_reasons = True, []

    # Stage 9: Boltz-2 AI confirmation (optional, top-N only)
    boltz_result = None
    if should_run_boltz(rank=1, passed_admet=hit):
        boltz_result = call_boltz_api(
            smiles=smiles,
            target_pdb_id=target.pdb_id,
            pose_sdf=docking_result.best_pose_sdf,
        )

    return PipelineResult(
        molecule_smiles=smiles,
        target_id=target_id,
        affinity_kcal_mol=docking_result.best_affinity,
        vinardo_score=vinardo_score,
        consensus_score=consensus_result.consensus_score,
        all_affinities=docking_result.all_affinities,
        pose_sdf=docking_result.best_pose_sdf,
        pose_pdbqt=docking_result.best_pose_pdbqt,
        drug_likeness=drug_likeness,
        admet=admet_result,
        is_hit=hit,
        hit_failure_reasons=hit_failure_reasons,
        comparisons=comparisons,
        verdict=verdict,
        boltz=boltz_result,
    )
