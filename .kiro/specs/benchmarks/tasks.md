# Benchmarks — Tasks

#[[file:.kiro/specs/benchmarks/design.md]]

---

## Task 1: Tests for pure metric functions (write first)
- [ ] Create `tests/test_benchmarks.py`:
      - AUC: perfect separation -> 1.0; reversed -> 0.0; all tied -> 0.5.
      - EF: all actives in top decile -> EF10 == 10.0; uniform -> EF10 ~= 1.0.
      - RMSD: identical conformers -> 0.0.
      - `load_benchmarks()` with missing artifacts returns not-run markers,
        raises nothing.
- [ ] No Vina required; these are pure computations.

Traces: REQ-BM-1, REQ-BM-4

---

## Task 2: Metrics module
- [ ] Create `drugforge/benchmarks.py` with `compute_auc`, `compute_ef`,
      `compute_rmsd`, `load_benchmarks`.
- [ ] AUC via rank-based Mann-Whitney form (no sklearn/scipy dependency).
- [ ] `compute_rmsd` uses `rdMolAlign.GetBestRMS` for symmetry correction.
- [ ] `load_benchmarks` reads `data/benchmarks/*.json`, tolerates absence.

Traces: REQ-BM-1, REQ-BM-4

---

## Task 3: ChEMBL actives/inactives set
- [ ] Create `data/benchmark_sets/pf-dhfr_chembl.json` with `actives` and
      `inactives` arrays: name, smiles, chembl_id, activity_nm, source.
- [ ] Actives: documented PfDHFR inhibitors (pyrimethamine, cycloguanil,
      trimethoprim, methotrexate, WR99210, and further ChEMBL entries).
- [ ] Inactives: drug-like compounds with no reported PfDHFR activity.
- [ ] Cite ChEMBL target id and accession in the file header.

Traces: REQ-BM-4

---

## Task 4: Internal validation script
- [ ] Create `scripts/bench_internal.py`:
      - Redocking RMSD: extract crystal ligand, rebuild, redock, `GetBestRMS`.
      - Reproducibility: N=5 dockings, report mean/std/spread.
      - Controls: reference vs glucose and ethanol, `ordering_held` flag.
      - Enrichment: dock the ChEMBL set, compute AUC + EF1 + EF10 for Vina and
        consensus, set `consensus_improves`.
      - Write `data/benchmarks/internal.json` with config and timestamp.
- [ ] Record every skipped compound with a reason; never drop silently.
- [ ] CLI: `--exhaustiveness`, `--repeats`, `--output`.

Traces: REQ-BM-1, REQ-BM-2, REQ-BM-3, REQ-BM-4, REQ-BM-6, REQ-BM-7

---

## Task 5: External complex set (committed before first run)
- [ ] Create `data/benchmark_sets/external_complexes.json`: fixed PDB id list
      (Astex Diverse Set), committed prior to any result being generated.
- [ ] Create `data/benchmark_sets/external_selection.md` documenting the
      selection rule and the no-post-hoc-edit commitment.

Traces: REQ-BM-5

---

## Task 6: External redocking script
- [ ] Create `scripts/bench_external.py`:
      - For each PDB id: download (cached), pick largest non-water/non-ion
        HETATM ligand, rebuild, prepare receptor, box from ligand centroid,
        dock, compute `GetBestRMS`.
      - Record `status: ok|skipped` with an enumerated `reason` on skip.
      - Aggregate `attempted`, `evaluated`, `skipped`, `success_rate_under_2A`
        (over evaluated only), `median_rmsd`, and a skip-reason breakdown.
      - Echo `selection_rule` into the output.
      - Write `data/benchmarks/external.json`.
- [ ] CLI: `--limit`, `--exhaustiveness`, `--output` for partial runs.

Traces: REQ-BM-5, REQ-BM-6, REQ-BM-7

---

## Task 7: API endpoint
- [ ] Add `GET /api/benchmarks` to `drugforge/api.py` returning
      `{internal, external, scope_statement, disclaimer}`.
- [ ] Missing artifact -> `null` plus not-run marker, not a 404.
- [ ] Test: response contains `scope_statement` and `disclaimer`; skipped
      entries in an artifact survive into the response.

Traces: REQ-BM-8, REQ-BM-9

---

## Task 8: Benchmarks page
- [ ] Create `static/js/pages/benchmarks.js`, route `#/benchmarks`.
- [ ] Scope statement rendered first, visually prominent.
- [ ] Internal section: RMSD, reproducibility, controls, enrichment with Vina
      and consensus side by side.
- [ ] External section: selection rule, attempted/evaluated/skipped counts,
      success rate, median RMSD, skip-reason breakdown, per-complex table.
- [ ] "Not yet run" state when an artifact is absent.
- [ ] Reproduction commands shown on the page.
- [ ] Add nav link to `#/benchmarks`.

Traces: REQ-BM-6, REQ-BM-8, REQ-BM-9

---

## Task 9: Reproducibility documentation
- [ ] Create `scripts/README.md`: environment setup, exact commands, expected
      runtime on 4 CPU cores, and how to regenerate every published number.

Traces: REQ-BM-7

---

## Task 10: Run and validate
- [ ] Run `bench_internal.py` on the VPS; inspect artifact.
- [ ] Run `bench_external.py` with `--limit` first, then the full set.
- [ ] Verify the page renders real numbers including skipped cases.
- [ ] Report the numbers honestly even if enrichment does not improve.
- [ ] Commit artifacts and scripts.

Traces: all

---

## Dependency Order
```
Task 1 (tests)
Task 2 (metrics)      <- needs Task 1
Task 3 (ChEMBL set)   | independent
Task 5 (external set) | independent, commit before running
Task 4 (internal script)  <- needs Task 2, 3
Task 6 (external script)  <- needs Task 2, 5
Task 7 (API)              <- needs Task 2
Task 8 (page)             <- needs Task 7
Task 9 (docs)             <- needs Task 4, 6
Task 10 (run + validate)  <- needs all
```
