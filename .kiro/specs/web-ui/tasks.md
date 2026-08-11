# Web UI — Tasks

#[[file:.kiro/specs/web-ui/design.md]]

---

## Task 1: Ethnobotanical seed data
- [ ] Create `data/ethnobotanical.json` with full records for:
      - Cryptolepis sanguinolenta (cryptolepine, root decoction, Ghana/Akan)
      - Artemisia annua/afra (artemisinin, infusion, East Africa)
      - Khaya senegalensis (limonoids, bark decoction, West Africa/Hausa)
      - Rauvolfia vomitoria (reserpine, root decoction, West Africa/Yoruba)
      - Nauclea latifolia (strictosamide, bark decoction, West Africa/Mandinka)
- [ ] Each entry includes: id, compound_name, smiles, plant (scientific_name,
      local_name, family), traditional_use (disease, region, people, preparation,
      part_used), source citation, disclaimer.
- [ ] Add SMILES to `data/compounds.json` if not already present.

Traces: REQ-UI-7, REQ-UI-8, REQ-UI-13

---

## Task 2: Library API endpoints
- [ ] Create `drugforge/library.py`:
      - Load `data/ethnobotanical.json` at import.
      - `get_compounds() -> list[dict]` — full ethnobotanical entries.
      - `get_compound(compound_id) -> dict | None`.
- [ ] Add to `drugforge/api.py`:
      - `GET /api/compounds` — list all ethnobotanical compounds.
      - `GET /api/compounds/{compound_id}` — single compound detail.
      - `GET /api/library/{target_id}` — pre-computed rankings (future; for now,
        returns compound list with metadata for on-demand docking).
- [ ] Write `tests/test_library.py`: endpoint returns ≥5 compounds with required fields.

Traces: REQ-UI-6, REQ-UI-7

---

## Task 3: HTML shell and CSS framework
- [ ] Rewrite `static/index.html` as the SPA shell:
      - `<header>` with site title + nav links (Screen / Library)
      - Honesty banner (permanent, non-dismissible)
      - `<main id="app">` content area (pages render here)
      - Skip-to-content link
      - Semantic structure, ARIA landmarks
- [ ] Create `static/css/style.css`:
      - CSS custom properties (color palette, spacing, fonts)
      - Layout: responsive grid with breakpoints (mobile/tablet/desktop)
      - Component styles: cards, badges, tables, forms, buttons
      - Funnel visualization styles
      - Accessibility: focus indicators, contrast ratios
      - Print styles (hide interactive elements)

Traces: REQ-UI-5, REQ-UI-11

---

## Task 4: JavaScript application core
- [ ] Create `static/js/api.js`:
      - `fetchTargets()`, `submitDock(molecule, target_id, exhaustiveness)`,
        `fetchResult(id)`, `fetchCompounds()`, `fetchLibrary(target_id)`.
      - Proper error handling + loading state support.
- [ ] Create `static/js/app.js`:
      - Hash-based router: `#/`, `#/result/:id`, `#/library`
      - Page mount/unmount lifecycle
      - Global state (current target list, loading flag)
      - `navigate(hash)` helper

Traces: REQ-UI-9, REQ-UI-12

---

## Task 5: Submit page
- [ ] Create `static/js/pages/submit.js`:
      - Molecule text input (name or SMILES) with placeholder examples
      - Quick-pick grid from ethnobotanical library (clickable compound cards)
      - Target dropdown (populated from API)
      - Exhaustiveness slider (1–32, default 8)
      - "Dock" button → POST /api/dock → navigate to #/result/:id
      - Loading spinner ("Docking in progress... ~30-60s")
      - Error display (structured API errors shown clearly)

Traces: REQ-UI-1, REQ-UI-12

---

