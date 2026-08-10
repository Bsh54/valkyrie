"""Receptor manager — download PDB, prepare receptor PDBQT, cache locally."""

import logging
from pathlib import Path

import requests

from drugforge.config import RECEPTOR_CACHE_DIR
from drugforge.errors import ReceptorError
from drugforge.targets import Target

logger = logging.getLogger(__name__)


def _download_pdb(pdb_id: str, dest: Path) -> None:
    """Download a PDB file from RCSB."""
    url = f"https://files.rcsb.org/download/{pdb_id}.pdb"
    try:
        resp = requests.get(url, timeout=60)
        resp.raise_for_status()
        dest.write_text(resp.text, encoding="utf-8")
        logger.info(f"Downloaded PDB {pdb_id} to {dest}")
    except requests.RequestException as e:
        raise ReceptorError(
            f"Failed to download PDB {pdb_id} from RCSB: {e}"
        )


def _prepare_receptor_pdbqt(pdb_path: Path, pdbqt_path: Path) -> None:
    """
    Prepare receptor PDBQT from a PDB file.

    Steps:
    - Strip water molecules (HOH)
    - Strip non-protein heteroatoms (ligands, ions)
    - Keep only ATOM records + polar hydrogens info
    - Write as PDBQT (simplified: ATOM lines with charge/type columns)

    Note: For production use, ADFR Suite's prepare_receptor is preferred.
    This is a lightweight fallback that produces a usable PDBQT.
    """
    try:
        lines = pdb_path.read_text(encoding="utf-8").splitlines()
    except IOError as e:
        raise ReceptorError(f"Cannot read PDB file {pdb_path}: {e}")

    pdbqt_lines = []
    for line in lines:
        record = line[:6].strip()

        # Skip water and heteroatoms
        if record == "HETATM":
            continue
        if record == "ATOM":
            res_name = line[17:20].strip()
            if res_name == "HOH":
                continue
            # Convert ATOM line to PDBQT format
            # PDBQT adds partial charge (0.0) and atom type at end
            atom_name = line[12:16].strip()

            # Determine AutoDock atom type from element
            element = line[76:78].strip() if len(line) >= 78 else atom_name[0]
            ad_type = _get_autodock_type(element, atom_name)

            # Format: original PDB line + charge + type
            pdbqt_line = f"{line[:54]}  0.00  0.000    {ad_type:>2s}"
            pdbqt_lines.append(pdbqt_line)
        elif record in ("TER", "END"):
            pdbqt_lines.append(line.rstrip())

    if not pdbqt_lines:
        raise ReceptorError(
            f"No ATOM records found in PDB file {pdb_path}"
        )

    pdbqt_path.write_text("\n".join(pdbqt_lines) + "\n", encoding="utf-8")
    logger.info(f"Prepared receptor PDBQT: {pdbqt_path}")


def _get_autodock_type(element: str, atom_name: str) -> str:
    """Map element to AutoDock atom type."""
    element = element.upper().strip()
    type_map = {
        "C": "C",
        "N": "N",
        "O": "OA",
        "S": "SA",
        "H": "HD",
        "F": "F",
        "P": "P",
        "CL": "Cl",
        "BR": "Br",
        "I": "I",
        "FE": "Fe",
        "ZN": "Zn",
        "MG": "Mg",
        "CA": "Ca",
        "MN": "Mn",
    }
    # Check for polar hydrogens (bonded to N or O)
    if element == "H" and atom_name.startswith("H"):
        return "HD"
    return type_map.get(element, "C")


def get_receptor_pdbqt(target: Target) -> Path:
    """
    Ensure the receptor PDBQT for a target is available.

    Downloads from RCSB and prepares if not cached.
    Returns the path to the receptor PDBQT file.
    """
    cache_dir = RECEPTOR_CACHE_DIR / target.pdb_id
    cache_dir.mkdir(parents=True, exist_ok=True)

    pdb_path = cache_dir / f"{target.pdb_id}.pdb"
    pdbqt_path = cache_dir / f"{target.pdb_id}_receptor.pdbqt"

    # Return cached version if available
    if pdbqt_path.exists():
        return pdbqt_path

    # Download PDB if needed
    if not pdb_path.exists():
        _download_pdb(target.pdb_id, pdb_path)

    # Prepare PDBQT
    _prepare_receptor_pdbqt(pdb_path, pdbqt_path)

    return pdbqt_path
