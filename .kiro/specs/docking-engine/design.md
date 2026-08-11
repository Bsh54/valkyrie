# Docking Engine — Design

#[[file:.kiro/specs/docking-engine/requirements.md]]

---

## 1. Target-Registry Data Model

Each disease target is a frozen dataclass in `drugforge/targets.py`:

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class DockingBox:
    center_x: float
    center_y: float
    center_z: float
    size_x: float
    size_y: float
    size_z: float

@dataclass(frozen=True)
class ReferenceDrug:
    name: str              # e.g. "pyrimethamine"
    smiles: str            # canonical SMILES

@dataclass(frozen=True)
class Target:
    id: str                # slug, e.g. "pf-dhfr"
    name: str              # display name, e.g. "PfDHFR"
    disease: str           # e.g. "malaria"
    pdb_id: str            # e.g. "1J3I"
    box: DockingBox        # from co-crystallized ligand coordinates
    reference: ReferenceDrug
```

Registry access:

```python
TARGETS: dict[str, Target] = { "pf-dhfr": Target(...) }

def get_target(target_id: str) -> Target:
    """Raise TargetNotFoundError if unknown."""
```

Adding a new disease = adding one `Target` entry to `TARGETS`. No file parsing,
no config language — Python validates at import time.

### Initial target: Malaria / PfDHFR

| Field | Value |
|-------|-------|
| id | pf-dhfr |
| pdb_id | 1J3I |
| box center | Derived from co-crystallized pyrimethamine coordinates |
| box size | 20 × 20 × 20 Å (standard for small-molecule pocket) |
| reference | pyrimethamine · `c1ccc(c(c1)Cl)c2cnc(nc2N)N` |

---

## 2. Docking Pipeline

The pipeline is a linear sequence of pure-ish functions. Each stage receives
typed input and returns typed output; failure at any stage short-circuits with a
structured error.

```
User input (name or SMILES)
        │
        ▼
┌──────────────────┐
│ 1. RESOLVE       │  resolver.py — name → canonical SMILES
│    local lookup  │  (local compounds.json → SMILES parse → PubChem fallback)
│    then PubChem  │
└────────┬─────────┘
         │ canonical SMILES
         ▼
┌──────────────────┐
│ 2. PREPARE       │  ligand_prep.py — SMILES → 3D Mol + PDBQT
│    LIGAND        │  (RDKit embed ETKDGv3 → MMFF optimize → Meeko → PDBQT)
└────────┬─────────┘
         │ Mol object + PDBQT string
         ▼
┌──────────────────┐
│ 3. PREPARE       │  receptor.py — ensure receptor PDBQT is cached
│    TARGET        │  (download PDB from RCSB → strip water → prepare PDBQT)
└────────┬─────────┘
         │ receptor PDBQT path
         ▼
┌──────────────────┐
│ 4. DOCK          │  docking.py — Vina execution
│    (Vina)        │  (set receptor, ligand, box, exhaustiveness → run)
└────────┬─────────┘
         │ DockingResult (affinity, poses PDBQT, best pose SDF)
         ▼
┌──────────────────┐
│ 5. DRUG-LIKENESS │  druglikeness.py — descriptor computation
│                  │  (MW, logP, HBD, HBA, TPSA, RotBonds, Lipinski violations)
└────────┬─────────┘
         │ DrugLikeness dataclass
         ▼
┌──────────────────┐
│ 6. COMPARE TO    │  comparator.py — side-by-side + verdict
│    REFERENCE     │  (dock reference if not cached, compute delta/ratio, badge)
└────────┬─────────┘
         │ list[Comparison] + verdict badge
         ▼
┌──────────────────┐
│ 7. STORE & REPLY │  store.py + api.py — persist to SQLite, return JSON
└──────────────────┘
```

### Pipeline orchestrator (`drugforge/pipeline.py`)

```python
def run_docking_pipeline(
    molecule_input: str,
    target_id: str,
    exhaustiveness: int = 8,
) -> PipelineResult:
    """
    Execute the full pipeline synchronously.
    Returns PipelineResult or raises PipelineError with stage info.
    """
