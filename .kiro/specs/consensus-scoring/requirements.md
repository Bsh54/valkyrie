# Consensus Scoring — Requirements

## Feature
Extend the docking pipeline with a second CPU-light scoring function, combine it
with the AutoDock Vina score into a consensus score, and re-rank candidates by
consensus. Measure enrichment improvement on a validation set.

## Requirements (EARS notation)

### REQ-CS-1: Second Scoring Method
The system shall rescore the top docking poses with a second scoring method that
runs on CPU (no GPU) when a docking result is produced.

### REQ-CS-2: Dual Score Reporting
The system shall report both the Vina score and a consensus score, and rank
candidates by consensus when presenting results.

### REQ-CS-3: Enrichment Benchmarking
The system shall measure whether consensus improves enrichment (AUC/EF) on the
existing PfDHFR actives/inactives set, and report it honestly on a `/benchmarks`
endpoint.

### REQ-CS-4: Determinism
The system shall produce identical consensus scores for identical inputs when
docking conditions are held constant.

### REQ-CS-5: Control Preservation
The system shall ensure that a known active compound still outranks inert controls
(glucose, ethanol) after rescoring and consensus re-ranking.

## Constraints
- CPU only (8 GB VPS, no GPU).
- No new heavy dependencies beyond RDKit and what's already installed.
- Consensus must not mask the raw Vina score — both are always visible.
