# Web UI — Requirements

## Feature
A clean, English-first web interface that tells a clear story: a user turns a
molecule intuition into a prioritized lead. Responsive, accessible, no simulated
data — calls the real backend. Every result has a shareable URL.

## Requirements (EARS notation)

### REQ-UI-1: Submit Page
The system shall present a submit page where the user can enter a molecule
(common name or SMILES), pick from the medicinal-plant compound library, or
choose a disease target when initiating a screening request.

### REQ-UI-2: Verdict Badge
The system shall display a clear VERDICT badge (Promising / Comparable / Weak /
Discard) on the result page, ALWAYS compared to the target's reference drug,
when a docking result is returned.

### REQ-UI-3: Pipeline Funnel Visualization
The system shall display a visual FUNNEL showing the molecule descending through
pipeline stages (Vina → Vinardo rescore → consensus → drug-likeness → ADMET/tox
filter), indicating what passed or failed at each stage and why, when a result
is shown. Boltz-2 AI confirmation is not part of this funnel (see REQ-UI-14).

### REQ-UI-4: 3D Binding Pose
The system shall render an interactive 3D view (3Dmol.js) of the target
structure before a run, and of the docked pose after a run, when pose or
structure data is available. The library used shall be self-hosted rather than
loaded from a third-party CDN, since CDN scripts loaded as classic `<script>`
tags can be silently dropped by a browser's cross-origin resource blocking
without any visible error, leaving the viewer empty.

### REQ-UI-3b: Explanation Placement
The AI explanation panel, when present, shall be displayed directly beneath the
pipeline funnel on the result view, and the primary affinity figure shall be
rendered in a monospace (tabular) numeral style so scores align visually across
runs.

### REQ-UI-5: Honesty Banner
The system shall permanently display an honesty banner on every page:
"In-silico predictions — not clinical advice." This banner shall never be
dismissible or hidden.

### REQ-UI-6: Library Page
The system shall provide a library page showing ranked pre-computed screening
results per target (known drugs + African medicinal-plant compounds) with
Lipinski/ADMET annotation when the user navigates to the library.

### REQ-UI-7: Ethnobotanical Records
The system shall display an ethnobotanical record for each plant compound in the
library, including: plant scientific name, local/common name, traditionally-treated
disease, region/people, traditional preparation method (aqueous decoction / infusion
/ ethanolic extract), active compound, and cited source. The UI shall frame each
result as "traditional knowledge → molecular validation (in silico)".

### REQ-UI-8: Seed Entries
The system shall include real seed entries for the library:
- Cryptolepis sanguinolenta (root decoction, cryptolepine, malaria, Ghana/Akan)
- Artemisia afra/annua (infusion, artemisinin, malaria, East/Southern Africa)
- Khaya senegalensis (bark decoction, limonoids, malaria, West Africa/Hausa)
- Rauvolfia vomitoria (root decoction, reserpine, malaria, West Africa/Yoruba)
- Nauclea latifolia (bark decoction, strictosamide, malaria, West Africa/Mandinka)

### REQ-UI-9: Shareable URLs
The system shall provide a shareable URL for each result (`/result/:id`),
allowing users to bookmark or share a specific docking result via its unique
identifier, resolved server-side without a hash fragment.

### REQ-UI-10: Reference Comparison
The system shall always show scores relative to the target's reference drug,
displaying a side-by-side comparison table with delta/ratio for every metric.

### REQ-UI-11: Responsive & Accessible
The system shall be responsive (mobile-friendly) and accessible (WCAG 2.1 AA:
keyboard navigable, semantic HTML, ARIA labels, sufficient color contrast,
screen-reader compatible).

### REQ-UI-12: Real Backend
The system shall call the real backend API (no simulated or hard-coded data).
Loading states, errors, and empty states shall be handled gracefully.

### REQ-UI-13: Source Citation
Every ethnobotanical entry shall cite its source (journal, book, or traditional
knowledge repository) and carry the in-silico-only disclaimer.

### REQ-UI-14: Application Shell for Tool Pages
The Lab, Library and Benchmarks pages shall share a persistent application
shell (left navigation rail on desktop, top bar on mobile, a sticky workspace
toolbar) with no marketing chrome. The marketing landing page (`/`) is a
separate, standalone layout and is not part of this shell.

### REQ-UI-15: Target Switcher
The Lab and Benchmarks pages shall let the user switch between all registered
disease targets. Switching targets on the Benchmarks page re-renders that
target's internal validation report without a page reload.

### REQ-UI-16: Ethnobotanical Images
Each Library card shall display a real photograph of the plant when one is
available (sourced from a public, appropriately licensed repository such as
Wikimedia Commons) and shall fall back to a plain icon when no photograph is
configured or the image fails to load. No placeholder or AI-generated stock
imagery shall be used.

### REQ-UI-17: Boltz-2 Removed from the UI
No page shall reference Boltz-2 or display an AI binding-confirmation stage.
The backend `boltz` field may remain in the API response for forward
compatibility, but the frontend shall not read or render it.

## Constraints
- HTML/CSS/JS only (no build step, no framework bundle).
- 3Dmol.js is vendored under `static/js/vendor/`, not loaded from a CDN.
- Client-side routing uses real paths via the History API
  (`/`, `/lab`, `/library`, `/benchmarks`, `/result/:id`), served by FastAPI
  returning the same `index.html` shell for each; no per-page `.html` files.
- English-first UI. No em dashes in any UI copy.
- Must work on the 8 GB VPS served by FastAPI static mount.
