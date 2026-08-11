# Benchmarks — Design

#[[file:.kiro/specs/benchmarks/requirements.md]]

---

## 1. Architecture

Benchmarks are computed **offline** by scripts, never inside an HTTP request.
The scripts write JSON artifacts; the API and page serve those artifacts.

```
scripts/bench_internal.py ──┐
                            ├──> data/benchmarks/internal.json ──┐
scripts/bench_external.py ──┘                                    ├──> GET /api/benchmarks
                            └──> data/benchmarks/external.json ──┘         │
                                                                            ▼
                                                                    #/benchmarks page
```

Rationale: a redocking sweep over dozens of complexes takes minutes to hours on
4 CPU cores. Running it per-request would block the server and violate the
8 GB / no-GPU constraint.

---

## 2. Internal Validation (`scripts/bench_internal.py`)

Four measurements, all on registry targets (currently PfDHFR / 1J3I).

### 2.1 Redocking RMSD
1. Extract the co-crystallized ligand from the cached PDB (HETATM records for the
   reference ligand residue).
2. Rebuild it as an RDKit mol, prepare with Meeko, dock into the same receptor.
3. Compute symmetry-corrected heavy-atom RMSD vs the crystal coordinates using
   `rdMolAlign.GetBestRMS`.
4. Report per-complex RMSD and the fraction with RMSD < 2.0 A.

### 2.2 Reproducibility
Dock the reference drug N=5 times at fixed exhaustiveness. Report
`mean`, `std`, `spread = max - min` in kcal/mol.

### 2.3 Positive/Negative Controls
Dock the reference ligand plus `glucose` and `ethanol`. Report each score and a
boolean `ordering_held` (reference strictly better than both).

### 2.4 Enrichment (AUC + EF)
- Input: `data/benchmark_sets/pf-dhfr_chembl.json` with `actives` / `inactives`
  (name + SMILES + ChEMBL id + activity value).
- Dock every compound once; collect Vina score and consensus score.
- Compute AUC-ROC and EF at 1% / 10% for **both** score types.

AUC is computed without scipy/sklearn (rank-based Mann-Whitney form):

```
AUC = (sum of ranks of actives - n_act*(n_act+1)/2) / (n_act * n_inact)
```

Enrichment factor:

```
EF(x%) = (actives_in_top_x / total_in_top_x) / (n_actives / n_total)
```

### Output: `data/benchmarks/internal.json`
```json
{
  "generated_at": "2026-08-11T21:00:00Z",
  "target_id": "pf-dhfr",
  "config": { "exhaustiveness": 8, "vina_version": "1.2.7" },
  "redocking": {
    "evaluated": 1, "skipped": 0,
    "results": [{ "pdb_id": "1J3I", "rmsd": 1.42, "status": "ok" }],
    "success_rate_under_2A": 1.0
  },
  "reproducibility": { "n": 5, "mean": -7.91, "std": 0.04, "spread": 0.10 },
  "controls": {
    "reference": { "name": "pyrimethamine", "vina": -7.9 },
    "negatives": [{ "name": "glucose", "vina": -5.1 }, { "name": "ethanol", "vina": -2.8 }],
    "ordering_held": true
  },
  "enrichment": {
    "n_actives": 20, "n_inactives": 40, "skipped": 2,
    "vina":      { "auc": 0.71, "ef1": 3.0, "ef10": 2.1 },
    "consensus": { "auc": 0.74, "ef1": 3.0, "ef10": 2.4 },
    "consensus_improves": true
  }
}
```

---

## 3. External Independent Benchmark (`scripts/bench_external.py`)

### Selection rule (fixed, documented, method-agnostic)
Stored in `data/benchmark_sets/external_selection.md` and echoed into the output
JSON so readers can audit it:

1. Source: a published, third-party curated redocking set (Astex Diverse Set
   PDB ids) — chosen because it predates and is independent of DrugForge.
2. No complex is added or removed after results are seen.
3. Every listed complex is attempted; failures are recorded as `skipped`.

The PDB id list lives in `data/benchmark_sets/external_complexes.json` and is
committed **before** the first run.

### Procedure per complex
1. Download PDB from RCSB (cached).
2. Identify the primary ligand: largest non-water, non-ion HETATM residue.
3. Rebuild ligand with RDKit + bond perception; prepare with Meeko.
   On failure → `status: "skipped"`, `reason: "ligand_rebuild_failed"`.
4. Prepare receptor via OpenBabel. On failure → `skipped`.
5. Define the box from the crystal ligand centroid, 20 A cube.
6. Dock, then compute `GetBestRMS` vs crystal pose.

