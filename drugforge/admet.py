"""ADMET/toxicity filter — RDKit-based structural alerts and property filters."""

import logging
from dataclasses import dataclass, field, asdict
from typing import ClassVar

from rdkit import Chem
from rdkit.Chem import Descriptors, FilterCatalog, rdMolDescriptors

from drugforge.druglikeness import DrugLikeness

logger = logging.getLogger(__name__)

# DISCLAIMER attached to every ADMET result
_DISCLAIMER = (
    "These are in-silico predictions based on structural rules and "
    "physicochemical models. They do not constitute toxicology data "
    "or clinical evidence. Laboratory validation is required."
)

# Reactive group SMARTS patterns
_REACTIVE_SMARTS = {
    "Michael acceptor": "[CX3]=[CX3][CX3]=[O,N]",
    "Alkyl halide": "[CX4][F,Cl,Br,I]",
    "Acyl halide": "[CX3](=[OX1])[F,Cl,Br,I]",
    "Sulfonyl halide": "[SX4](=[OX1])(=[OX1])[F,Cl,Br,I]",
    "Acid anhydride": "[CX3](=[OX1])[OX2][CX3](=[OX1])",
    "Epoxide": "C1OC1",
    "Aziridine": "C1NC1",
}


@dataclass
class ADMETResult:
    """ADMET/toxicity filter results."""
    esol_logs: float
    gi_absorption: str  # "High" or "Low"
    pains_alerts: list[str]
    brenk_alerts: list[str]
    nih_alerts: list[str]
    reactive_groups: list[str]
    passes_filter: bool
    failure_reasons: list[str]
    disclaimer: str = field(default=_DISCLAIMER)

    def to_dict(self) -> dict:
        return asdict(self)


def _compute_esol(mol: Chem.Mol) -> float:
    """
    Predict aqueous solubility (logS) using the Delaney/ESOL model.

    Delaney equation: logS = 0.16 - 0.63*logP - 0.0062*MW + 0.066*RB - 0.74*AP
    Where AP = aromatic proportion (aromatic atoms / heavy atoms).
    """
    logp = Descriptors.MolLogP(mol)
    mw = Descriptors.MolWt(mol)
    rb = rdMolDescriptors.CalcNumRotatableBonds(mol)
    heavy_atoms = mol.GetNumHeavyAtoms()
    aromatic_atoms = sum(1 for atom in mol.GetAtoms() if atom.GetIsAromatic())
    ap = aromatic_atoms / heavy_atoms if heavy_atoms > 0 else 0

    logs = 0.16 - 0.63 * logp - 0.0062 * mw + 0.066 * rb - 0.74 * ap
    return round(logs, 2)


def _predict_gi_absorption(mol: Chem.Mol) -> str:
    """
    Predict GI absorption using the Egan model (TPSA + logP thresholds).
    High absorption if TPSA < 140 and logP in [-2, 5.88].
    """
    tpsa = Descriptors.TPSA(mol)
    logp = Descriptors.MolLogP(mol)

    if tpsa < 140 and -2 <= logp <= 5.88:
        return "High"
    return "Low"


def _get_filter_alerts(mol: Chem.Mol, catalog_name: str) -> list[str]:
    """Run a FilterCatalog and return matching alert names."""
    try:
        params = FilterCatalog.FilterCatalogParams()
        if catalog_name == "PAINS":
            params.AddCatalog(FilterCatalog.FilterCatalogParams.FilterCatalogs.PAINS_A)
            params.AddCatalog(FilterCatalog.FilterCatalogParams.FilterCatalogs.PAINS_B)
            params.AddCatalog(FilterCatalog.FilterCatalogParams.FilterCatalogs.PAINS_C)
        elif catalog_name == "BRENK":
            params.AddCatalog(FilterCatalog.FilterCatalogParams.FilterCatalogs.BRENK)
        elif catalog_name == "NIH":
            params.AddCatalog(FilterCatalog.FilterCatalogParams.FilterCatalogs.NIH)
        else:
            return []

        catalog = FilterCatalog.FilterCatalog(params)
        matches = catalog.GetMatches(mol)
        return [match.GetDescription() for match in matches]
    except Exception as e:
        logger.warning(f"FilterCatalog {catalog_name} failed: {e}")
        return []


def _detect_reactive_groups(mol: Chem.Mol) -> list[str]:
    """Detect known reactive groups via SMARTS matching."""
    found = []
    for name, smarts in _REACTIVE_SMARTS.items():
        pattern = Chem.MolFromSmarts(smarts)
        if pattern and mol.HasSubstructMatch(pattern):
            found.append(name)
    return found


def compute_admet(mol: Chem.Mol) -> ADMETResult:
    """
    Compute ADMET-style properties and structural alerts.

    Uses RDKit-based models only (CPU, no external API).

    Args:
        mol: RDKit Mol (can have Hs).

    Returns:
        ADMETResult with all filters applied.
    """
    mol_no_h = Chem.RemoveHs(mol)

    # Solubility
    esol_logs = _compute_esol(mol_no_h)

    # GI absorption
    gi_absorption = _predict_gi_absorption(mol_no_h)

    # Structural alerts
    pains_alerts = _get_filter_alerts(mol_no_h, "PAINS")
    brenk_alerts = _get_filter_alerts(mol_no_h, "BRENK")
    nih_alerts = _get_filter_alerts(mol_no_h, "NIH")

    # Reactive groups
    reactive_groups = _detect_reactive_groups(mol_no_h)

    # Determine pass/fail
    failure_reasons = []

    if pains_alerts:
        failure_reasons.append(f"PAINS alert(s): {', '.join(pains_alerts)}")
    if reactive_groups:
        failure_reasons.append(f"Reactive group(s): {', '.join(reactive_groups)}")
    if esol_logs < -6:
        failure_reasons.append(f"ESOL logS = {esol_logs} (threshold: > -6)")

    passes_filter = len(failure_reasons) == 0

    return ADMETResult(
        esol_logs=esol_logs,
        gi_absorption=gi_absorption,
        pains_alerts=pains_alerts,
        brenk_alerts=brenk_alerts,
        nih_alerts=nih_alerts,
        reactive_groups=reactive_groups,
        passes_filter=passes_filter,
        failure_reasons=failure_reasons,
    )


def is_hit(drug_likeness: DrugLikeness, admet: ADMETResult) -> tuple[bool, list[str]]:
    """
    Determine if a molecule is a hit (passes both drug-likeness and ADMET).

    Returns:
        (is_hit, combined_failure_reasons)
    """
    reasons = []

    # Drug-likeness check
    if drug_likeness.lipinski_violations > 1:
        reasons.append(
            f"Lipinski violations: {drug_likeness.lipinski_violations} (max 1)"
        )
    if drug_likeness.rotatable_bonds > 10:
        reasons.append(
            f"Rotatable bonds: {drug_likeness.rotatable_bonds} (Veber max 10)"
        )

    # ADMET check
    reasons.extend(admet.failure_reasons)

    return (len(reasons) == 0, reasons)
