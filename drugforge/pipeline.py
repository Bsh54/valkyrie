"""Pipeline orchestrator — ties all docking stages together."""

import logging
from dataclasses import dataclass, field

from drugforge.comparator import Comparison, compare_to_reference
from drugforge.docking import DockingResult, dock
from drugforge.druglikeness import DrugLikeness, compute_druglikeness
from drugforge.errors import (
    DrugForgeError,
    PipelineError,
    ValidationError,
)
from drugforge.ligand_prep import prepare_ligand
from drugforge.receptor import get_receptor_pdbqt
from drugforge.targets import get_target
from drugforge.validator import validate_molecule

logger = logging.getLogger(__name__)


@dataclass
class PipelineResult:
    """Complete result of a docking pipeline run."""
    molecule_smiles: str
    target_id: str
    affinity_kcal_mol: float
    all_affinities: list[float]
    pose_sdf: str
    pose_pdbqt: str
    drug_likeness: DrugLikeness
    comparisons: list[Comparison]
    verdict: str

    def to_dict(self) -> dict:
        return {
            "molecule_smiles": self.molecule_smiles,
            "target_id": self.target_id,
            "affinity_kcal_mol": self.affinity_kcal_mol,
            "all_affinities": self.all_affinities,
            "pose_sdf": self.pose_sdf,
            "pose_pdbqt": self.pose_pdbqt,
            "drug_likeness": self.drug_likeness.to_dict(),
            "comparisons": [c.to_dict() for c in self.comparisons],
            "verdict": self.verdict,
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

    return PipelineResult(
        molecule_smiles=smiles,
        target_id=target_id,
        affinity_kcal_mol=docking_result.best_affinity,
        all_affinities=docking_result.all_affinities,
        pose_sdf=docking_result.best_pose_sdf,
        pose_pdbqt=docking_result.best_pose_pdbqt,
        drug_likeness=drug_likeness,
        comparisons=comparisons,
        verdict=verdict,
    )
