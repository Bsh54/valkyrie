# AI Explainer — Tasks

#[[file:.kiro/specs/ai-explainer/design.md]]

---

## Task 1: Tests (write first)
- [ ] Create `tests/test_explainer.py`:
      - **Prompt contains real numbers**: build prompt with known values,
        assert the prompt string contains those exact numbers.
      - **Missing API key**: unset `DEEPSEEK_API_KEY`, call generate_explanation,
        assert status="unavailable", no crash.
      - **Disease fact sheet loaded**: call load helper for "pf-dhfr",
        assert non-empty string containing "Plasmodium" or "DHFR".
      - **Disclaimer always present**: any Explanation object has non-empty
        disclaimer containing "prediction" or "in silico".
      - **Successful API call (mocked)**: mock requests.post to return a valid
        response, assert status="success" and text is non-empty.
- [ ] No `@pytest.mark.slow` needed — all use mocked HTTP.

Traces: REQ-AE-1, REQ-AE-3, REQ-AE-4, REQ-AE-6, REQ-AE-7

---

## Task 2: Disease fact sheets
- [ ] Create `data/disease_facts/pf-dhfr.md`:
      - Disease overview (malaria, P. falciparum)
      - Target mechanism (DHFR folate pathway)
      - Reference drug context (pyrimethamine, resistance)
      - Clinical context (what affinity threshold means, validation needed)
- [ ] Add config constant `DISEASE_FACTS_DIR` to `valkyrie/config.py`.

Traces: REQ-AE-7

---

## Task 3: Explainer module
- [ ] Create `valkyrie/explainer.py`:
      - `SYSTEM_PROMPT` constant with grounding rules.
      - `build_prompt(result: dict, disease_facts: str) -> str` — template
        populated with real numbers from the result dict.
      - `load_disease_facts(target_id: str) -> str` — reads markdown file.
      - `is_explainer_available() -> bool` — checks env var.
      - `generate_explanation(result: dict, target_id: str) -> Explanation` —
        orchestrates prompt building, API call, error handling.
      - Graceful failure on: missing key, timeout, invalid response, any error.
- [ ] Add `DEEPSEEK_API_URL`, `DEEPSEEK_MODEL`, `DEEPSEEK_TIMEOUT` to config.

Traces: REQ-AE-1, REQ-AE-2, REQ-AE-3, REQ-AE-4, REQ-AE-5

---

## Task 4: Pipeline integration
- [ ] Modify `valkyrie/pipeline.py`:
      - After all stages complete, call `generate_explanation()` if available.
      - Add `explanation: Explanation | None` to `PipelineResult`.
      - Non-blocking: if explainer fails, pipeline still returns valid result.
- [ ] Update `PipelineResult.to_dict()` to include explanation.

Traces: REQ-AE-4

---

## Task 5: Store schema update
- [ ] Add `explanation_json` column to `docking_results` table.
- [ ] Update `save_result()` and `get_result()`.

---

## Task 6: API response update
- [ ] Include `explanation` field in `POST /api/dock` and `GET /api/result/{id}`.
- [ ] Ensure explanation is available for the PDF report (report-export spec).

---

## Task 7: Validate
- [ ] Sync to VPS, run tests (mocked).
- [ ] Verify prompt building produces correct context.
- [ ] Verify graceful degradation without API key.
- [ ] Commit.

---

## Dependency Order
```
Task 1 (tests)
Task 2 (fact sheets) ← independent
Task 3 (explainer module) ← needs Task 2
Task 4 (pipeline) ← needs Task 3
Task 5 (store) ← parallel with Task 4
Task 6 (API) ← needs Task 4 + 5
Task 7 (validate)
```
