# Report Export — Tasks

#[[file:.kiro/specs/report-export/design.md]]

---

## Task 1: Tests (write first)
- [ ] Create `tests/test_report.py`:
      - **Report produced**: mock a stored result, call generate_report(),
        assert returns non-empty bytes starting with PDF magic bytes (`%PDF`).
      - **Contains real numbers**: generate report for a result with
        affinity=-8.1, assert "-8.1" appears in the PDF text.
      - **API endpoint**: use FastAPI TestClient, mock store.get_result,
        assert GET /api/result/{id}/report returns 200 + PDF content-type.
      - **Not found**: non-existent ID returns 404.

Traces: REQ-RE-1, REQ-RE-4

---

## Task 2: Install fpdf2 dependency
- [ ] Add `fpdf2` to requirements.txt.
- [ ] Install on VPS: `.venv/bin/pip install fpdf2`.

---

## Task 3: Report generation module
- [ ] Create `valkyrie/report.py`:
      - `render_molecule_image(smiles) -> bytes` — RDKit 2D depiction as PNG.
      - `generate_report(result: dict) -> bytes` — builds the full PDF:
        - Header with disclaimer banner
        - Molecule identity section
        - Verdict badge (text-based in PDF)
        - Pipeline funnel (pass/fail list)
        - 2D molecule image embedded
        - Comparison table
        - ADMET details
        - AI explanation (if present in result)
        - Footer disclaimer
      - Returns PDF as bytes.

Traces: REQ-RE-2, REQ-RE-3, REQ-RE-5, REQ-RE-6

---

## Task 4: API endpoint
- [ ] Add `GET /api/result/{id}/report` to `valkyrie/api.py`:
      - Load result from store.
      - Call generate_report(result).
      - Return Response with content_type="application/pdf" and
        Content-Disposition header for download.
      - 404 if result not found.

Traces: REQ-RE-1

---

## Task 5: Validate
- [ ] Sync to VPS, install fpdf2, run tests.
- [ ] Verify PDF opens correctly with actual computed data.
- [ ] Commit.

---

## Dependency Order
```
Task 1 (tests)
Task 2 (install dep)
Task 3 (report module) ← needs fpdf2
Task 4 (API endpoint) ← needs Task 3
Task 5 (validate)
```
