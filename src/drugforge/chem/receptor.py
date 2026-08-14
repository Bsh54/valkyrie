"""Receptor preparation.

Structures are fetched from RCSB and cached on disk. Only the PDB identifier is
committed, which keeps the repository small and the retrieval reproducible.
"""

from __future__ import annotations

import logging
import subprocess
from pathlib import Path

import requests

from drugforge.config import HTTP_TIMEOUT_S, RCSB_DOWNLOAD_URL, RECEPTOR_CACHE_DIR
from drugforge.domain.models import Target
from drugforge.errors import ReceptorError

logger = logging.getLogger(__name__)

_SOLVENT_RESIDUES = {"HOH", "DOD", "WAT"}
# Functionally essential cofactors that define the binding pocket and must be kept
# in the receptor (e.g. the CYP51 haem the azole coordinates, the PTR1 NADP the
# inhibitor stacks against). The co-crystallised inhibitor is still removed.
_COFACTOR_RESIDUES = {
    "HEM", "HEC", "HEA", "HEB", "HAS",  # haems
    "NAP", "NDP", "NAD", "NAI", "NADP",  # nicotinamide cofactors
    "FAD", "FMN",  # flavins
    "FES", "SF4",  # iron-sulfur clusters
    "PLP",  # pyridoxal phosphate
}
_OBABEL_TIMEOUT_S = 120


def get_receptor_pdbqt(target: Target) -> Path:
    """Return a cached receptor PDBQT, downloading and preparing if needed."""
    cache_dir = RECEPTOR_CACHE_DIR / target.pdb_id
    cache_dir.mkdir(parents=True, exist_ok=True)

    pdb_path = cache_dir / f"{target.pdb_id}.pdb"
    pdbqt_path = cache_dir / f"{target.pdb_id}_receptor.pdbqt"

    if pdbqt_path.exists():
        return pdbqt_path

    if not pdb_path.exists():
        download_structure(target.pdb_id, pdb_path)

    prepare_receptor(pdb_path, pdbqt_path)
    return pdbqt_path


def download_structure(pdb_id: str, destination: Path) -> None:
    """Fetch a structure from RCSB."""
    try:
        response = requests.get(
            RCSB_DOWNLOAD_URL.format(pdb_id=pdb_id), timeout=HTTP_TIMEOUT_S * 4
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise ReceptorError(f"Failed to download PDB {pdb_id}: {exc}") from exc

    destination.write_text(response.text, encoding="utf-8")
    logger.info("Downloaded %s to %s", pdb_id, destination)


_STRUCTURAL_RECORDS = {"TER", "END"}


def _keep_line(line: str) -> bool:
    tag = line[:6].strip()
    residue = line[17:20].strip()
    if tag == "ATOM":
        return residue not in _SOLVENT_RESIDUES
    if tag == "HETATM":
        return residue in _COFACTOR_RESIDUES
    return tag in _STRUCTURAL_RECORDS


def strip_solvent_and_ligands(pdb_text: str) -> str:
    """Keep the protein and essential cofactors; drop water and the inhibitor.

    Protein ATOM records are kept, functionally critical cofactors (haem, NADP,
    flavins...) are retained as HETATM, and everything else — water, ions and the
    co-crystallised inhibitor — is discarded so the pocket is empty but complete.
    """
    kept = [line for line in pdb_text.splitlines() if _keep_line(line)]

    if not any(line.startswith("ATOM") for line in kept):
        raise ReceptorError("No protein ATOM records found in the structure.")
    return "\n".join(kept) + "\n"


def prepare_receptor(pdb_path: Path, pdbqt_path: Path) -> None:
    """Clean a structure and convert it to PDBQT with Gasteiger charges."""
    try:
        pdb_text = pdb_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ReceptorError(f"Cannot read {pdb_path}: {exc}") from exc

    clean_path = pdb_path.with_name(f"{pdb_path.stem}_clean.pdb")
    clean_path.write_text(strip_solvent_and_ligands(pdb_text), encoding="utf-8")

    try:
        completed = subprocess.run(
            # No Gasteiger charges: AutoDock Vina scores by atom type, not partial
            # charge, and Gasteiger fails on cofactor metals (e.g. the haem iron),
            # which would silently drop the cofactor or empty the whole receptor.
            ["obabel", str(clean_path), "-p", "7.4", "-O", str(pdbqt_path), "-xr"],
            capture_output=True,
            text=True,
            timeout=_OBABEL_TIMEOUT_S,
            check=False,
        )
    except FileNotFoundError as exc:
        raise ReceptorError(
            "Open Babel not found. Install it with: apt install openbabel"
        ) from exc
    except subprocess.TimeoutExpired as exc:
        raise ReceptorError("Open Babel conversion timed out.") from exc

    if completed.returncode != 0 or not pdbqt_path.exists():
        raise ReceptorError(f"Open Babel conversion failed: {completed.stderr[:300]}")

    # Guard against a silent empty receptor: an empty PDBQT would let a run dock
    # against nothing and report a meaningless 0.0 affinity.
    if pdbqt_path.stat().st_size == 0 or not any(
        line.startswith(("ATOM", "HETATM"))
        for line in pdbqt_path.read_text(encoding="utf-8").splitlines()
    ):
        pdbqt_path.unlink(missing_ok=True)
        raise ReceptorError(
            f"Open Babel produced an empty receptor for {pdb_path.stem}: "
            f"{completed.stderr[:300]}"
        )

    logger.info("Prepared receptor %s", pdbqt_path)
