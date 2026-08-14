# Docking Engine — Design

#[[file:.kiro/specs/docking-engine/requirements.md]]

---

## 1. Target-Registry Data Model

Domain models live in `src/drugforge/domain/models.py`; the registry in
`src/drugforge/domain/targets.py`.

```python
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
    name: str
    smiles: str

@dataclass(frozen=True)
class Target:
    id: str
    name: str
    disease: str
    pdb_id: str
    box: DockingBox
    reference: ReferenceDrug

TARGETS: dict[str, Target] = { "pf-dhfr": Target(...), "tc-cyp51": Target(...), ... }

def get_target(target_id: str) -> Target:
    """Raise TargetNotFoundError if unknown."""
```

Adding a new disease means adding one `Target` entry. No file parsing, no
config language; Python validates the shape at import time.

### Registry (4 targets)

| id | disease | PDB | box (per axis) | reference |
|---|---|---|---|---|
| pf-dhfr | malaria | 1J3I | 20.0 A | pyrimethamine |
| tc-cyp51 | Chagas disease | 3K1O | 22.5 A | fluconazole |
| lm-ptr1 | leishmaniasis | 1E7W | 22.5 A | methotrexate |
| tb-ptr1 | sleeping sickness | 2WD8 | 22.5 A | methotrexate |

Box centers are the co-crystallised ligand centroid for each PDB entry (POZ for
3K1O, MTX for 1E7W, VGF for 2WD8). Box size is capped at 22.5 A per axis, down
from an earlier 30 A, to keep the search focused and CPU-light on the 8 GB VPS.

Chagas uses fluconazole rather than posaconazole as the reference: posaconazole
is large enough that its repeated docking (the reference is re-docked for every
comparison) exceeded the benchmark timeout. Fluconazole targets the same CYP51
enzyme, is clinically used against Chagas disease, and docks in about a minute.

---

## 2. Docking Pipeline

Linear stages, each typed in and typed out; any failure short-circuits with a
structured error naming the stage. Orchestrated by
`src/drugforge/pipeline/runner.py::run_screening`.

```
molecule_input, target_id
        |
        v
1. VALIDATE            drugforge.chem.validator
   name/SMILES -> canonical SMILES (local table -> ethnobotanical registry
   -> direct SMILES parse -> PubChem)
        |
        v
2. TARGET LOOKUP       drugforge.domain.targets.get_target
        |
        v
3. LIGAND PREPARATION  drugforge.chem.ligand
   protonate at pH 7.4 (Open Babel, falls back to the input SMILES on any
   failure) -> RDKit ETKDGv3 embed -> MMFF optimise -> Meeko -> PDBQT
        |
        v
4. RECEPTOR PREPARATION drugforge.chem.receptor
   download PDB from RCSB (cached) -> strip water/inhibitor, KEEP essential
   cofactors -> Open Babel PDBQT at pH 7.4, no Gasteiger charges -> guard
   against an empty receptor
        |
        v
5. DOCK                drugforge.docking.engine.dock
   AutoDock Vina, bounded CPU count -> DockingResult (affinity, pose PDBQT/SDF)
        |
        v
6. RESCORE             drugforge.docking.rescoring.rescore_vinardo
   same pose, Vinardo scoring function (falls back to the Vina score if
   rescoring fails; never aborts the run)
        |
        v
7. REFERENCE BASELINE  drugforge.pipeline.comparison.reference_baseline
   dock the target's reference drug once per process, cache it
        |
        v
8. CONSENSUS           drugforge.docking.consensus.compute_consensus
   weighted, reference-normalised combination of Vina and Vinardo
        |
        v
9. DRUG-LIKENESS       drugforge.chem.descriptors.compute_drug_likeness
        |
        v
10. ADMET FILTER       drugforge.chem.admet.compute_admet / evaluate_hit
        |
        v
11. REFERENCE COMPARISON drugforge.pipeline.comparison.build_comparisons
        |
        v
12. AI EXPLANATION (optional) drugforge.ai.explainer.explain
    grounded in the computed result and, when the molecule matches an
    ethnobotanical library entry by canonical SMILES, its traditional use
        |
        v
ScreeningResult -> persisted (drugforge.storage.repository) -> JSON response
```

Boltz-2 AI confirmation was designed as an additional optional stage but is not
built: it needs a GPU and is not free, so it is out of scope for this
deployment. The `boltz` field remains on `ScreeningResult` for forward
compatibility but nothing in the pipeline populates it in normal operation and
nothing in the UI reads it.

---

## 3. Module Structure

