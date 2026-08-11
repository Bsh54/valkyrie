"""ADMET proxies and structural alerts, computed locally with RDKit.

Reported values are rule-based estimates, never measured toxicology.
"""

from __future__ import annotations

import logging
from functools import lru_cache

from rdkit import Chem
from rdkit.Chem import Descriptors, FilterCatalog, rdMolDescriptors

from drugforge.chem.descriptors import MAX_ROTATABLE_BONDS
from drugforge.domain.models import ADMETResult, DrugLikeness

logger = logging.getLogger(__name__)

MIN_ESOL_LOGS = -6.0
MAX_TPSA_FOR_ABSORPTION = 140.0
LOGP_ABSORPTION_RANGE = (-2.0, 5.88)
MAX_LIPINSKI_VIOLATIONS = 1

_REACTIVE_GROUPS = {
    "Michael acceptor": "[CX3]=[CX3][CX3]=[O,N]",
    "Alkyl halide": "[CX4][F,Cl,Br,I]",
    "Acyl halide": "[CX3](=[OX1])[F,Cl,Br,I]",
    "Sulfonyl halide": "[SX4](=[OX1])(=[OX1])[F,Cl,Br,I]",
    "Acid anhydride": "[CX3](=[OX1])[OX2][CX3](=[OX1])",
    "Epoxide": "C1OC1",
    "Aziridine": "C1NC1",
}

_CATALOG_NAMES = {
    "PAINS": ("PAINS_A", "PAINS_B", "PAINS_C"),
    "BRENK": ("BRENK",),
    "NIH": ("NIH",),
}


@lru_cache(maxsize=8)
def _catalog(kind: str) -> FilterCatalog.FilterCatalog:
    params = FilterCatalog.FilterCatalogParams()
    for name in _CATALOG_NAMES[kind]:
        params.AddCatalog(getattr(FilterCatalog.FilterCatalogParams.FilterCatalogs, name))
    return FilterCatalog.FilterCatalog(params)


@lru_cache(maxsize=32)
def _reactive_patterns() -> tuple[tuple[str, Chem.Mol], ...]:
    compiled = []
    for name, smarts in _REACTIVE_GROUPS.items():
        pattern = Chem.MolFromSmarts(smarts)
        if pattern is not None:
            compiled.append((name, pattern))
    return tuple(compiled)


def predict_esol(mol: Chem.Mol) -> float:
    """Aqueous solubility (log S) via the Delaney ESOL equation."""
    heavy_atoms = mol.GetNumHeavyAtoms()
    aromatic_atoms = sum(1 for atom in mol.GetAtoms() if atom.GetIsAromatic())
    aromatic_proportion = aromatic_atoms / heavy_atoms if heavy_atoms else 0.0

    logs = (
        0.16
        - 0.63 * Descriptors.MolLogP(mol)
        - 0.0062 * Descriptors.MolWt(mol)
        + 0.066 * rdMolDescriptors.CalcNumRotatableBonds(mol)
        - 0.74 * aromatic_proportion
    )
    return round(logs, 2)


def predict_gi_absorption(mol: Chem.Mol) -> str:
    """Egan-style absorption classification from TPSA and lipophilicity."""
    logp = Descriptors.MolLogP(mol)
    within_logp = LOGP_ABSORPTION_RANGE[0] <= logp <= LOGP_ABSORPTION_RANGE[1]
    if Descriptors.TPSA(mol) < MAX_TPSA_FOR_ABSORPTION and within_logp:
        return "High"
    return "Low"


def _alerts(mol: Chem.Mol, kind: str) -> list[str]:
    try:
        return [match.GetDescription() for match in _catalog(kind).GetMatches(mol)]
    except Exception as exc:
        logger.warning("%s filter failed: %s", kind, exc)
        return []


def _reactive_matches(mol: Chem.Mol) -> list[str]:
    return [name for name, pattern in _reactive_patterns() if mol.HasSubstructMatch(pattern)]


def compute_admet(mol: Chem.Mol) -> ADMETResult:
    """Evaluate solubility, absorption and structural alerts."""
    heavy = Chem.RemoveHs(mol)

    esol = predict_esol(heavy)
    pains = _alerts(heavy, "PAINS")
    reactive = _reactive_matches(heavy)

    failures: list[str] = []
    if pains:
        failures.append(f"PAINS alert: {', '.join(pains)}")
    if reactive:
        failures.append(f"Reactive group: {', '.join(reactive)}")
    if esol < MIN_ESOL_LOGS:
        failures.append(f"Predicted log S {esol} below {MIN_ESOL_LOGS}")

    return ADMETResult(
        esol_logs=esol,
        gi_absorption=predict_gi_absorption(heavy),
        pains_alerts=pains,
        brenk_alerts=_alerts(heavy, "BRENK"),
        nih_alerts=_alerts(heavy, "NIH"),
        reactive_groups=reactive,
        passes_filter=not failures,
        failure_reasons=failures,
    )


def evaluate_hit(
    drug_likeness: DrugLikeness, admet: ADMETResult
) -> tuple[bool, list[str]]:
    """A hit must clear both drug-likeness and the ADMET filter."""
    reasons: list[str] = []

    if drug_likeness.lipinski_violations > MAX_LIPINSKI_VIOLATIONS:
        reasons.append(
            f"{drug_likeness.lipinski_violations} Lipinski violations "
            f"(limit {MAX_LIPINSKI_VIOLATIONS})"
        )
    if drug_likeness.rotatable_bonds > MAX_ROTATABLE_BONDS:
        reasons.append(
            f"{drug_likeness.rotatable_bonds} rotatable bonds "
            f"(Veber limit {MAX_ROTATABLE_BONDS})"
        )

    reasons.extend(admet.failure_reasons)
    return not reasons, reasons
