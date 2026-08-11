# AI Explainer — Design

#[[file:.kiro/specs/ai-explainer/requirements.md]]

---

## 1. Architecture

```
Pipeline result available
        │
        ▼
┌──────────────────────┐
│  Build prompt context│  ← real numbers + disease fact sheet
└────────┬─────────────┘
         │
         ▼
┌──────────────────────┐
│  Call DeepSeek API   │  ← POST /chat/completions (deepseek-v4-flash)
│  (15s timeout)       │
└────────┬─────────────┘
         │
         ▼
┌──────────────────────┐
│  Return explanation  │  ← or "unavailable" on failure
└──────────────────────┘
```

---

## 2. Module Design

### `drugforge/explainer.py`

```python
@dataclass
class Explanation:
    text: str             # The generated explanation
    status: str           # "success" | "unavailable" | "error"
    error_detail: str | None
    disclaimer: str       # always present

def is_explainer_available() -> bool:
    """Check if DEEPSEEK_API_KEY is set."""

def generate_explanation(result: dict, target_id: str) -> Explanation:
    """
    Generate a grounded natural-language explanation.

    - Loads disease fact sheet from data/disease_facts/{target_id}.md
    - Builds prompt context from real computed numbers
    - Calls DeepSeek API (deepseek-v4-flash)
    - Returns Explanation or graceful failure
    """
```

---

## 3. Prompt Design

### System prompt
```
You are a scientific communication assistant for DrugForge, a virtual screening
platform. You explain molecular docking results in plain language for researchers.

RULES:
- Use ONLY the data provided in the context below. Do not cite external sources.
- If information is missing, say "not enough data to assess this."
- Never claim a molecule "cures", "works", or "is effective." Use: "predicted",
  "suggests", "in silico estimate", "computational prediction."
- Keep language accessible but scientifically accurate.
- Be concise (2-3 paragraphs max).
- End with a one-sentence scope reminder.
```

### User prompt (template)
```
Explain this docking result for a researcher:

MOLECULE: {smiles} ({compound_name})
TARGET: {target_name} ({disease}) — PDB: {pdb_id}
REFERENCE DRUG: {reference_name}

SCORES:
- Vina affinity: {affinity} kcal/mol (reference: {ref_affinity})
- Vinardo score: {vinardo} kcal/mol
- Consensus score: {consensus} (1.0 = equal to reference)
- Verdict: {verdict}

DRUG-LIKENESS:
- MW: {mw}, logP: {logp}, HBD: {hbd}, HBA: {hba}
- TPSA: {tpsa}, Rotatable bonds: {rotbonds}
- Lipinski violations: {lipinski_violations}

ADMET:
- ESOL logS: {esol}, GI absorption: {gi}
- PAINS alerts: {pains}
- Hit status: {hit_status}

DISEASE CONTEXT:
{disease_fact_sheet}

Explain what this result means, whether this molecule looks promising compared
to {reference_name}, and what the key strengths/weaknesses are. Be honest about
limitations.
```

---

## 4. Disease Fact Sheets

Stored in `data/disease_facts/{target_id}.md`:

### Example: `data/disease_facts/pf-dhfr.md`
```markdown
# PfDHFR — Plasmodium falciparum Dihydrofolate Reductase

## Disease
Malaria (Plasmodium falciparum). ~250 million cases/year, ~600,000 deaths/year
(mostly children under 5 in sub-Saharan Africa).

## Target
DHFR catalyzes the reduction of dihydrofolate to tetrahydrofolate, essential for
nucleotide synthesis. Inhibiting PfDHFR starves the parasite of thymidylate.

## Reference Drug
Pyrimethamine: competitive inhibitor of PfDHFR. Used in combination therapy
(with sulfadoxine). Widespread resistance mutations (S108N, N51I, C59R, I164L)
limit efficacy in many regions.

## Clinical Context
New inhibitors must overcome resistance mutations. Affinity < -7 kcal/mol
against wild-type PfDHFR is considered a reasonable starting point for
optimization. This is a computational screen — compounds must be validated
in enzymatic assays and parasite cultures before any clinical consideration.
```

---

## 5. API Integration

The explainer is called optionally after the pipeline completes:
- In `POST /api/dock`: generate explanation and include in response
- In `GET /api/result/{id}`: include stored explanation
- In PDF report: include the explanation text

### Response field
```json
{
  "explanation": {
    "text": "This docking result suggests that cryptolepine...",
    "status": "success",
    "disclaimer": "This is a computational prediction..."
  }
}
```

### Graceful failure
```json
{
  "explanation": {
    "text": "",
    "status": "unavailable",
    "error_detail": "DEEPSEEK_API_KEY not set",
    "disclaimer": "..."
  }
}
```

---

## 6. DeepSeek API Call

```python
POST https://api.deepseek.com/chat/completions
Headers:
  Authorization: Bearer $DEEPSEEK_API_KEY
  Content-Type: application/json
Body:
{
  "model": "deepseek-chat",
  "messages": [
    {"role": "system", "content": SYSTEM_PROMPT},
    {"role": "user", "content": USER_PROMPT}
  ],
  "max_tokens": 300,
  "temperature": 0.3
}
```

Note: `deepseek-v4-flash` may map to model name `deepseek-chat` or similar
at the API level. The config makes this adjustable.

---

## 7. Testing Strategy

### Test: Prompt context contains real numbers
```
Given: a result with affinity=-8.1, MW=232, logP=2.8
When: the prompt is built
Then: the prompt string contains "-8.1", "232", "2.8"
```

### Test: Missing API key does not crash
```
Given: DEEPSEEK_API_KEY is not set
When: generate_explanation() is called
Then: returns Explanation(status="unavailable"), no exception raised
```

### Test: Disease fact sheet loaded
```
Given: target_id="pf-dhfr"
When: fact sheet is loaded
Then: returns non-empty string containing "Plasmodium"
```

### Test: Explanation disclaimer always present
```
Given: any Explanation result
Then: disclaimer field is non-empty and contains "in silico" or "prediction"
```
