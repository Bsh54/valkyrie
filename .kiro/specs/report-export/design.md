# Report Export — Design

#[[file:.kiro/specs/report-export/requirements.md]]

---

## 1. Architecture

```
GET /api/result/{id}/report
        │
        ▼
┌──────────────────────┐
│  Load PipelineResult │  ← from SQLite store
│  from store          │
└────────┬─────────────┘
         │
         ▼
┌──────────────────────┐
│  Generate molecule   │  ← RDKit Draw.MolToImage()
│  2D depiction        │
└────────┬─────────────┘
         │
         ▼
┌──────────────────────┐
│  Build PDF           │  ← fpdf2 or reportlab
│  (sections below)    │
└────────┬─────────────┘
         │
         ▼
  Return PDF as response (Content-Type: application/pdf)
```

---

## 2. PDF Layout (A4, portrait)

### Page 1: Summary
```
┌─────────────────────────────────────────────────────┐
│  ⚠ IN-SILICO PREDICTION — NOT FOR CLINICAL USE      │
├─────────────────────────────────────────────────────┤
│  DrugForge — Molecular Docking Report               │
│  Generated: 2026-08-08                              │
├─────────────────────────────────────────────────────┤
│                                                      │
│  Molecule: Cryptolepine                             │
│  SMILES: Cn1c2ccccc2c2c1c1ccccc1[nH]2              │
│  Target: PfDHFR (Malaria)   PDB: 1J3I              │
│  Reference drug: Pyrimethamine                      │
│                                                      │
│  ┌─────────────────────┐                            │
│  │  [2D molecule image] │     VERDICT: PROMISING    │
│  │                      │     Affinity: -8.1 kcal/mol│
│  │                      │     Consensus: 1.03       │
│  └─────────────────────┘                            │
│                                                      │
│  ── Pipeline Funnel ──                              │
│  ✅ Vina Docking: -8.1 kcal/mol                    │
│  ✅ Vinardo Rescore: -7.2 kcal/mol                 │
│  ✅ Consensus: 1.03 (better than reference)         │
│  ✅ Drug-likeness: 0 Lipinski violations            │
│  ✅ ADMET/Tox: Clean (no alerts)                   │
│  ⏭ Boltz-2 AI: Unavailable                        │
│                                                      │
├─────────────────────────────────────────────────────┤
│  ⚠ In-silico predictions based on computational     │
│  models. Not clinical evidence. Lab validation       │
│  required before any conclusion.                     │
└─────────────────────────────────────────────────────┘
```

### Page 2: Detailed Comparison + ADMET
```
┌─────────────────────────────────────────────────────┐
│  ── Comparison to Reference Drug ──                  │
│                                                      │
│  Metric        │ Molecule  │ Reference │ Delta      │
│  ─────────────────────────────────────────────────  │
│  Affinity      │ -8.1      │ -7.9      │ -0.2 ✓    │
│  MW            │ 232       │ 248       │ -16        │
│  logP          │ 2.8       │ 1.9       │ +0.9       │
│  HBD           │ 1         │ 2         │ -1         │
│  HBA           │ 2         │ 4         │ -2         │
│  TPSA          │ 19.2      │ 77.8      │ -58.6      │
│  Rot. bonds    │ 0         │ 2         │ -2         │
│  Lipinski viol │ 0         │ 0         │  0         │
│                                                      │
│  ── ADMET Profile ──                                │
│  ESOL logS: -3.1 (acceptable solubility)            │
│  GI Absorption: High                                │
│  PAINS alerts: None                                 │
│  Brenk alerts: None                                 │
│  Reactive groups: None                              │
│  Hit status: ✅ PASS                                │
│                                                      │
│  ── AI Explanation ──                               │
│  [natural-language explanation from ai-explainer,    │
│   or "AI explanation unavailable" if key not set]    │
│                                                      │
├─────────────────────────────────────────────────────┤
│  ⚠ DISCLAIMER: All numbers are in-silico predictions│
│  This report does not constitute medical evidence.   │
└─────────────────────────────────────────────────────┘
```

---

## 3. Module Structure

```
drugforge/
├── report.py       # NEW — PDF report generation
└── api.py          # MODIFIED — adds GET /api/result/{id}/report
```

### `drugforge/report.py`

```python
def generate_report(result: dict) -> bytes:
    """
    Generate a PDF report from a stored docking result.

    Args:
        result: dict from store.get_result()

    Returns:
        PDF file as bytes.
    """
```

---

## 4. Dependencies

- `fpdf2` — lightweight PDF generation (pure Python, no system deps)
- `rdkit.Chem.Draw` — 2D molecule depiction (already installed)
- `Pillow` — image handling for embedding in PDF (already installed)

---

## 5. Molecule Image Generation

```python
from rdkit import Chem
from rdkit.Chem import Draw
from io import BytesIO

def render_molecule_image(smiles: str, size=(400, 300)) -> bytes:
    mol = Chem.MolFromSmiles(smiles)
    img = Draw.MolToImage(mol, size=size)
    buf = BytesIO()
    img.save(buf, format='PNG')
    return buf.getvalue()
```

---

## 6. Testing Strategy

### Test: Report produced for valid result
```
Given: a valid stored docking result
When: GET /api/result/{id}/report is called
Then: response is 200, Content-Type is application/pdf, body is non-empty PDF
```

### Test: Report contains real numbers
```
Given: a result with affinity = -8.1
When: PDF is generated
Then: the PDF text content contains "-8.1"
```

### Test: Report not found
```
Given: a non-existent result ID
When: GET /api/result/{id}/report
Then: response is 404
```