### Skip reasons (enumerated, all reported)
`ligand_rebuild_failed`, `receptor_prep_failed`, `no_suitable_ligand`,
`download_failed`, `docking_failed`, `rmsd_atom_mismatch`.

### Output: `data/benchmarks/external.json`
```json
{
  "generated_at": "...",
  "selection_rule": "Astex Diverse Set, fixed list committed before run; no post-hoc edits.",
  "attempted": 85, "evaluated": 71, "skipped": 14,
  "success_rate_under_2A": 0.58,
  "median_rmsd": 1.79,
  "results": [
    { "pdb_id": "1G9V", "rmsd": 1.21, "status": "ok" },
    { "pdb_id": "1HWI", "status": "skipped", "reason": "ligand_rebuild_failed" }
  ]
}
```

`success_rate_under_2A` is computed over `evaluated` only, and the page displays
`evaluated` and `skipped` side by side so the denominator is never ambiguous.

---

## 4. Module and Script Layout

```
drugforge/
├── benchmarks.py          # NEW: load artifacts, compute AUC/EF (pure functions)
└── api.py                 # MODIFIED: GET /api/benchmarks
scripts/
├── bench_internal.py      # NEW: internal validation runner
├── bench_external.py      # NEW: external redocking runner
└── README.md              # NEW: how to reproduce
data/
├── benchmark_sets/
│   ├── pf-dhfr_chembl.json
│   ├── external_complexes.json
│   └── external_selection.md
└── benchmarks/
    ├── internal.json
    └── external.json
static/js/pages/
└── benchmarks.js          # NEW: #/benchmarks page
```

### `drugforge/benchmarks.py` public surface
```python
def compute_auc(active_scores: list[float], inactive_scores: list[float]) -> float
def compute_ef(scores: list[tuple[float, bool]], fraction: float) -> float
def compute_rmsd(probe: Mol, reference: Mol) -> float
def load_benchmarks() -> dict          # {"internal": {...}|None, "external": {...}|None}
```

Keeping AUC/EF/RMSD as pure functions makes them unit-testable without Vina.

---

## 5. API

`GET /api/benchmarks` returns:
```json
{
  "internal": { ... } | null,
  "external": { ... } | null,
  "scope_statement": "...",
  "disclaimer": "In-silico benchmark. Not clinical or experimental validation."
}
```

Missing artifacts return `null` for that section with a `status: "not_run"` marker
rather than a 404, so the page can state "not yet run" honestly.

---

## 6. Page Design (`#/benchmarks`)

```
Benchmarks

[ SCOPE ]  These are in-silico benchmarks of a docking pipeline. Docking scores
are weak predictors of true binding affinity. This is not a clinical or
experimental validation. Failures and skipped cases are shown.

-- Internal validation (PfDHFR / 1J3I) ------------------------
Redocking RMSD        1.42 A         (1 evaluated, 0 skipped)
Reproducibility       +/- 0.10       (n=5, exhaustiveness 8)
Controls              ref -7.9 < glucose -5.1, ethanol -2.8   [ordering held]
Enrichment            Vina AUC 0.71 | Consensus AUC 0.74
                      EF10%: 2.1 -> 2.4        (20 actives / 40 inactives, 2 skipped)

-- External independent redocking -----------------------------
Selection rule: Astex Diverse Set, list committed before run.
Attempted 85 | Evaluated 71 | Skipped 14
RMSD < 2.0 A: 58%   Median RMSD: 1.79 A

Skipped breakdown:  ligand_rebuild_failed 9 | receptor_prep_failed 3 | ...

[ table: pdb_id | rmsd | status | reason ]

Reproduce: python scripts/bench_internal.py && python scripts/bench_external.py
```

Design intent: enrichment shows Vina and consensus next to each other so a null
result is as visible as a positive one, and skip counts sit next to every rate.

---

## 7. Testing Strategy

Pure functions are tested without Vina:

| Test | Assertion |
|---|---|
| AUC perfect separation | actives all better -> AUC == 1.0 |
| AUC reversed | actives all worse -> AUC == 0.0 |
| AUC random/tied | all equal scores -> AUC == 0.5 |
| EF enrichment | all actives in top 10% -> EF10 == 10.0 |
| EF no enrichment | uniform distribution -> EF ~= 1.0 |
| RMSD identity | mol vs itself -> RMSD == 0.0 |
| Load missing artifact | returns None / status "not_run", no exception |
| API shape | `/api/benchmarks` returns scope_statement + disclaimer keys |
| Skipped preserved | artifact with skipped entries keeps them in the response |
