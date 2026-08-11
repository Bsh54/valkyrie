---
inclusion: always
---

Use property-based tests for scientific reliability. Required invariants:
(1) reproducibility — same molecule docked N times gives a stable score (within a
small epsilon); (2) positive/negative controls — the reference ligand always
scores better than inert molecules (glucose, ethanol); (3) redocking — re-docking
the co-crystallized ligand yields low RMSD vs the real pose; (4) input robustness
— an invalid SMILES is rejected cleanly without crashing; (5) every score is
reported relative to the target's reference drug. Be honest about scope in all
reported numbers.