## Task 6: Result page
- [ ] Create `static/js/pages/result.js`:
      - Load result from `GET /api/result/:id` (shareable URL)
      - Verdict badge (Promising/Comparable/Weak/Discard) with color + icon
      - Score summary: affinity, vinardo, consensus, always vs reference
      - Pipeline funnel component (pass/fail at each stage)
      - 3D viewer (3Dmol.js, loads SDF pose)
      - Comparison table (all metrics: molecule vs reference with delta)
      - ADMET details panel (alerts, solubility, GI, reactive groups)
      - Boltz-2 panel (if available: AI affinity + confidence badge)
      - "Copy shareable link" button
      - "New screening" link back to submit

Traces: REQ-UI-2, REQ-UI-3, REQ-UI-4, REQ-UI-9, REQ-UI-10

---

## Task 7: Pipeline funnel component
- [ ] Create `static/js/components/funnel.js`:
      - Vertical stage list with icons (✅ pass / ❌ fail / ⏭ skipped)
      - Each stage shows: name, score/status, reason for failure if failed
      - Stages: Vina → Vinardo → Consensus → Drug-likeness → ADMET → Boltz-2
      - Animated appearance (CSS transitions)
      - Accessible: ARIA labels on each stage status

Traces: REQ-UI-3

---

## Task 8: 3D viewer component
- [ ] Create `static/js/components/viewer3d.js`:
      - Initialize 3Dmol.js viewer in a container div
      - Load molecule SDF string → render as sticks (Jmol colorscheme)
      - Optional: load receptor surface if available
      - Controls: rotate, zoom, reset view button
      - Alt text / ARIA description
      - Responsive: viewer fills container width

Traces: REQ-UI-4

---

## Task 9: Library page
- [ ] Create `static/js/pages/library.js`:
      - Target selector (defaults to pf-dhfr)
      - Ranked compound table: rank, compound name, plant, verdict, affinity
      - Each row expandable → ethnobotanical record card:
        plant name (scientific + local), disease, region/people, preparation,
        active compound, source citation, disclaimer
      - Framing: "Traditional knowledge → molecular validation (in silico)"
      - "Dock this compound" button per row → navigates to submit with prefill
      - Reference drug highlighted in a distinct row

Traces: REQ-UI-6, REQ-UI-7, REQ-UI-8, REQ-UI-13

---

## Task 10: API integration + shareable URLs
- [ ] Wire submit page → POST /api/dock → save_result → navigate #/result/:id
- [ ] Result page loads from GET /api/result/:id on page load (supports
      bookmark/share: user lands on #/result/uuid and sees the result).
- [ ] 404 handling: if result not found, show "Result not found" with link to submit.
- [ ] Update browser title per page for bookmarking.

Traces: REQ-UI-9, REQ-UI-12

---

## Task 11: Responsive + accessibility audit
- [ ] Test all pages at 320px, 768px, 1024px, 1440px widths.
- [ ] Keyboard navigation: Tab through all interactive elements.
- [ ] Screen reader: verify ARIA labels on badges, funnel stages, 3D viewer.
- [ ] Color contrast: verify verdict badges meet 4.5:1 ratio.
- [ ] Fix any layout/accessibility issues found.

Traces: REQ-UI-11

---

## Task 12: Deploy and validate
- [ ] Sync static/ to VPS.
- [ ] Verify FastAPI serves index.html at root.
- [ ] Test end-to-end: submit → dock → result → shareable link → library.
- [ ] Commit.

---

## Dependency Order
```
Task 1 (seed data)
Task 2 (library API) ← needs Task 1
Task 3 (HTML/CSS shell) ← independent
Task 4 (JS core + router) ← needs Task 3
Task 5 (submit page) ← needs Task 4
Task 6 (result page) ← needs Task 4, 7, 8
Task 7 (funnel component) ← needs Task 4
Task 8 (3D viewer) ← needs Task 4
Task 9 (library page) ← needs Task 4, 2
Task 10 (API wiring) ← needs Tasks 5, 6, 9
Task 11 (responsive/a11y) ← needs Tasks 5, 6, 9
Task 12 (deploy) ← needs all above
```
