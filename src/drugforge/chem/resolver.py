"""Resolve a user-supplied molecule to canonical SMILES.

Order: curated local table, then direct SMILES parsing, then PubChem. The local
table wins so offline use and reproducibility do not depend on a remote service.
"""

from __future__ import annotations

import json
import logging
from functools import lru_cache
from urllib.parse import quote

import requests
from rdkit import Chem

from drugforge.config import COMPOUNDS_PATH, HTTP_TIMEOUT_S, PUBCHEM_SMILES_URL
from drugforge.errors import ResolutionError

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _local_table() -> dict[str, str]:
    """Curated names merged with the ethnobotanical registry."""
    table: dict[str, str] = {}

    if COMPOUNDS_PATH.exists():
        try:
            raw = json.loads(COMPOUNDS_PATH.read_text(encoding="utf-8"))
            table.update({k.lower().strip(): v for k, v in raw.items()})
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Could not read %s: %s", COMPOUNDS_PATH.name, exc)

    from drugforge.content.library import list_compounds

    for entry in list_compounds():
        smiles = entry.get("smiles")
        if not smiles:
            continue
        for key in (entry.get("id"), entry.get("compound_name")):
            if key:
                table.setdefault(key.lower().strip(), smiles)

    return table


def canonicalize(smiles: str) -> str | None:
    """Return canonical SMILES, or None when the input is not a structure."""
    mol = Chem.MolFromSmiles(smiles)
    if mol is None or mol.GetNumAtoms() == 0:
        return None
    return Chem.MolToSmiles(mol)


def _lookup_pubchem(name: str) -> str | None:
    url = PUBCHEM_SMILES_URL.format(name=quote(name))
    try:
        response = requests.get(url, timeout=HTTP_TIMEOUT_S)
        if response.status_code != 200:
            return None
        properties = response.json().get("PropertyTable", {}).get("Properties", [])
        return properties[0].get("CanonicalSMILES") if properties else None
    except (requests.RequestException, ValueError, KeyError, IndexError) as exc:
        logger.debug("PubChem lookup failed for %r: %s", name, exc)
        return None


def resolve(molecule_input: str) -> str:
    """Resolve a name or SMILES to canonical SMILES."""
    if not molecule_input or not molecule_input.strip():
        raise ResolutionError("No molecule was provided.")

    query = molecule_input.strip()

    local = _local_table().get(query.lower())
    if local:
        canonical = canonicalize(local)
        if canonical:
            return canonical

    canonical = canonicalize(query)
    if canonical:
        return canonical

    remote = _lookup_pubchem(query)
    if remote:
        canonical = canonicalize(remote)
        if canonical:
            return canonical

    raise ResolutionError(
        f"Could not resolve '{query}' as a compound name or SMILES string."
    )