```
src/drugforge/
├── domain/
│   ├── models.py         # ScreeningResult, Target, DockingBox, etc. Pure, no I/O.
│   └── targets.py        # TARGETS registry, get_target
├── chem/
│   ├── resolver.py        # name -> canonical SMILES
│   ├── validator.py        # resolver wrapped for a stable ValidationError boundary
│   ├── ligand.py           # SMILES -> 3D Mol + PDBQT, pH 7.4 protonation
│   ├── receptor.py         # RCSB download, cofactor-aware cleaning, PDBQT prep
│   ├── crystal.py          # extract a co-crystallised ligand for redocking
│   ├── molblock.py         # atoms/coords -> RDKit Mol, bond-order recovery
│   ├── descriptors.py      # Lipinski/Veber drug-likeness
│   └── admet.py            # PAINS/Brenk/NIH, ESOL, reactive groups, hit gate
├── docking/
│   ├── engine.py           # Vina wrapper, PDBQT <-> mol block conversion
│   ├── rescoring.py        # Vinardo rescoring of an existing pose
│   └── consensus.py        # weighted Vina/Vinardo combination
├── ai/
│   ├── explainer.py         # DeepSeek grounded explanation
│   └── boltz.py             # unused stub, kept for the ScreeningResult field
├── pipeline/
│   ├── runner.py            # run_screening: the orchestrator above
│   └── comparison.py        # reference baseline, comparisons, verdict
├── storage/
│   ├── database.py          # SQLite connection + migrations
│   └── repository.py        # save/get a ScreeningResult
├── analytics/
│   └── benchmarks.py        # AUC/EF/RMSD pure functions, artifact loading
├── reporting/
│   └── pdf.py               # PDF export (fpdf2)
├── content/
│   └── library.py            # ethnobotanical registry
├── web/
│   ├── app.py                # FastAPI app, SPA route registration
│   └── routes/                # one module per resource
└── config.py                  # the only module reading os.environ
```

---

## 4. Error Handling Strategy

### Exception hierarchy (`src/drugforge/errors.py`)

```python
class DrugForgeError(Exception): ...
class ValidationError(DrugForgeError): ...
class ResolutionError(DrugForgeError): ...
class LigandPrepError(DrugForgeError): ...
class ReceptorError(DrugForgeError): ...
class DockingError(DrugForgeError): ...
class TargetNotFoundError(DrugForgeError): ...
class StorageError(DrugForgeError): ...
class PipelineError(DrugForgeError):
    stage: str
    cause: DrugForgeError
```

### Rules
1. Never crash: every RDKit, Open Babel, network, or Vina failure is caught at
   the stage level and wrapped in the appropriate typed error.
2. Structured API errors, mapped by exception type in
   `web/routes/screening.py` (`_STATUS_BY_CAUSE`):
   - `ValidationError` -> 422
   - `TargetNotFoundError` -> 404
   - `LigandPrepError` -> 422
   - `ReceptorError` -> 502
   - `DockingError` -> 500
3. An empty prepared receptor is rejected explicitly (REQ-10) rather than
   silently docking against nothing and reporting a meaningless affinity.
4. pH-7.4 protonation never fails the pipeline: any Open Babel problem falls
   back to the un-protonated input SMILES.

---

## 5. Property-Based Testing Strategy

### Invariant 1: Reproducibility
Dock a fixed molecule N=3 times at fixed exhaustiveness; assert
`max(scores) - min(scores) < 0.5` kcal/mol. Vina's search is not perfectly
deterministic, so the tolerance is a spread, not exact equality.

### Invariant 2: Positive/Negative Controls
Dock the reference drug plus glucose and ethanol on the same target; assert
the reference scores better (more negative) than both. Verified for all four
registered targets.

### Invariant 3: Redocking (RMSD)
Extract the co-crystallised ligand from the cached PDB, redock it, and compute
symmetry-corrected heavy-atom RMSD against the crystal pose
(`analytics.benchmarks.compute_rmsd`). A cofactor-heavy pocket can make ligand
extraction fail; that is reported as `skipped` with a reason, not hidden.

### Invariant 4: Input Robustness
Hypothesis-generated ASCII strings passed to `validate_molecule`; assert either
a valid SMILES is returned or `ValidationError` is raised, never an unhandled
exception.

### Invariant 5: Scores Relative to Reference
Every successful screening result has a non-empty `comparisons` list; every
`Comparison` has both `molecule_value` and `reference_value` populated.

### Test markers
- `slow`: invokes Vina.
- `property`: Hypothesis-based.
- Default `pytest -m "not slow"` excludes Vina runs; CI/local full runs include them.
