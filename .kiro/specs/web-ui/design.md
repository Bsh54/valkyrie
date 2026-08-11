# Web UI — Design

#[[file:.kiro/specs/web-ui/requirements.md]]

---

## 1. Architecture

Single-page application (SPA) served as static files from FastAPI. No build step.

```
static/
├── index.html        # Shell + router + honesty banner
├── css/
│   └── style.css     # All styles (responsive, accessible)
├── js/
│   ├── app.js        # Router, state management, page rendering
│   ├── api.js        # Backend API client
│   ├── pages/
│   │   ├── submit.js     # Submit page logic
│   │   ├── result.js     # Result page logic + funnel + 3D viewer
│   │   └── library.js    # Library page logic
│   └── components/
│       ├── funnel.js     # Pipeline funnel visualization
│       ├── viewer3d.js   # 3Dmol.js wrapper
│       ├── verdict.js    # Verdict badge component
│       └── comparison.js # Side-by-side comparison table
└── data/
    └── ethnobotanical.json  # Seed compound library with citations
```

### Routing (hash-based)
```
#/               → Submit page
#/result/:id     → Result page (shareable)
#/library        → Library page
#/library/:id    → Library entry detail
```

---

## 2. Page Designs

### 2.1 Submit Page (`#/`)

```
┌─────────────────────────────────────────────────────┐
│  🧪 DrugForge — Virtual Screening Lab               │
│  ──────────────────────────────────────────────────  │
│  ⚠ In-silico predictions — not clinical advice.     │
├─────────────────────────────────────────────────────┤
│                                                      │
│  ┌─ Enter a molecule ─────────────────────────────┐ │
│  │  [text input: name or SMILES]         [Dock]   │ │
│  └────────────────────────────────────────────────┘ │
│                                                      │
│  ── or pick from the medicinal-plant library ──      │
│  ┌──────────────────────────────────────────────┐   │
│  │ ● Cryptolepine (Cryptolepis sanguinolenta)   │   │
│  │ ● Artemisinin (Artemisia annua)              │   │
│  │ ● Reserpine (Rauvolfia vomitoria)            │   │
│  │ ● ...more                                    │   │
│  └──────────────────────────────────────────────┘   │
│                                                      │
│  Target: [dropdown: PfDHFR (Malaria) ▼]             │
│  Exhaustiveness: [slider 1-32, default 8]           │
│                                                      │
└─────────────────────────────────────────────────────┘
```

### 2.2 Result Page (`#/result/:id`)

```
┌─────────────────────────────────────────────────────┐
│  ⚠ In-silico predictions — not clinical advice.     │
├─────────────────────────────────────────────────────┤
│                                                      │
│  ┌── VERDICT ────────────────────────────────────┐  │
│  │    ████████████████████████████████████████   │  │
│  │         🟢 PROMISING                          │  │
│  │    vs. Pyrimethamine (reference drug)         │  │
│  │    Affinity: -8.3 kcal/mol (ref: -7.9)       │  │
│  │    Consensus: 1.05                            │  │
│  └───────────────────────────────────────────────┘  │
│                                                      │
│  ┌── PIPELINE FUNNEL ────────────────────────────┐  │
│  │  ▼ Vina Docking .......... ✅ -8.3 kcal/mol  │  │
│  │  ▼ Vinardo Rescore ....... ✅ -7.1 kcal/mol  │  │
│  │  ▼ Consensus ............. ✅ 1.05            │  │
│  │  ▼ Drug-likeness ......... ✅ 0 violations    │  │
│  │  ▼ ADMET/Tox Filter ...... ✅ Clean           │  │
│  │  ▼ Boltz-2 AI ............ ⏭ Unavailable     │  │
│  └───────────────────────────────────────────────┘  │
│                                                      │
│  ┌── 3D BINDING POSE ───────────────────────────┐   │
│  │                                               │   │
│  │         [3Dmol.js interactive viewer]         │   │
│  │                                               │   │
│  └───────────────────────────────────────────────┘  │
│                                                      │
│  ┌── COMPARISON TABLE ──────────────────────────┐   │
│  │ Metric     │ Molecule │ Reference │ Verdict  │   │
│  │ Affinity   │ -8.3     │ -7.9      │ better   │   │
│  │ MW         │ 282      │ 248       │ ok       │   │
│  │ logP       │ 2.1      │ 1.9       │ ok       │   │
│  │ ...        │          │           │          │   │
│  └──────────────────────────────────────────────┘   │
│                                                      │
│  ┌── ADMET DETAILS ─────────────────────────────┐   │
│  │ ESOL logS: -2.8 (acceptable)                 │   │
│  │ GI Absorption: High                          │   │
│  │ PAINS: None                                  │   │
│  │ Reactive groups: None                        │   │
│  │ Status: ✅ HIT                               │   │
│  └──────────────────────────────────────────────┘   │
│                                                      │
│  [📋 Copy link] [← New screening]                   │
│                                                      │
└─────────────────────────────────────────────────────┘
```

