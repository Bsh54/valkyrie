# ADMET Filter — Design

#[[file:.kiro/specs/admet-filter/requirements.md]]

---

## 1. ADMET Properties Computed

All computed using RDKit — no external dependencies or APIs.

### Absorption / Solubility
| Property | Method | Threshold |
|----------|--------|-----------|
| ESOL logS | Delaney equation (RDKit Descriptors) | > -6 (acceptable) |
| GI absorption | Derived from TPSA + logP (Egan egg model) | TPSA < 140 Å² AND logP < 5.88 |

### Structural Alerts (binary flags)
| Filter | Source | Result |
|--------|--------|--------|
| PAINS | RDKit FilterCatalog (PAINS_A, PAINS_B, PAINS_C) | alert name(s) or "clean" |
| Brenk | RDKit FilterCatalog (BRENK) | alert name(s) or "clean" |
| NIH | RDKit FilterCatalog (NIH) | alert name(s) or "clean" |

### Reactive Groups
| Check | Method |
|-------|--------|
| Michael acceptors | SMARTS match |
| Alkyl halides | SMARTS match |
| Acyl halides | SMARTS match |

---

## 2. Hit Determination Logic

```python
def is_hit(drug_likeness: DrugLikeness, admet: ADMETResult) -> tuple[bool, list[str]]:
    """
    Returns (is_hit, reasons_for_failure).
    A molecule is a hit IFF:
      - lipinski_violations <= 1
      - rotatable_bonds <= 10 (Veber)
      - no PAINS alerts
      - no Brenk alerts (critical subset)
      - ESOL logS > -6
      - no reactive group flags
    """
```

When a molecule fails, the `reasons` list contains human-readable explanations:
```
["PAINS alert: rhodanine_A", "ESOL logS = -7.2 (threshold: > -6)"]
```

---

## 3. Data Model

```python
@dataclass
class ADMETResult:
    esol_logs: float              # predicted aqueous solubility
    gi_absorption: str            # "High" or "Low"
    pains_alerts: list[str]       # matched PAINS pattern names
    brenk_alerts: list[str]       # matched Brenk pattern names
    nih_alerts: list[str]         # matched NIH pattern names
    reactive_groups: list[str]    # matched reactive SMARTS names
    passes_filter: bool           # overall pass/fail
    failure_reasons: list[str]    # why it failed (empty if passes)

    DISCLAIMER: str = (
        "These are in-silico predictions based on structural rules and "
        "physicochemical models. They do not constitute toxicology data "
        "or clinical evidence. Laboratory validation is required."
    )
```

---

## 4. Module Structure

```
drugforge/
├── admet.py          # NEW — ADMET computation + filter logic
└── pipeline.py       # MODIFIED — adds ADMET stage after drug-likeness
```

### Pipeline position

```
... → dock → rescore → consensus → drug-likeness → ADMET FILTER → compare → store
                                                        ↓
                                              ADMETResult (pass/fail + reasons)
                                                        ↓
                                              PipelineResult.is_hit = True/False
                                              PipelineResult.admet = ADMETResult
```

---

## 5. API Changes

`POST /api/dock` response gains:
```json
{
  "admet": {
    "esol_logs": -3.2,
    "gi_absorption": "High",
    "pains_alerts": [],
    "brenk_alerts": [],
    "reactive_groups": [],
    "passes_filter": true,
    "failure_reasons": [],
    "disclaimer": "These are in-silico predictions..."
  },
  "is_hit": true
}
```

When filtered:
```json
{
  "admet": {
    "pains_alerts": ["rhodanine_A"],
    "passes_filter": false,
    "failure_reasons": ["PAINS alert: rhodanine_A"]
  },
  "is_hit": false
}
```

---

## 6. Testing Strategy

### Test: Known toxicophore is flagged
```
Given: a molecule containing a rhodanine substructure (known PAINS hit)
When: ADMET filter is applied
Then: pains_alerts is non-empty AND passes_filter is False
```

### Test: Clean drug-like molecule passes
```
Given: pyrimethamine (clean, drug-like, no structural alerts)
When: ADMET filter is applied
Then: passes_filter is True AND failure_reasons is empty AND is_hit is True
```

### Test: Disclaimer always present
```
Given: any ADMET result
Then: DISCLAIMER field is a non-empty string containing "in-silico"
```
