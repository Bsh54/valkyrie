# Consensus Scoring — Design

#[[file:.kiro/specs/consensus-scoring/requirements.md]]

---

## 1. Scoring Strategy

### Second scoring function: RDKit descriptor-based re-scoring

Instead of a second docking engine (too heavy for 8 GB VPS), we use a
**knowledge-based interaction fingerprint score** computed from the docked pose:

1. **Interaction Fingerprint Score (IFP)** — compute protein-ligand interactions
   from the docked pose: H-bonds, hydrophobic contacts, pi-stacking proximity.
   Uses RDKit distance geometry on the pose SDF + receptor PDB coordinates.

2. **Alternative: Vinardo / ad4 scoring** — Vina supports multiple scoring
   functions (`vinardo`, `ad4`). We can rescore the same pose with `vinardo`
   as the second score — zero new dependencies, purely CPU.

**Chosen approach: Vinardo rescoring** — simplest, most reliable, no new deps.
Vina's Python API supports `score()` with different scoring functions on an
already-docked pose.

### Consensus formula

```
consensus_score = (w1 * normalized_vina) + (w2 * normalized_vinardo)
```

Where:
- `normalized_X = (X - worst_in_batch) / (best_in_batch - worst_in_batch)`
  for single-molecule mode, use the reference drug as the normalizer:
  `normalized_X = X / reference_X` (ratio, lower = better)
- Default weights: `w1 = 0.6, w2 = 0.4` (Vina is primary, Vinardo confirms)
- Consensus rank: sort by consensus_score ascending (lower = better binding)

---

## 2. Architecture Changes

```
Existing pipeline:
  ... → dock (Vina) → drug-likeness → compare → store

Extended pipeline:
  ... → dock (Vina) → RESCORE (Vinardo) → CONSENSUS → drug-likeness → compare → store
                          ↓
                    DockingResult now includes:
                      - vina_score (kcal/mol)
                      - vinardo_score (kcal/mol)
                      - consensus_score (normalized combination)
```

### New/Modified modules

| Module | Change |
|--------|--------|
| `valkyrie/rescoring.py` | NEW — Vinardo rescoring of docked pose |
| `valkyrie/consensus.py` | NEW — consensus formula, normalization, ranking |
| `valkyrie/docking.py` | MODIFIED — DockingResult gains `vinardo_score` field |
| `valkyrie/pipeline.py` | MODIFIED — adds rescore + consensus stages |
| `valkyrie/api.py` | MODIFIED — response includes both scores + consensus |
| `valkyrie/benchmarks.py` | NEW — enrichment measurement (AUC/EF) |
| `valkyrie/api.py` | MODIFIED — adds `GET /benchmarks` endpoint |

---

## 3. Enrichment Benchmarking

### Validation set: PfDHFR actives vs inactives

We need a small curated set:
- **Actives** (5-10): known PfDHFR inhibitors (pyrimethamine, cycloguanil,
  trimethoprim, methotrexate, WR99210)
- **Inactives** (10-20): random drug-like molecules known NOT to bind PfDHFR
  (glucose, ethanol, caffeine, aspirin, ibuprofen, etc.)

### Metrics
- **AUC-ROC**: area under the ROC curve (actives vs inactives ranked by score)
- **EF1%**: enrichment factor at 1% (how many actives in top 1%)
- **EF10%**: enrichment factor at 10%

### Honest reporting
- Show AUC for Vina-only vs consensus side-by-side
- If consensus does NOT improve enrichment, report that honestly
- Include confidence intervals / standard errors where possible

---

## 4. Data Model Changes

```python
@dataclass
class DockingResult:
    best_affinity: float          # Vina kcal/mol (unchanged)
    vinardo_score: float          # NEW: Vinardo rescore
    all_affinities: list[float]
    best_pose_pdbqt: str
    best_pose_sdf: str

@dataclass
class ConsensusResult:
    vina_score: float
    vinardo_score: float
    consensus_score: float        # combined normalized score
    rank_by_vina: int | None      # for batch mode
    rank_by_consensus: int | None
```

---

## 5. Property-Based Testing

### Test: Consensus determinism
```
Given: fixed molecule + fixed target + fixed exhaustiveness
When: pipeline run N=3 times
Then: all consensus_scores are identical (exact float equality)
```

### Test: Active outranks inert after consensus
```
Given: pyrimethamine (active) and glucose (inert) docked on pf-dhfr
When: both are rescored and consensus-ranked
Then: pyrimethamine.consensus_score < glucose.consensus_score (lower = better)
```
