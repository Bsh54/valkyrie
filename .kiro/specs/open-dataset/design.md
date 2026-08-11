# Open Dataset — Design

#[[file:.kiro/specs/open-dataset/requirements.md]]

---

## 1. Architecture

```
data/ethnobotanical.json ──┐
                           ├──> dataset.build_dataset() ──> validate_schema()
SQLite docking_results ────┘                                      │
                                                     ┌────────────┴────────────┐
                                                     ▼                         ▼
                                          data/dataset/drugforge.json   drugforge.csv
                                                     │
                                          GET /api/dataset            (query, JSON)
                                          GET /api/dataset/download   (csv | json)
```

The dataset is a **join**: ethnobotanical registry (the knowledge) x stored
docking results (the computation). Neither side is mutated.

---

## 2. Schema

One row per (compound, target) pair. Declared once in `drugforge/dataset.py`
and used for both export and validation.

| Field | Type | Required | Notes |
|---|---|---|---|
| `entry_id` | str | yes | `{compound_id}__{target_id}` |
| `compound_id` | str | yes | registry key |
| `compound_name` | str | yes | |
| `compound_smiles` | str | yes | canonical SMILES |
| `plant_scientific_name` | str | yes | |
| `plant_local_name` | str | yes | |
| `plant_family` | str | no | |
| `traditional_disease` | str | yes | |
| `region` | str | yes | |
| `people` | str | yes | |
| `preparation_method` | str | yes | decoction / infusion / ethanolic extract |
| `part_used` | str | yes | |
| `target_id` | str | yes | |
| `target_name` | str | yes | |
| `target_pdb_id` | str | yes | structural source |
| `reference_drug` | str | yes | |
| `vina_kcal_mol` | float\|null | no | null when not yet docked |
| `vinardo_kcal_mol` | float\|null | no | |
| `consensus_score` | float\|null | no | |
| `reference_vina_kcal_mol` | float\|null | no | comparison baseline |
| `delta_vs_reference` | float\|null | no | molecule - reference |
| `verdict` | str\|null | no | Promising / Comparable / Weak |
| `boltz_status` | str | yes | success / unavailable / error / skipped |
| `boltz_predicted_affinity` | float\|null | no | |
| `boltz_confidence` | float\|null | no | |
| `lipinski_violations` | int\|null | no | |
| `esol_logs` | float\|null | no | |
| `gi_absorption` | str\|null | no | |
| `pains_alerts` | str | yes | `;`-joined, `""` when none |
| `brenk_alerts` | str | yes | `;`-joined |
| `reactive_groups` | str | yes | `;`-joined |
| `admet_pass` | bool\|null | no | |
| `is_hit` | bool\|null | no | |
| `status` | str | yes | `computed` or `pending` |
| `ethnobotanical_source` | str | yes | full citation — export fails if empty |
| `structural_source` | str | yes | `RCSB PDB {pdb_id}` |
| `license` | str | yes | `CC-BY-4.0` |
| `disclaimer` | str | yes | in-silico only, non-clinical |

`status: "pending"` rows keep every funnel field `null` — visible, not hidden.

---

## 3. Module Design

### `drugforge/dataset.py`

```python
SCHEMA: dict[str, FieldSpec]           # single source of truth
LICENSE = "CC-BY-4.0"
DISCLAIMER = ("In-silico predictions only. Not clinical evidence. "
              "Laboratory validation required.")

def build_dataset() -> list[dict]
    """Join ethnobotanical registry with stored docking results."""

def validate_schema(rows: list[dict]) -> list[str]
    """Return a list of violations. Empty list means valid."""

def to_json(rows: list[dict]) -> str
    """Envelope: metadata (license, disclaimer, generated_at, counts) + rows."""

def to_csv(rows: list[dict]) -> str
    """Comment header lines (# license, # disclaimer) then CSV per SCHEMA order."""

def query(rows, disease=None, target=None, plant=None, hit_only=False) -> list[dict]
```

