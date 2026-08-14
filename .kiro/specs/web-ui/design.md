# Web UI — Design

#[[file:.kiro/specs/web-ui/requirements.md]]

---

## 1. Architecture

Single-page application served as static files from FastAPI, no build step and
no per-page HTML files. Real paths via the History API, not hash fragments.

```
static/
├── index.html              # shell: loads Tailwind CDN, theme.js, vendored 3Dmol.js,
│                            #   router.js, api.js, components/*, pages/*, app.js
├── js/
│   ├── theme.js             # Tailwind color/type tokens (design system)
│   ├── router.js             # minimal History API router, no dependency
│   ├── api.js                 # backend client
│   ├── app.js                  # route table
│   ├── vendor/
│   │   └── 3Dmol-min.js         # self-hosted; see REQ-UI-4 for why
│   ├── components/
│   │   ├── layout.js             # Layout (marketing header/footer) + AppShell
│   │   └── viewer3d.js            # 3Dmol.js wrapper
│   └── pages/
│       ├── home.js                 # marketing landing, own layout
│       ├── lab.js                   # docking lab, AppShell
│       ├── library.js                # ethnobotanical library, AppShell
│       └── benchmarks.js              # per-target validation reports, AppShell
```

### Routing (History API, real paths)

| Path | Page | Shell |
|---|---|---|
| `/` | Home (marketing) | `Layout` |
| `/lab` | Docking lab | `AppShell` |
| `/library` | Ethnobotanical library | `AppShell` |
| `/benchmarks` | Validation reports | `AppShell` |
| `/result/:id` | Shareable result (rendered by the lab page) | `AppShell` |

FastAPI (`web/app.py`) registers each of these paths to return the same
`static/index.html`; `router.js` then resolves the actual page from
`location.pathname`. No `.html` filename ever appears in a URL.

### Two shells

`Layout` (marketing: header + nav + multi-column footer with the disclaimer)
is used only by the home page. `AppShell` (persistent left rail on desktop, a
horizontal icon bar on mobile, a sticky workspace toolbar) is used by Lab,
Library and Benchmarks, and carries no marketing chrome. This split exists
because the home page is a pitch and the tool pages are a workspace; sharing
one shell was making both worse.

---

## 2. Page Behaviour

### 2.1 Home (`/`)
Static marketing sections built from real facts about the running product (4
targets, the funnel stages, the ethnobotanical bridge). A live 3Dmol.js view
of PfDHFR (`$3Dmol.download("pdb:1J3I", ...)`) renders in the hero preview
panel; this is a real structure fetch, not a screenshot or generated image.

### 2.2 Lab (`/lab`, `/result/:id`)
- Target rail: lists all registered targets from `GET /api/targets`; selecting
  one sets the docking target for the next submission.
- Molecule input plus exhaustiveness; quick-pick list from
  `GET /api/compounds`.
- On submit: `POST /api/screenings`, then navigate to `/result/:id`.
- Result view: verdict badge, pipeline funnel (Vina, Vinardo, consensus,
  drug-likeness, ADMET; no Boltz-2 row), 3Dmol.js pose viewer, comparison
  table, ADMET panel, then the AI explanation directly beneath the funnel.
  The Vina affinity number uses a monospace numeral style.

### 2.3 Library (`/library`)
Card grid from `GET /api/compounds`. Search filters by plant name, local name,
compound name or SMILES; a disease filter is derived from the data, not
hard-coded. Each card shows a real photograph (Wikimedia Commons) keyed by
compound id, with an `onerror` fallback to a plain icon tile; a "Dock this
compound" button stores the SMILES in `sessionStorage` and navigates to
`/lab`, which reads and pre-fills it.

### 2.4 Benchmarks (`/benchmarks`)
Reads `GET /api/benchmarks`, which returns a `targets` list (one internal
report per disease). A `<select>` switches the active target and re-renders
client-side; no reload, no recomputation. For the active target: reproducibility
bar chart, positive/negative control bars, redocking RMSD (or an honest
"skipped: <reason>" panel when the ligand could not be extracted), an
enrichment summary, and an ROC curve built client-side from the enrichment
ranking rows already present in the artifact (Vina and consensus plotted
separately). No external-redocking section is rendered; that benchmark is
cancelled for this release (see benchmarks spec).

---

## 3. Ethnobotanical Data Model

Unchanged from the original design (`data/ethnobotanical.json`), still the
canonical shape read by `content/library.py` and consumed by both the Library
page and the AI explainer's traditional-use bridging:

```json
{
  "id": "cryptolepine",
  "compound_name": "Cryptolepine",
  "smiles": "Cn1c2ccccc2c2c1c1ccccc1[nH]2",
  "plant": { "scientific_name": "Cryptolepis sanguinolenta", "local_name": "Nibima", "family": "Apocynaceae" },
  "traditional_use": {
    "disease": "Malaria, fever", "region": "Ghana, West Africa", "people": "Akan",
    "preparation": "Aqueous decoction of roots", "part_used": "Roots"
  },
  "source": "Boye & Ampofo, 1983. Ghana Medical Journal."
}
```

---

## 4. API Endpoints Used

| Endpoint | Page | Purpose |
|---|---|---|
| `GET /api/targets` | Lab | Target rail |
| `GET /api/compounds` | Lab, Library | Quick-pick and library grid |
| `POST /api/screenings` | Lab | Run a screening |
| `GET /api/screenings/:id` | Lab (result view) | Load a shareable result |
| `GET /api/screenings/:id/report` | Lab (result view) | Download the PDF |
| `GET /api/benchmarks` | Benchmarks | Per-target validation reports |

---

## 5. Accessibility (WCAG 2.1 AA)

- Semantic HTML: `<header>`, `<nav>`, `<main>`, `<aside>`, `<footer>`.
- Verdict and funnel states use both colour and an icon/label, never colour alone.
- Keyboard: all links and buttons are native `<a>`/`<button>` elements.
- Colour contrast: text on the theme's surface tokens meets 4.5:1.
- Alt text on library images names the plant; the fallback icon tile is
  decorative and marked accordingly.

---

## 6. Responsive Behaviour

- `AppShell` rail collapses to a horizontal scrolling icon bar under the `md`
  breakpoint (Tailwind default, 768px).
- Card grids (`Library`, benchmark stat cards) go from 3/4 columns down to 1.
- The benchmarks ROC chart uses an SVG `viewBox` with `preserveAspectRatio`,
  so it scales without JS recalculation.

---

## 7. Colour Palette and Verdict Semantics

Palette lives in `static/js/theme.js` (Tailwind config extension), lifted from
the Stitch design tokens (`primary`, `success-docking`, `warning-energy`,
`error`, `structural-blue`, `molecular-green`, `deep-navy`, etc.).

Verdict badge colour mapping (`lab.js`):
- `Promising` -> `success-docking`
- `Comparable` -> `structural-blue`
- `Weak` -> `warning-energy`
- `Discard` -> `error`

Verdict text is computed server-side (`pipeline/comparison.py`); the frontend
only maps the string to a colour and never recomputes the threshold.
