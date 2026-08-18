"""Screening pipeline.

Stages run in order and each is wrapped so a failure reports which stage broke.
Optional stages (rescoring, AI services) degrade instead of aborting the run:
losing an AI opinion must never cost the user a physics result.
"""

from __future__ import annotations

import logging

from valkyrie.ai import boltz, explainer
from valkyrie.chem.admet import compute_admet, evaluate_hit
from valkyrie.chem.descriptors import compute_drug_likeness
from valkyrie.chem.ligand import prepare_ligand
from valkyrie.chem.receptor import get_receptor_pdbqt
from valkyrie.chem.validator import validate_molecule
from valkyrie.config import DEFAULT_EXHAUSTIVENESS
from valkyrie.docking.consensus import compute_consensus
from valkyrie.docking.engine import dock
from valkyrie.docking.rescoring import rescore_vinardo
from valkyrie.domain.models import ScreeningResult
from valkyrie.domain.targets import get_target
from valkyrie.errors import ValkyrieError, PipelineError
from valkyrie.pipeline.comparison import (
    build_comparisons,
    overall_verdict,
    reference_baseline,
)

logger = logging.getLogger(__name__)


def _stage(name: str, action):
    """Run a required stage, tagging any domain failure with its stage."""
    try:
        return action()
    except ValkyrieError as exc:
        raise PipelineError(stage=name, cause=exc) from exc
    except Exception as exc:
        raise PipelineError(stage=name, cause=ValkyrieError(str(exc))) from exc


def run_screening(
    molecule_input: str,
    target_id: str,
    exhaustiveness: int = DEFAULT_EXHAUSTIVENESS,
    with_explanation: bool = True,
) -> ScreeningResult:
    """Screen one molecule against one target."""
    smiles = _stage("validate", lambda: validate_molecule(molecule_input))
    target = _stage("target_lookup", lambda: get_target(target_id))
    mol, ligand_pdbqt = _stage("ligand_preparation", lambda: prepare_ligand(smiles))
    receptor_path = _stage("receptor_preparation", lambda: get_receptor_pdbqt(target))

    docking = _stage(
        "docking",
        lambda: dock(
            ligand_pdbqt=ligand_pdbqt,
            receptor_pdbqt_path=receptor_path,
            box=target.box,
            exhaustiveness=exhaustiveness,
            template_smiles=smiles,
        ),
    )

    vinardo = _rescore(docking.best_pose_pdbqt, receptor_path, target, docking.best_affinity)
    baseline = _stage(
        "reference_baseline",
        lambda: reference_baseline(target, receptor_path, exhaustiveness),
    )

    consensus = compute_consensus(
        vina_score=docking.best_affinity,
        vinardo_score=vinardo,
        reference_vina=baseline.affinity,
        reference_vinardo=baseline.vinardo,
    )

    drug_likeness = _stage("drug_likeness", lambda: compute_drug_likeness(mol))
    admet = _stage("admet", lambda: compute_admet(mol))
    is_hit, hit_reasons = evaluate_hit(drug_likeness, admet)

    result = ScreeningResult(
        molecule_smiles=smiles,
        target_id=target.id,
        affinity_kcal_mol=docking.best_affinity,
        vinardo_score=vinardo,
        consensus_score=consensus.consensus_score,
        all_affinities=docking.all_affinities,
        pose_sdf=docking.best_pose_sdf,
        pose_pdbqt=docking.best_pose_pdbqt,
        drug_likeness=drug_likeness,
        admet=admet,
        is_hit=is_hit,
        hit_failure_reasons=hit_reasons,
        comparisons=build_comparisons(docking.best_affinity, drug_likeness, baseline),
        verdict=overall_verdict(consensus.consensus_score, is_hit),
    )

    result.boltz = _confirm_with_boltz(result, target)
    if with_explanation:
        result.explanation = _explain(result, target)
    return result


def _rescore(pose_pdbqt: str, receptor_path, target, fallback: float) -> float:
    """Rescore with Vinardo, falling back to the Vina score on failure."""
    try:
        return rescore_vinardo(pose_pdbqt, receptor_path, target.box)
    except ValkyrieError as exc:
        logger.warning("Vinardo rescoring unavailable, reusing Vina score: %s", exc.detail)
        return fallback


def _confirm_with_boltz(result: ScreeningResult, target):
    if not boltz.should_run(rank=1, passed_admet=result.is_hit):
        return None
    return boltz.confirm_binding(
        smiles=result.molecule_smiles,
        target_pdb_id=target.pdb_id,
        pose_sdf=result.pose_sdf,
    )


def _explain(result: ScreeningResult, target):
    if not explainer.is_available():
        return None
    try:
        return explainer.explain(result.to_dict(), target)
    except Exception as exc:
        logger.warning("Explanation stage failed: %s", exc)
        return None