### 2.3 Library Page (`#/library`)

```
┌─────────────────────────────────────────────────────┐
│  ⚠ In-silico predictions — not clinical advice.     │
├─────────────────────────────────────────────────────┤
│  Screening Library — PfDHFR (Malaria)               │
│  Traditional knowledge → molecular validation       │
│                                                      │
│  ┌─ Rank │ Compound │ Plant │ Verdict │ Affinity ─┐ │
│  │  1    │ Crypto-  │ C.san │ Promi-  │ -8.1      │ │
│  │       │ lepine   │ guino │ sing    │           │ │
│  │  2    │ Artem-   │ A.ann │ Compa-  │ -7.8      │ │
│  │       │ isinin   │ ua    │ rable   │           │ │
│  │  3    │ Pyrimetha│ (ref) │ ────    │ -7.9      │ │
│  │  ...  │          │       │         │           │ │
│  └───────────────────────────────────────────────┘  │
│                                                      │
│  ── Ethnobotanical Record ──────────────────────────│
│  ┌──────────────────────────────────────────────┐   │
│  │ 🌿 Cryptolepis sanguinolenta (Nibima)        │   │
│  │ Disease: Malaria                              │   │
│  │ Region: Ghana, West Africa (Akan people)      │   │
│  │ Preparation: Aqueous root decoction           │   │
│  │ Active compound: Cryptolepine                 │   │
│  │ Source: Boye & Ampofo, 1983; Mills-Robertson  │   │
│  │         et al., 2012                          │   │
│  │                                               │   │
│  │ Traditional knowledge → in-silico validation  │   │
│  │ ⚠ Prediction only. Lab validation required.   │   │
│  └──────────────────────────────────────────────┘   │
│                                                      │
└─────────────────────────────────────────────────────┘
```

---

## 3. Ethnobotanical Data Model

```json
{
  "id": "cryptolepine",
  "compound_name": "Cryptolepine",
  "smiles": "Cn1c2ccccc2c2c1c1ccccc1[nH]2",
  "plant": {
    "scientific_name": "Cryptolepis sanguinolenta",
    "local_name": "Nibima",
    "family": "Apocynaceae"
  },
  "traditional_use": {
    "disease": "Malaria, fever",
    "region": "Ghana, West Africa",
    "people": "Akan",
    "preparation": "Aqueous decoction of roots",
    "part_used": "Roots"
  },
  "source": "Boye & Ampofo, 1983. Ghana Medical Journal.",
  "disclaimer": "In-silico prediction. Not clinical evidence."
}
```

---

## 4. API Endpoints Used

| Endpoint | Page | Purpose |
|----------|------|---------|
| `GET /api/targets` | Submit | Populate target dropdown |
| `POST /api/dock` | Submit | Execute docking |
| `GET /api/result/:id` | Result | Load stored result (shareable URL) |
| `GET /api/library/:target_id` | Library | Get pre-computed rankings (NEW) |
| `GET /api/library/compounds` | Library | List ethnobotanical compounds (NEW) |

### New endpoints needed:
- `GET /api/library/{target_id}` — returns ranked compounds with scores + ethnobotanical data
- `GET /api/compounds` — returns the full ethnobotanical compound list for selection

---

## 5. Accessibility (WCAG 2.1 AA)

- Semantic HTML: `<main>`, `<nav>`, `<article>`, `<section>`, `<header>`
- ARIA labels on interactive elements
- Keyboard navigation: all actions reachable via Tab/Enter
- Color contrast: minimum 4.5:1 for text, 3:1 for large text
- Verdict badges use both color AND text/icon (not color-alone)
- Alt text on the 3D viewer: "Interactive 3D view of [molecule] in [target] pocket"
- Skip-to-content link
- Focus indicators

---

## 6. Responsive Breakpoints

| Breakpoint | Layout |
|------------|--------|
| ≥1024px | Desktop: 2-column (form + results side by side) |
| 768–1023px | Tablet: single column, full-width cards |
| <768px | Mobile: stacked, compact funnel, horizontal scroll for table |

---

## 7. Color Palette & Verdict Badges

```css
--color-promising: #198754  /* green */
--color-comparable: #ffc107 /* amber */
--color-weak: #dc3545       /* red */
--color-discard: #6c757d    /* gray */
--color-honesty-bg: #fff3cd /* yellow warning background */
```

Verdict determination:
- **Promising**: consensus ≥ 1.0 AND is_hit AND affinity ≤ reference
- **Comparable**: consensus 0.8–1.0 AND is_hit
- **Weak**: consensus < 0.8 OR !is_hit (ADMET fail only)
- **Discard**: fails ADMET with critical alerts (PAINS, reactive groups)
