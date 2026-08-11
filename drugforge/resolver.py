"""Molecule resolver — converts user input (name or SMILES) to canonical SMILES."""

import json
import logging
from pathlib import Path

import requests
from rdkit import Chem

from drugforge.config import COMPOUNDS_PATH
from drugforge.errors import ResolutionError

logger = logging.getLogger(__name__)

# Load local compound lookup table
_COMPOUND_LOOKUP: dict[str, str] = {}


def _load_compounds() -> None:
    """Build the local name lookup from the curated table and the plant registry."""
    global _COMPOUND_LOOKUP
    if _COMPOUND_LOOKUP:
        return

    lookup: dict[str, str] = {}
    try:
        with open(COMPOUNDS_PATH, "r", encoding="utf-8") as f:
            lookup.update({k.lower().strip(): v for k, v in json.load(f).items()})
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.warning(f"Could not load compounds table: {e}")

    try:
        from drugforge.library import get_compounds

        for entry in get_compounds():
            smiles = entry.get("smiles")
            if not smiles:
                continue
            for key in (entry.get("id"), entry.get("compound_name")):
                if key:
                    lookup.setdefault(key.lower().strip(), smiles)
    except Exception as e:
        logger.warning(f"Could not load ethnobotanical registry: {e}")

    _COMPOUND_LOOKUP = lookup


def _canonicalize(smiles: str) -> str | None:
    """Return canonical SMILES if valid, else None."""
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None
    return Chem.MolToSmiles(mol)


def _lookup_local(name: str) -> str | None:
    """Check local curated compound table."""
    _load_compounds()
    return _COMPOUND_LOOKUP.get(name.lower().strip())


def _lookup_pubchem(name: str) -> str | None:
    """Query PubChem REST API for canonical SMILES by compound name."""
    url = (
        f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/"
        f"{requests.utils.quote(name)}/property/CanonicalSMILES/JSON"
    )
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            props = data.get("PropertyTable", {}).get("Properties", [])
            if props:
                return props[0].get("CanonicalSMILES")
    except (requests.RequestException, ValueError, KeyError) as e:
        logger.debug(f"PubChem lookup failed for '{name}': {e}")
    return None


def resolve(molecule_input: str) -> str:
    """
    Resolve user input to canonical SMILES.

    Resolution order:
    1. Local curated lookup (case-insensitive)
    2. Direct SMILES parse (RDKit)
    3. PubChem REST API fallback
    4. Raise ResolutionError

    Returns canonical SMILES string.
    """
    if not molecule_input or not molecule_input.strip():
        raise ResolutionError("Empty molecule input.")

    cleaned = molecule_input.strip()

    # Step 1: Local lookup
    local_smiles = _lookup_local(cleaned)
    if local_smiles:
        canonical = _canonicalize(local_smiles)
        if canonical:
            return canonical

    # Step 2: Try parsing as SMILES directly
    canonical = _canonicalize(cleaned)
    if canonical:
        return canonical

    # Step 3: PubChem fallback
    pubchem_smiles = _lookup_pubchem(cleaned)
    if pubchem_smiles:
        canonical = _canonicalize(pubchem_smiles)
        if canonical:
            return canonical

    raise ResolutionError(
        f"Could not resolve '{cleaned}' as a compound name or SMILES string."
    )
