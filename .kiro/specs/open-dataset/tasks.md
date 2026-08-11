# Open Dataset — Tasks

#[[file:.kiro/specs/open-dataset/design.md]]

---

## Task 1: Tests (write first)
- [ ] Create `tests/test_dataset.py`:
      - `validate_schema(build_dataset())` returns no violations.
      - Every row has non-empty `ethnobotanical_source` and `structural_source`.
      - A row with an empty source produces a violation (rejection path).
      - Numeric fidelity: stored `-8.123` exports as `-8.123` in JSON and CSV.
      - CSV round-trips via `csv.DictReader` with `#` comment lines skipped.
      - CSV header contains `CC-BY-4.0` and the disclaimer.
      - JSON envelope has `license`, `disclaimer`, `n_entries`.
      - Compounds without results appear as `status: "pending"` with null scores.
      - `query()` filters by disease, target, plant, hit_only.

Traces: REQ-OD-6, REQ-OD-8, REQ-OD-9, REQ-OD-10

---

## Task 2: Dataset module
- [ ] Create `drugforge/dataset.py`:
      - `SCHEMA` as the single source of truth (field, type, required, precision).
      - `LICENSE`, `DISCLAIMER` constants.
      - `build_dataset()` joining `ethnobotanical.json` with `docking_results`.
      - `validate_schema(rows) -> list[str]` collecting all violations.
      - `to_json(rows)` with metadata envelope.
      - `to_csv(rows)` with `#` comment header carrying license + disclaimer.
      - `query(rows, ...)` for the read-only API.
- [ ] Pending entries: funnel fields `null`, `status="pending"`, never dropped.
- [ ] No pandas; stdlib `csv` and `json` only.

Traces: REQ-OD-1, REQ-OD-7, REQ-OD-8, REQ-OD-9

---

## Task 3: Store lookup helper
- [ ] Add `get_results_by_molecule(smiles, target_id) -> dict | None` to
      `drugforge/store.py`, returning the most recent result for a pair.
- [ ] Index or ordered query by `timestamp DESC LIMIT 1`.
- [ ] Test: returns the latest result when several exist.

Traces: REQ-OD-1, REQ-OD-10

---

## Task 4: Build script
- [ ] Create `scripts/build_dataset.py`:
      - build -> validate -> write `data/dataset/drugforge.{json,csv}`.
      - Print violations and exit non-zero on failure.
      - Print total / computed / pending counts.
      - `--output-dir` flag.

Traces: REQ-OD-5, REQ-OD-9

---

## Task 5: License file
- [ ] Create `data/dataset/LICENSE` with the CC-BY-4.0 text and the required
      attribution statement for the data.
- [ ] Note in it that code is under the repository license, data under CC-BY-4.0.

Traces: REQ-OD-7

---

## Task 6: API endpoints
- [ ] Add to `drugforge/api.py`:
      - `GET /api/dataset` — query with `disease`, `target`, `plant`,
        `hit_only`, `limit` (default 100, max 1000); always returns metadata.
      - `GET /api/dataset/download?format=csv|json` — correct content type and
        `Content-Disposition` filename.
      - `GET /api/dataset/schema` — schema documentation as JSON.
- [ ] Test: content types, disposition header, metadata present, filters work.

Traces: REQ-OD-2, REQ-OD-3

---

## Task 7: Documentation
- [ ] Create `docs/DATASET.md`:
      - Field-by-field schema table (name, type, unit, meaning, nullability).
      - Query API reference with example requests and responses.
      - Download instructions for CSV and JSON.
      - License and attribution requirements.
      - Reproduction: `python scripts/build_dataset.py`.
      - In-silico-only disclaimer.

Traces: REQ-OD-4

---

## Task 8: Dataset page link
- [ ] Add a Dataset section to the library page or a `#/dataset` route with:
      download buttons (CSV / JSON), license statement, entry counts,
      link to `docs/DATASET.md`.
- [ ] Keep the honesty banner and disclaimer visible.

Traces: REQ-OD-2, REQ-OD-7, REQ-OD-8

---

## Task 9: Generate and validate
- [ ] Dock the 5 seed ethnobotanical compounds against PfDHFR so the dataset has
      real computed rows.
- [ ] Run `scripts/build_dataset.py`; confirm schema validation passes.
- [ ] Verify exported numbers match the stored SQLite values exactly.
- [ ] Confirm pending rows are present and marked, not hidden.
- [ ] Sync to VPS, verify the download endpoints, commit.

Traces: REQ-OD-9, REQ-OD-10

---

## Dependency Order
```
Task 1 (tests)
Task 3 (store helper)   | independent
Task 5 (license file)   | independent
Task 2 (dataset module) <- needs Task 1, 3
Task 4 (build script)   <- needs Task 2
Task 6 (API)            <- needs Task 2
Task 7 (docs)           <- needs Task 2
Task 8 (page)           <- needs Task 6
Task 9 (generate)       <- needs all
```
