# ADMET Filter — Tasks

#[[file:.kiro/specs/admet-filter/design.md]]

---

## Task 1: Property-based tests (write first)
- [ ] Create `tests/test_admet.py`:
      - **Toxicophore flagged**: molecule with rhodanine (PAINS) is flagged,
        `passes_filter == False`, `pains_alerts` is non-empty.
      - **Clean molecule passes**: pyrimethamine passes all filters,
        `passes_filter == True`, `failure_reasons` is empty.
      - **Disclaimer present**: every ADMETResult has non-empty DISCLAIMER
        containing "in-silico".
      - **Reactive group detection**: molecule with Michael acceptor is flagged.
- [ ] Mark deterministic tests as standard; no `@pytest.mark.slow` needed
      (ADMET is purely computational, < 1s).

Traces: REQ-AF-2, REQ-AF-3, REQ-AF-5, REQ-AF-6

---

## Task 2: ADMET module
- [ ] Create `valkyrie/admet.py`:
      - `compute_admet(mol: Mol) -> ADMETResult`
      - ESOL logS using Delaney equation (MW, logP, rotatable bonds, aromatic proportion)
      - GI absorption from TPSA + logP (Egan model)
      - PAINS filter using `rdkit.Chem.FilterCatalog` with PAINS_A/B/C
      - Brenk filter using FilterCatalog with BRENK params
      - NIH filter using FilterCatalog with NIH params
      - Reactive groups via SMARTS matching (list of known reactive SMARTS)
      - `is_hit(drug_likeness, admet) -> tuple[bool, list[str]]` combining all checks

Traces: REQ-AF-1, REQ-AF-5

---

## Task 3: Pipeline integration
- [ ] Modify `valkyrie/pipeline.py`:
      - Add ADMET computation after drug-likeness stage.
      - Add `admet: ADMETResult` and `is_hit: bool` to `PipelineResult`.
      - Include `failure_reasons` in result.
- [ ] Modify `PipelineResult.to_dict()` to include ADMET data + disclaimer.

Traces: REQ-AF-2, REQ-AF-3, REQ-AF-4

---

## Task 4: API and frontend updates
- [ ] Modify `POST /api/dock` response to include `admet` object and `is_hit`.
- [ ] Add disclaimer text to every dock response.
- [ ] Update `static/index.html`:
      - Show "HIT" or "FILTERED" badge based on `is_hit`.
      - If filtered, show failure reasons in a warning box.
      - Always show the disclaimer below results.

Traces: REQ-AF-3, REQ-AF-4

---

## Task 5: Store schema update
- [ ] Add `admet_json` and `is_hit` columns to `docking_results` table.
- [ ] Update `save_result()` and `get_result()` in `valkyrie/store.py`.

Traces: persistence

---

## Task 6: Integration validation
- [ ] Run full test suite, confirm no regressions.
- [ ] Verify toxicophore test passes.
- [ ] Verify clean molecule test passes.
- [ ] Commit.

---

## Dependency Order
```
Task 1 (tests first)
Task 2 (ADMET module) ← needs RDKit FilterCatalog
Task 3 (pipeline) ← needs Task 2
Task 4 (API/frontend) ← needs Task 3
Task 5 (store) ← parallel with Task 3/4
Task 6 (validation)
```