```

This is the single entry point called by the API. It catches stage-level errors
and wraps them with context (which stage failed, what was the input).

---

## 3. Module Structure

```
drugforge/
├── __init__.py
├── config.py           # Paths, defaults (exhaustiveness, box padding, etc.)
├── targets.py          # Target/DockingBox/ReferenceDrug dataclasses + TARGETS
├── resolver.py         # Name resolution: local → SMILES → PubChem
├── validator.py        # Input validation, wraps resolver
├── ligand_prep.py      # SMILES → 3D Mol + PDBQT
├── receptor.py         # PDB download, caching, receptor PDBQT preparation
├── docking.py          # Vina wrapper → DockingResult
├── druglikeness.py     # Descriptor computation → DrugLikeness
├── comparator.py       # Reference docking + comparison table + verdict
├── pipeline.py         # Orchestrator — ties stages 1–7 together
├── store.py            # SQLite persistence
├── api.py              # FastAPI endpoints
└── errors.py           # Custom exception hierarchy
data/
├── compounds.json      # Curated ethnobotanical name → SMILES lookup
├── receptors/          # Cached PDB + PDBQT (gitignored)
└── results.db          # SQLite (gitignored)
static/
└── index.html          # Frontend with 3Dmol.js
tests/
├── test_resolver.py
├── test_validator.py
├── test_ligand_prep.py
├── test_docking.py
├── test_druglikeness.py
├── test_comparator.py
├── test_pipeline.py
└── test_properties.py  # Property-based (Hypothesis)
```

---

## 4. Error Handling Strategy

### Exception hierarchy (`drugforge/errors.py`)

```python
class DrugForgeError(Exception):
    """Base for all DrugForge errors."""
    pass

class ValidationError(DrugForgeError):
    """Invalid molecule input."""
    detail: str

class ResolutionError(DrugForgeError):
    """Could not resolve name to SMILES."""
    detail: str

class LigandPrepError(DrugForgeError):
    """3D embedding or PDBQT conversion failed."""
    detail: str

class ReceptorError(DrugForgeError):
    """PDB download or receptor preparation failed."""
    detail: str

class DockingError(DrugForgeError):
    """Vina execution failed."""
    detail: str

class TargetNotFoundError(DrugForgeError):
    """Unknown target_id."""
    detail: str

class PipelineError(DrugForgeError):
    """Wraps stage errors with pipeline context."""
    stage: str
    cause: DrugForgeError
```

### Error-handling rules

1. **Never crash** — every RDKit, network, or Vina failure is caught at the
   stage level and wrapped in the appropriate typed error.
2. **Structured API errors** — FastAPI exception handlers map:
   - `ValidationError` → HTTP 422 `{"error": "invalid_molecule", "detail": ...}`
   - `ResolutionError` → HTTP 404 `{"error": "unresolved_molecule", "detail": ...}`
   - `TargetNotFoundError` → HTTP 404 `{"error": "unknown_target", "detail": ...}`
   - `LigandPrepError | ReceptorError | DockingError` → HTTP 500
     `{"error": "pipeline_failure", "stage": ..., "detail": ...}`
3. **No silent swallowing** — errors are logged with full traceback server-side
   before returning the safe client message.
4. **Timeout safety** — docking is synchronous but bounded: if Vina hangs beyond
   a configurable limit (default 300s), the process is killed and a
   `DockingError("timeout")` is raised.

---

## 5. Property-Based Testing Strategy

Derived from the testing steering invariants. Uses `pytest` + `hypothesis`.

### Invariant 1: Reproducibility
```
Given: a fixed molecule (e.g. pyrimethamine) docked against pf-dhfr
When: docked N=3 times with the same exhaustiveness and random seed
Then: all affinity scores are within ε = 0.1 kcal/mol of each other
```
Implementation: parameterize seed in Vina, assert `max(scores) - min(scores) < 0.1`.

### Invariant 2: Positive/Negative Controls
```
Given: pf-dhfr target
When: pyrimethamine (positive) and glucose (negative) are docked
Then: pyrimethamine affinity < glucose affinity (more negative = better)
```
Implementation: dock both, assert `ref_affinity < glucose_affinity`.

### Invariant 3: Redocking (RMSD)
```
Given: the co-crystallized ligand pose from PDB 1J3I
When: re-docked into the same receptor
Then: RMSD between predicted and crystal pose < 2.0 Å
```
Implementation: extract ligand from PDB, dock, compute heavy-atom RMSD vs
crystal coordinates. (Stretch goal — requires extracting reference coordinates.)

### Invariant 4: Input Robustness
```
Given: arbitrary ASCII strings (Hypothesis text strategy)
When: submitted to the validator
Then: either a valid SMILES is returned OR a ValidationError is raised
      (never an unhandled exception)
```
Implementation: `@given(st.text(alphabet=st.characters(codec='ascii'), max_size=200))`

### Invariant 5: Scores Relative to Reference
```
Given: any successful docking result
Then: the comparison list is non-empty, every Comparison has both
      molecule_value and reference_value populated, and ratio > 0
```
Implementation: assert on structure after every pipeline run in integration tests.

### Test markers
- `@pytest.mark.slow` — tests that invoke Vina (invariants 1, 2, 3).
- `@pytest.mark.property` — Hypothesis-based tests.
- Default `pytest` run excludes slow; CI runs all.

### Test data
- Positive control: pyrimethamine (the reference drug).
- Negative controls: glucose (`OC[C@H]1OC(O)[C@H](O)[C@@H](O)[C@@H]1O`),
  ethanol (`CCO`).
- Invalid inputs: empty string, `"not_a_molecule_xyz!!!"`, random bytes.
