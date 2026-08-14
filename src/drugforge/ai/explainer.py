"""Grounded natural-language explanation of a screening result.

The prompt carries only computed values plus a curated per-disease fact sheet
from the repository. The system prompt forbids outside claims, and the model is
asked to say so when the context is insufficient.
"""

from __future__ import annotations

import logging

import requests
from rdkit import Chem

from drugforge.config import (
    DEEPSEEK_API_URL,
    DEEPSEEK_MAX_TOKENS,
    DEEPSEEK_MODEL,
    DEEPSEEK_TIMEOUT_S,
    DISEASE_FACTS_DIR,
    deepseek_api_key,
)
from drugforge.content.library import list_compounds
from drugforge.domain.models import Explanation, Target

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a computational-chemistry assistant. You INTERPRET a
docking result for a researcher and turn the numbers into clear, useful insight.

Your job is analysis, not a restatement of the values. Explain what the result
means and what to do with it.

Rules:
- Reason using only the data in the context below. Never add outside facts or cite
  sources. If a value is missing, say "not enough data to assess this".
- Interpret every key number relative to the reference drug: is the molecule
  better, comparable or worse, and what does that imply?
- Turn drug-likeness and ADMET into meaning: name the single biggest strength and
  the single biggest weakness, and which property is the bottleneck.
- DrugForge bridges traditional African plant medicine and modern validation. When
  a traditional use is provided, connect the computed result to it: does the
  in-silico prediction support or nuance that traditional use? Credit the plant and
  the people, and stay cautious (support is not proof).
- Be actionable: end with a concrete takeaway (for example, worth prioritising for
  lab testing, or which liability should be fixed first).
- Never say a molecule cures, works, or is effective. Say predicted, estimated,
  suggests, or in silico.
- Be tight and readable: three to four short paragraphs.
- Close with one sentence on what docking cannot show."""

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

Traditional use
{traditional_use}

Disease context
{disease_facts}

Give a grounded interpretation with real insight:
1. Binding: how the Vina affinity and the consensus compare to {reference_drug},
   and what that suggests about how tightly this molecule may sit in the pocket.
2. Developability: read the drug-likeness and ADMET together, name the biggest
   strength and the biggest weakness, and say which property is the bottleneck.
3. Traditional knowledge: if a traditional use is given above, say cautiously
   whether this in-silico result supports, nuances, or does not support that
   traditional use, and credit the plant and people it comes from. If none is
   given, skip this point.
4. Takeaway: one clear, actionable conclusion (prioritise for lab testing, or the
   first liability to address), consistent with the verdict.
5. What remains unknown that only experiments could settle."""


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


def _canonical(smiles: str) -> str | None:
    try:
        mol = Chem.MolFromSmiles(smiles)
        return Chem.MolToSmiles(mol) if mol is not None else None
    except Exception:
        return None


def traditional_use_for(smiles: str) -> str:
    """Ethnobotanical context for a molecule, matched by canonical SMILES."""
    target = _canonical(smiles)
    if target:
        for entry in list_compounds():
            if _canonical(entry.get("smiles", "")) == target:
                plant = entry.get("plant") or {}
                use = entry.get("traditional_use") or {}
                local = plant.get("local_name")
                return "\n".join(
                    part
                    for part in [
                        f"{entry.get('compound_name', 'compound')} from "
                        f"{plant.get('scientific_name', 'unknown plant')}"
                        + (f" ({local})" if local else ""),
                        f"Traditionally used for: {use.get('disease', 'unknown')}",
                        f"Region and people: {use.get('region', 'unknown')}; "
                        f"{use.get('people', 'unknown')}",
                        f"Preparation: {use.get('preparation', 'unknown')}",
                        f"Source: {entry.get('source', 'unknown')}",
                    ]
                    if part
                )
    return "This molecule is not in the ethnobotanical library; no traditional-use record."


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
        traditional_use=traditional_use_for(result.get("molecule_smiles", "unknown")),
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
