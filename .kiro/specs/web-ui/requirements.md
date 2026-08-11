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
pipeline stages (Vina → Consensus → ADMET/Tox Filter → Boltz-2 AI Confirmation),
indicating what passed or failed at each stage and why, when a result is shown.

### REQ-UI-4: 3D Binding Pose
The system shall render an interactive 3D binding pose (3Dmol.js) of the molecule
in the protein pocket when a docking result includes pose data.

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
The system shall provide a shareable URL for each result, allowing users to
bookmark or share a specific docking result via its unique identifier.

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

## Constraints
- HTML/CSS/JS only (no build step, no framework bundle).
- 3Dmol.js from CDN for molecular visualization.
- Single-page application style with client-side routing (hash-based or History API).
- English-first UI.
- Must work on the 8 GB VPS served by FastAPI static mount.
