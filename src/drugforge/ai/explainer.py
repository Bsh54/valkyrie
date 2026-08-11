"""Grounded natural-language explanation of a screening result.

The prompt carries only computed values plus a curated per-disease fact sheet
from the repository. The system prompt forbids outside claims, and the model is
asked to say so when the context is insufficient.
"""

from __future__ import annotations

import logging

import requests

from drugforge.config import (
    DEEPSEEK_API_URL,
    DEEPSEEK_MAX_TOKENS,
    DEEPSEEK_MODEL,
    DEEPSEEK_TIMEOUT_S,
    DISEASE_FACTS_DIR,
    deepseek_api_key,
)
from drugforge.domain.models import Explanation, Target

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You explain molecular docking results to researchers.

Rules:
- Use only the data in the context below. Never cite outside sources or add
  facts that are not present.
- If something is not in the context, say "not enough data to assess this".
- Never say a molecule cures, works, or is effective. Say predicted, estimated,
  suggests, or in silico.
- Be concise: at most three short paragraphs.
- Close with one sentence on the limits of what docking can show."""

_TEMPLATE = """Molecule: {smiles}
Target: {target_name} ({disease}), PDB {pdb_id}
Reference drug: {reference_drug}

Scores
- Vina affinity: {affinity} kcal/mol (reference: {reference_affinity})
- Vinardo score: {vinardo} kcal/mol
- Consensus vs reference: {consensus} (1.0 equals the reference)
- Verdict: {verdict}

Drug-likeness
- Molecular weight {molecular_weight}, log P {logp}
- H-bond donors {hbd}, acceptors {hba}, TPSA {tpsa}
- Rotatable bonds {rotatable_bonds}, Lipinski violations {lipinski_violations}

ADMET
- Predicted log S {esol}, GI absorption {gi_absorption}
- PAINS alerts: {pains}
- Reactive groups: {reactive}
- Hit status: {hit_status}

Disease context
{disease_facts}

Explain what this suggests about the molecule relative to {reference_drug},
what its strengths and weaknesses are, and what remains unknown."""


def is_available() -> bool:
    return bool(deepseek_api_key())


def load_disease_facts(target_id: str) -> str:
    """Read the curated fact sheet for a target."""
    path = DISEASE_FACTS_DIR / f"{target_id}.md"
    if not path.exists():
        return "No fact sheet is available for this target."
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return "No fact sheet is available for this target."


def build_prompt(result: dict, target: Target, disease_facts: str) -> str:
    """Render the prompt from real computed values."""
    drug_likeness = result.get("drug_likeness") or {}
    admet = result.get("admet") or {}

    reference_affinity = "not available"
    for comparison in result.get("comparisons") or []:
        if comparison.get("metric") == "affinity":
            reference_affinity = comparison.get("reference_value", reference_affinity)
            break

    def joined(values: object) -> str:
        return ", ".join(values) if isinstance(values, list) and values else "none"

    return _TEMPLATE.format(
        smiles=result.get("molecule_smiles", "unknown"),
        target_name=target.name,
        disease=target.disease,
        pdb_id=target.pdb_id,
        reference_drug=target.reference.name,
        affinity=result.get("affinity_kcal_mol", "not available"),
        reference_affinity=reference_affinity,
        vinardo=result.get("vinardo_score", "not available"),
        consensus=result.get("consensus_score", "not available"),
        verdict=result.get("verdict", "not available"),
        molecular_weight=drug_likeness.get("molecular_weight", "not available"),
        logp=drug_likeness.get("logp", "not available"),
        hbd=drug_likeness.get("hbd", "not available"),
        hba=drug_likeness.get("hba", "not available"),
        tpsa=drug_likeness.get("tpsa", "not available"),
        rotatable_bonds=drug_likeness.get("rotatable_bonds", "not available"),
        lipinski_violations=drug_likeness.get("lipinski_violations", "not available"),
        esol=admet.get("esol_logs", "not available"),
        gi_absorption=admet.get("gi_absorption", "not available"),
        pains=joined(admet.get("pains_alerts")),
        reactive=joined(admet.get("reactive_groups")),
        hit_status="passed filters" if result.get("is_hit") else "filtered out",
        disease_facts=disease_facts,
    )


def explain(result: dict, target: Target) -> Explanation:
    """Generate an explanation, degrading to a status when unavailable."""
    api_key = deepseek_api_key()
    if not api_key:
        return Explanation(status="unavailable", error_detail="DEEPSEEK_API_KEY is not set")

    prompt = build_prompt(result, target, load_disease_facts(target.id))

    try:
        response = requests.post(
            DEEPSEEK_API_URL,
            json={
                "model": DEEPSEEK_MODEL,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                "max_tokens": DEEPSEEK_MAX_TOKENS,
                "temperature": 0.3,
            },
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            timeout=DEEPSEEK_TIMEOUT_S,
        )
    except requests.Timeout:
        return Explanation(status="error", error_detail="timeout")
    except requests.ConnectionError:
        return Explanation(status="error", error_detail="network_error")
    except requests.RequestException as exc:
        return Explanation(status="error", error_detail=type(exc).__name__)

    if response.status_code != 200:
        return Explanation(status="error", error_detail=f"http_{response.status_code}")

    try:
        choices = response.json().get("choices") or []
        text = choices[0]["message"]["content"].strip()
    except (ValueError, KeyError, IndexError, AttributeError):
        return Explanation(status="error", error_detail="invalid_response")

    if not text:
        return Explanation(status="error", error_detail="empty_response")
    return Explanation(text=text, status="success")
