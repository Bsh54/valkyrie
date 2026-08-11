# Boltz-2 Confirmation — Tasks

#[[file:.kiro/specs/boltz-confirmation/design.md]]

---

## Task 1: Property-based tests (write first)
- [ ] Create `tests/test_boltz.py`:
      - **Missing API key**: unset `BOLTZ_API_KEY`, call pipeline, assert
        `result.boltz.status == "unavailable"` and pipeline completes normally.
      - **Top-N gating**: mock Boltz API, process 5 molecules, assert only
        top 3 (default N) have boltz called.
      - **Graceful failure**: mock API to return 500, assert
        `result.boltz.status == "error"` and pipeline still returns valid
        physics scores.
      - **ADMET-filtered skip**: molecule that failed ADMET is never sent to
        Boltz even if it would rank in top-N.
- [ ] No `@pytest.mark.slow` — all Boltz tests use mocked HTTP.

Traces: REQ-BC-3, REQ-BC-5, REQ-BC-6

---

## Task 2: Boltz client module
- [ ] Create `drugforge/boltz.py`:
      - `BoltzResult` dataclass with status, predicted_affinity, confidence,
        error_detail, disclaimer.
      - `is_boltz_available() -> bool` — checks env var.
      - `call_boltz_api(smiles, target_pdb_id, pose_sdf) -> BoltzResult` —
        HTTP POST with 30s timeout, catches all exceptions.
      - `should_run_boltz(rank, passed_admet, top_n) -> bool` — gating logic.
      - `BOLTZ_TOP_N = 3` configurable constant.

Traces: REQ-BC-1, REQ-BC-2, REQ-BC-3

---

## Task 3: Pipeline integration
- [ ] Modify `drugforge/pipeline.py`:
      - Add optional Boltz-2 stage at the end (after compare, before store).
      - Only invoke if `should_run_boltz()` returns True.
      - Add `boltz: BoltzResult | None` to `PipelineResult`.
- [ ] Modify `PipelineResult.to_dict()` to include boltz data or null.

Traces: REQ-BC-1, REQ-BC-5

---

## Task 4: API and response updates
- [ ] Modify `POST /api/dock` response to include `boltz` field.
- [ ] Add clear "experimental/AI" label in response metadata.
- [ ] Update frontend to show Boltz-2 section only when status="success":
      - AI Affinity badge with confidence percentage.
      - Clear "Experimental AI Prediction" label.
      - Disclaimer text.

Traces: REQ-BC-4

---

## Task 5: Configuration
- [ ] Add to `drugforge/config.py`:
      - `BOLTZ_API_URL` (default: "https://api.boltz.bio/v2/predict")
      - `BOLTZ_API_TIMEOUT` (default: 30 seconds)
      - `BOLTZ_TOP_N` (default: 3)
- [ ] Document in project README that `BOLTZ_API_KEY` must be set as env var.
- [ ] Add `BOLTZ_API_KEY` to `.gitignore` / env example.

Traces: REQ-BC-2

---

## Task 6: Store schema update
- [ ] Add `boltz_json` column to `docking_results` table.
- [ ] Update `save_result()` and `get_result()` in `drugforge/store.py`.

---

## Task 7: Integration validation
- [ ] Run full test suite (mocked Boltz tests + existing tests).
- [ ] Verify missing-key test passes.
- [ ] Verify top-N gating test passes.
- [ ] Verify graceful-failure test passes.
- [ ] Commit.

---

## Dependency Order
```
Task 1 (tests first)
Task 2 (boltz client) ← pure module, no deps beyond requests
Task 3 (pipeline) ← needs Task 2
Task 4 (API/frontend) ← needs Task 3
Task 5 (config) ← parallel with Task 2
Task 6 (store) ← parallel with Task 3
Task 7 (validation)
```
