"""Ligand preparation — SMILES to 3D mol + PDBQT string."""

import logging

from rdkit import Chem
from rdkit.Chem import AllChem
from meeko import MoleculePreparation

from drugforge.errors import LigandPrepError

logger = logging.getLogger(__name__)


def prepare_ligand(smiles: str) -> tuple:
    """
    Prepare a ligand for docking from a SMILES string.

    Steps:
    1. Parse SMILES
    2. Add explicit hydrogens
    3. Embed in 3D (ETKDGv3)
    4. MMFF94 force-field optimization
    5. Convert to PDBQT via Meeko

    Returns:
        tuple of (RDKit Mol with 3D coords, PDBQT string)

    Raises:
        LigandPrepError on any preparation failure.
    """
    # Step 1: Parse
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        raise LigandPrepError(f"Could not parse SMILES: {smiles}")

    # Step 2: Add hydrogens
    mol = Chem.AddHs(mol)

    # Step 3: 3D embedding
    params = AllChem.ETKDGv3()
    params.randomSeed = 42
    result = AllChem.EmbedMolecule(mol, params)
    if result == -1:
        # Retry with different seed
        params.randomSeed = 123
        result = AllChem.EmbedMolecule(mol, params)
        if result == -1:
            raise LigandPrepError(
                f"3D embedding failed for SMILES: {smiles}"
            )

    # Step 4: MMFF optimization
    try:
        opt_result = AllChem.MMFFOptimizeMolecule(mol, maxIters=500)
        if opt_result == -1:
            logger.warning(f"MMFF optimization did not converge for: {smiles}")
    except Exception as e:
        logger.warning(f"MMFF optimization error (continuing): {e}")

    # Step 5: Meeko preparation → PDBQT
    try:
        preparator = MoleculePreparation()
        mol_setups = preparator.prepare(mol)
        # Get PDBQT string from the first setup
        pdbqt_lines = []
        for setup in mol_setups:
            pdbqt_string = setup.write_pdbqt_string()
            pdbqt_lines.append(pdbqt_string)
            break  # only need first conformer

        if not pdbqt_lines:
            raise LigandPrepError("Meeko produced no PDBQT output.")

        pdbqt_string = pdbqt_lines[0]
    except LigandPrepError:
        raise
    except Exception as e:
        raise LigandPrepError(
            f"Meeko PDBQT conversion failed: {type(e).__name__}: {e}"
        )

    return (mol, pdbqt_string)
