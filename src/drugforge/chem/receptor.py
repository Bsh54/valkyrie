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


def _is_protein_atom(line: str) -> bool:
    return line[:6].strip() == "ATOM" and line[17:20].strip() not in _SOLVENT_RESIDUES


def strip_solvent_and_ligands(pdb_text: str) -> str:
    """Keep protein ATOM records only, dropping water and heteroatoms."""
    kept = [
        line
        for line in pdb_text.splitlines()
        if _is_protein_atom(line) or line[:6].strip() in _STRUCTURAL_RECORDS
    ]

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
            [
                "obabel", str(clean_path), "-O", str(pdbqt_path),
                "-xr", "--partialcharge", "gasteiger",
            ],
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

    logger.info("Prepared receptor %s", pdbqt_path)