`validate_schema` returning violations (rather than raising) lets the exporter
report every problem at once instead of failing on the first.

### JSON envelope
```json
{
  "metadata": {
    "name": "DrugForge Ethnobotanical Docking Dataset",
    "version": "1.0",
    "generated_at": "2026-08-11T21:00:00Z",
    "license": "CC-BY-4.0",
    "disclaimer": "In-silico predictions only. Not clinical evidence...",
    "n_entries": 5,
    "n_computed": 3,
    "n_pending": 2,
    "schema": { "vina_kcal_mol": { "type": "float", "unit": "kcal/mol" } }
  },
  "entries": [ { ... } ]
}
```

### CSV header
```
# DrugForge Ethnobotanical Docking Dataset v1.0
# License: CC-BY-4.0
# DISCLAIMER: In-silico predictions only. Not clinical evidence. Lab validation required.
# Generated: 2026-08-11T21:00:00Z
entry_id,compound_id,compound_name,...
```

Comment lines use `#` so `csv`/pandas readers can skip them with `comment='#'`.

---

## 4. API

| Endpoint | Purpose |
|---|---|
| `GET /api/dataset` | Query, JSON envelope |
| `GET /api/dataset/download?format=csv\|json` | File download |
| `GET /api/dataset/schema` | Schema documentation |

### Query parameters for `GET /api/dataset`
| Param | Type | Meaning |
|---|---|---|
| `disease` | str | substring match on `traditional_disease` |
| `target` | str | exact `target_id` |
| `plant` | str | substring match on scientific or local name |
| `hit_only` | bool | keep only `is_hit == true` |
| `limit` | int | default 100, max 1000 |

Response always includes the `metadata` block, so the license and disclaimer
travel with every query result.

### Download headers
```
Content-Type: text/csv; charset=utf-8
Content-Disposition: attachment; filename="drugforge_dataset_v1.csv"
```

---

## 5. Script

### `scripts/build_dataset.py`
```
python scripts/build_dataset.py [--output-dir data/dataset]
```
1. `build_dataset()`
2. `validate_schema()` — on violations, print each and exit non-zero
3. Write `drugforge.json` and `drugforge.csv`
4. Print counts: total / computed / pending

Exit code is non-zero on validation failure so CI can gate on it.

---

## 6. File Layout

```
drugforge/
├── dataset.py            # NEW: schema, build, validate, export, query
└── api.py                # MODIFIED: 3 dataset endpoints
scripts/
└── build_dataset.py      # NEW
data/
└── dataset/
    ├── drugforge.json    # generated
    ├── drugforge.csv     # generated
    └── LICENSE           # CC-BY-4.0 text for the data
docs/
└── DATASET.md            # NEW: schema + API documentation
```

---

## 7. Numeric Fidelity

`build_dataset` reads scores straight from the SQLite columns and applies no
transformation. Rounding is applied only at CSV serialisation, at the precision
declared in `SCHEMA` (scores: 3 decimals). The fidelity test asserts a stored
value of `-8.123` reaches the export as `-8.123`, not `-8.12`.

---

## 8. Testing Strategy

| Test | Assertion |
|---|---|
| Schema valid | `validate_schema(build_dataset())` returns `[]` |
| Every row cites a source | `ethnobotanical_source` and `structural_source` non-empty for all rows |
| Missing source rejected | a row with empty source produces a violation |
| Numeric fidelity | stored `-8.123` appears as `-8.123` in JSON and CSV |
| CSV parses back | `csv.DictReader` with `comment` skip yields the same row count |
| CSV carries license | header contains `CC-BY-4.0` and the disclaimer |
| JSON metadata | envelope has `license`, `disclaimer`, `n_entries` |
| Pending rows kept | compounds with no result appear with `status: "pending"` and null scores |
| Query filters | `disease`, `target`, `plant`, `hit_only` each narrow correctly |
| Download endpoints | CSV returns `text/csv`, JSON returns `application/json`, both with `Content-Disposition` |
