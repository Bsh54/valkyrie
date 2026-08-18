# Docking Engine — Tasks

#[[file:.kiro/specs/docking-engine/design.md]]

Each task is traceable to one or more requirements (REQ-N) from requirements.md.

---

## Task 1: Project scaffold and configuration
- [ ] Create `valkyrie/__init__.py`.
- [ ] Create `valkyrie/config.py`: `DATA_DIR`, `RECEPTOR_CACHE_DIR`, `DB_PATH`,
      `DEFAULT_EXHAUSTIVENESS=8`, `DOCKING_TIMEOUT_S=300`.
- [ ] Create `requirements.txt`: fastapi, uvicorn[standard], rdkit-pypi, meeko,
      vina, requests, pytest, hypothesis.
- [ ] Create `data/` with `.gitkeep`.
- [ ] Add to `.gitignore`: `data/receptors/`, `data/results.db`, `__pycache__/`,
      `*.pyc`, `.venv/`.
- [ ] Create `static/` with empty placeholder.

Traces: project structure (design §3)

---

## Task 2: Error hierarchy
- [ ] Create `valkyrie/errors.py` with `ValkyrieError`, `ValidationError`,
      `ResolutionError`, `LigandPrepError`, `ReceptorError`, `DockingError`,
      `TargetNotFoundError`, `PipelineError`.

Traces: design §4

---

## Task 3: Target registry
- [ ] Create `valkyrie/targets.py` with `DockingBox`, `ReferenceDrug`, `Target`
      frozen dataclasses.
- [ ] Define `TARGETS` dict with the malaria/PfDHFR entry (PDB 1J3I,
      pyrimethamine reference, 20×20×20 Å box).
- [ ] Implement `get_target(target_id: str) -> Target` raising
      `TargetNotFoundError` for unknown IDs.
- [ ] Write `tests/test_targets.py`: valid lookup returns Target; invalid raises.

Traces: REQ-7

---

## Task 4: Molecule resolver
- [ ] Create `data/compounds.json` with ≥10 curated ethnobotanical entries
      (artemisinin, quinine, curcumin, berberine, emetine, chloroquine,
      dihydroartemisinin, luteolin, catechin, piperine) mapping name → SMILES.
- [ ] Create `valkyrie/resolver.py`:
      - Load `compounds.json` at module import.
      - `resolve(input: str) -> str`: local lookup (case-insensitive) →
        RDKit SMILES parse → PubChem REST fallback → raise `ResolutionError`.
- [ ] Write `tests/test_resolver.py`: local hit, SMILES pass-through, PubChem
      mock, failure case.

Traces: REQ-1

---

## Task 5: Input validator
- [ ] Create `valkyrie/validator.py`:
      `validate_molecule(input: str) -> str` — calls `resolve`, catches all
      exceptions, raises `ValidationError(detail=...)` on failure.
- [ ] Write `tests/test_validator.py`: valid name, valid SMILES, invalid SMILES,
      empty string, special characters — all handled without crash.

Traces: REQ-9

---

## Task 6: Ligand preparation
- [ ] Create `valkyrie/ligand_prep.py`:
      `prepare_ligand(smiles: str) -> tuple[Mol, str]`
      - Parse SMILES → add Hs → embed 3D (ETKDGv3, retry once with new seed on
        failure) → MMFF optimize → Meeko prepare → PDBQT string.
      - Raises `LigandPrepError` on failure.
- [ ] Write `tests/test_ligand_prep.py`: pyrimethamine produces valid Mol with
      3D coords and non-empty PDBQT; invalid SMILES raises error.

Traces: REQ-2

---

## Task 7: Receptor manager
- [ ] Create `valkyrie/receptor.py`:
      `get_receptor_pdbqt(target: Target) -> Path`
      - Check cache (`data/receptors/{pdb_id}/{pdb_id}.pdbqt`).
      - If missing: download PDB from RCSB, strip water/non-protein heteroatoms,
        add polar hydrogens, write PDBQT.
      - Raises `ReceptorError` on download/preparation failure.
- [ ] Write `tests/test_receptor.py`: mock HTTP download, verify PDBQT file
      is created and cached; second call uses cache (no HTTP).

Traces: REQ-8

---

## Task 8: Docking engine (Vina wrapper)
- [ ] Create `valkyrie/docking.py`:
      ```python
      @dataclass
      class DockingResult:
          best_affinity: float        # kcal/mol
          all_affinities: list[float]
          best_pose_pdbqt: str
          best_pose_sdf: str          # converted for 3Dmol.js
      ```
      `dock(ligand_pdbqt, receptor_path, box, exhaustiveness) -> DockingResult`
      - Use Vina Python API: set_receptor, set_ligand_from_string, compute_vina_maps,
        dock, get poses.
      - Convert best PDBQT pose → SDF via RDKit/OpenBabel.
      - Raises `DockingError` on Vina failure or timeout.
- [ ] Write `tests/test_docking.py`: dock pyrimethamine against pf-dhfr,
      assert affinity is negative float, SDF is non-empty. Mark `@pytest.mark.slow`.

Traces: REQ-3, REQ-4

---

## Task 9: Drug-likeness calculator
- [ ] Create `valkyrie/druglikeness.py`:
      ```python
      @dataclass
      class DrugLikeness:
          molecular_weight: float
          logp: float
          hbd: int
          hba: int
          tpsa: float
          rotatable_bonds: int
          lipinski_violations: int
      ```
      `compute_druglikeness(mol: Mol) -> DrugLikeness`
      - Uses RDKit Descriptors: MolWt, MolLogP, NumHDonors, NumHAcceptors,
        TPSA, NumRotatableBonds.
      - Lipinski violations: count of (MW>500, logP>5, HBD>5, HBA>10).
