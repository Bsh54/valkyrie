"""Ligand preparation: SMILES to a 3D conformer and a PDBQT block."""

from __future__ import annotations

import logging
import subprocess

from rdkit import Chem
from rdkit.Chem import AllChem

from drugforge.errors import LigandPrepError

logger = logging.getLogger(__name__)

_EMBED_SEEDS = (42, 123, 2024)


def prepare_ligand(smiles: str) -> tuple[Chem.Mol, str]:
    """Embed a molecule in 3D, optimise it, and convert it to PDBQT.

    The molecule is first (de-)protonated to its dominant state at pH 7.4 so that
    acids, amines and similar groups carry the charge they would in the body.
    """
    smiles = _protonate_ph74(smiles)
    mol = _parse(smiles)
    mol = Chem.AddHs(mol)
    _embed(mol, smiles)
    _optimise(mol, smiles)
    return mol, _to_pdbqt(mol)


def _protonate_ph74(smiles: str) -> str:
    """Return the pH 7.4 protonation state via Open Babel, or the input unchanged.

    Never fails the pipeline: any Open Babel problem falls back to the input SMILES.
    """
    try:
        completed = subprocess.run(
            ["obabel", f"-:{smiles}", "-osmi", "-p", "7.4"],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return smiles

    candidate = (completed.stdout or "").strip().split("\t")[0].split()[0:1]
    if candidate and Chem.MolFromSmiles(candidate[0]) is not None:
        return candidate[0]
    return smiles


def _parse(smiles: str) -> Chem.Mol:
    if not smiles or not smiles.strip():
        raise LigandPrepError("No SMILES was provided.")

    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        raise LigandPrepError(f"Could not parse SMILES: {smiles}")
    if mol.GetNumAtoms() == 0:
        raise LigandPrepError(f"SMILES contains no atoms: {smiles}")
    return mol


def _embed(mol: Chem.Mol, smiles: str) -> None:
    params = AllChem.ETKDGv3()
    for seed in _EMBED_SEEDS:
        params.randomSeed = seed
        if AllChem.EmbedMolecule(mol, params) == 0:
            return
    raise LigandPrepError(f"3D embedding failed for SMILES: {smiles}")


def _optimise(mol: Chem.Mol, smiles: str) -> None:
    try:
        if AllChem.MMFFOptimizeMolecule(mol, maxIters=500) == -1:
            logger.debug("MMFF did not converge for %s", smiles)
    except Exception as exc:
        logger.debug("MMFF optimisation skipped for %s: %s", smiles, exc)


def _to_pdbqt(mol: Chem.Mol) -> str:
    from meeko import MoleculePreparation

    try:
        setups = MoleculePreparation().prepare(mol)
    except Exception as exc:
        raise LigandPrepError(
            f"Meeko preparation failed: {type(exc).__name__}: {exc}"
        ) from exc

    if not setups:
        raise LigandPrepError("Meeko produced no molecule setup.")

    try:
        from meeko import PDBQTWriterLegacy

        pdbqt, succeeded, error = PDBQTWriterLegacy.write_string(setups[0])
        if not succeeded:
            raise LigandPrepError(f"PDBQT writing failed: {error}")
    except ImportError:
        pdbqt = MoleculePreparation().write_pdbqt_string()

    if not pdbqt:
        raise LigandPrepError("Meeko produced an empty PDBQT block.")
    return pdbqt
