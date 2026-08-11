"""Receptor manager — download PDB, prepare receptor PDBQT, cache locally."""

import logging
import subprocess
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
    Prepare receptor PDBQT from a PDB file using OpenBabel.

    Steps:
    - Strip water molecules and non-protein heteroatoms
    - Convert to PDBQT format with partial charges via OpenBabel
    """
    import subprocess

    # First create a cleaned PDB (no water, no ligands)
    try:
        lines = pdb_path.read_text(encoding="utf-8").splitlines()
    except IOError as e:
        raise ReceptorError(f"Cannot read PDB file {pdb_path}: {e}")

    clean_lines = []
    has_atoms = False
    for line in lines:
        record = line[:6].strip()
        if record == "HETATM":
            continue
        if record == "ATOM":
            res_name = line[17:20].strip()
            if res_name == "HOH":
                continue
            has_atoms = True
            clean_lines.append(line)
        elif record in ("TER", "END", "HEADER", "REMARK"):
            clean_lines.append(line)

    if not has_atoms:
        raise ReceptorError(
            f"No ATOM records found in PDB file {pdb_path}"
        )

    # Write cleaned PDB
    clean_pdb_path = pdb_path.parent / f"{pdb_path.stem}_clean.pdb"
    clean_pdb_path.write_text("\n".join(clean_lines) + "\n", encoding="utf-8")

    # Convert to PDBQT using OpenBabel
    try:
        result = subprocess.run(
            ["obabel", str(clean_pdb_path), "-O", str(pdbqt_path),
             "-xr", "--partialcharge", "gasteiger"],
            capture_output=True, text=True, timeout=120
        )
        if result.returncode != 0 or not pdbqt_path.exists():
            raise ReceptorError(
                f"OpenBabel conversion failed: {result.stderr}"
            )
    except FileNotFoundError:
        raise ReceptorError(
            "OpenBabel (obabel) not found. Install with: apt install openbabel"
        )
    except subprocess.TimeoutExpired:
        raise ReceptorError("OpenBabel conversion timed out.")

    logger.info(f"Prepared receptor PDBQT: {pdbqt_path}")


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