- [ ] Write `tests/test_druglikeness.py`: pyrimethamine has 0 Lipinski violations;
      a known violator (e.g. cyclosporine) has ≥2.

Traces: REQ-5

---

## Task 10: Reference comparator
- [ ] Create `valkyrie/comparator.py`:
      ```python
      @dataclass
      class Comparison:
          metric: str
          molecule_value: float
          reference_value: float
          delta: float
          ratio: float
          verdict: str  # "better" | "comparable" | "worse"
      ```
      `compare_to_reference(mol_result, mol_druglikeness, target) -> tuple[list[Comparison], str]`
      - Dock reference drug (cache result in memory/SQLite after first run).
      - Build comparisons for: affinity, MW, logP, HBD, HBA, TPSA, rotatable
        bonds, Lipinski violations.
      - Verdict badge from affinity ratio: ≤1.0 → "Promising",
        1.0–1.5 → "Comparable", >1.5 → "Weaker".
- [ ] Write `tests/test_comparator.py`: self-docking (pyrimethamine vs
      pyrimethamine) yields ratio ≈ 1.0 and badge "Comparable" or "Promising".

Traces: REQ-6

---

## Task 11: Pipeline orchestrator
- [ ] Create `valkyrie/pipeline.py`:
      `run_docking_pipeline(molecule_input, target_id, exhaustiveness) -> PipelineResult`
      - Calls: validate → prepare_ligand → get_receptor → dock → druglikeness →
        compare → returns `PipelineResult` (all fields needed by API response).
      - Wraps stage errors in `PipelineError(stage=..., cause=...)`.
- [ ] Write `tests/test_pipeline.py`: end-to-end with pyrimethamine on pf-dhfr;
      invalid input returns PipelineError with stage="validate".

Traces: design §2 (orchestration)

---

## Task 12: Results store (SQLite)
- [ ] Create `valkyrie/store.py`:
      - Auto-create `data/results.db` and table on first call.
      - `save_result(pipeline_result) -> str` (returns UUID).
      - `get_result(result_id: str) -> dict | None`.
- [ ] Write `tests/test_store.py`: save and retrieve round-trips correctly.

Traces: design §3 (persistence for open dataset goal)

---

## Task 13: FastAPI application
- [ ] Create `valkyrie/api.py`:
      - `GET /api/targets` → list targets.
      - `GET /api/targets/{target_id}` → target detail.
      - `POST /api/dock` → body `{molecule, target_id, exhaustiveness?}` →
        run pipeline → save → return full result.
      - `GET /api/result/{result_id}` → retrieve stored result.
      - Exception handlers mapping Valkyrie errors to HTTP status codes
        (422, 404, 500) with structured JSON bodies.
      - Mount `static/` for frontend.
- [ ] Write `tests/test_api.py`: use FastAPI TestClient for happy path and
      error cases (invalid SMILES → 422, unknown target → 404).

Traces: REQ-1–9 (integration)

---

## Task 14: Frontend (3Dmol.js viewer)
- [ ] Create `static/index.html`:
      - Text input for molecule (name or SMILES).
      - Dropdown for target (populated from `/api/targets`).
      - Optional exhaustiveness slider (1–32, default 8).
      - "Dock" button → POST `/api/dock` → display results.
      - Results panel: affinity, verdict badge (color-coded), comparison table.
      - 3Dmol.js viewer rendering the SDF pose + receptor surface.
      - Loading spinner during docking (~10-60s).
      - Error display for API errors.
- [ ] Include 3Dmol.js from CDN (`https://3dmol.csb.pitt.edu/build/3Dmol-min.js`).

Traces: product goal (browser-based screening)

---

## Task 15: Property-based tests (Hypothesis)
- [ ] Create `tests/test_properties.py`:
      - **Reproducibility** (invariant 1): dock pyrimethamine 3× with fixed seed,
        assert `max - min < 0.1 kcal/mol`. Mark `@pytest.mark.slow`.
      - **Positive/negative control** (invariant 2): pyrimethamine scores better
        than glucose on pf-dhfr. Mark `@pytest.mark.slow`.
      - **Input robustness** (invariant 4): `@given(st.text(max_size=200))` →
        validator never raises unhandled exception.
      - **Scores relative to reference** (invariant 5): every successful pipeline
        result contains non-empty comparison list with valid ratios.
- [ ] Add `pytest.ini` or `pyproject.toml` markers: `slow`, `property`.
- [ ] Default `pytest` excludes slow tests; `pytest -m slow` runs all.

Traces: testing steering invariants 1, 2, 4, 5

---

## Dependency Order

```
Task 1  (scaffold)
Task 2  (errors)          ← needed by all modules
Task 3  (targets)         ← needs errors
Task 4  (resolver)        ← needs errors, compounds.json
Task 5  (validator)       ← needs resolver
Task 6  (ligand prep)     ← needs validator, errors
Task 7  (receptor)        ← needs targets, config, errors
Task 8  (docking)         ← needs ligand_prep, receptor
Task 9  (drug-likeness)   ← needs RDKit only, independent of docking
Task 10 (comparator)      ← needs docking, drug-likeness, targets
Task 11 (pipeline)        ← needs all above
Task 12 (store)           ← needs config
Task 13 (API)             ← needs pipeline, store
Task 14 (frontend)        ← needs API running
Task 15 (property tests)  ← needs pipeline working end-to-end
```
