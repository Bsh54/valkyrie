# Benchmarks — Requirements

## Feature
A public `/benchmarks` page reporting internal validation on PfDHFR and an
external, independent redocking benchmark on public RCSB PDB complexes, with an
honest scope statement. All numbers are produced by reproducible scripts shipped
in the repository.

## Requirements (EARS notation)

### REQ-BM-1: Redocking RMSD (internal)
The system shall report the redocking RMSD of each target's co-crystallized
ligand against its crystal pose when the internal validation suite is run,
including the number of complexes evaluated and the RMSD < 2.0 A success rate.

### REQ-BM-2: Reproducibility
The system shall report reproducibility as the observed score spread
(+/- kcal/mol) across N repeated dockings of a fixed molecule under fixed
conditions, stating N, the exhaustiveness, and the random seed policy.

### REQ-BM-3: Positive/Negative Controls
The system shall report the docking scores of the reference ligand (positive
control) alongside inert molecules (glucose, ethanol) as negative controls, and
state explicitly whether the expected ordering held.

### REQ-BM-4: Enrichment (AUC + EF)
The system shall report enrichment on a ChEMBL-derived PfDHFR actives/inactives
set as AUC-ROC and enrichment factor (EF1%, EF10%), reported separately for the
Vina score and the consensus score so any improvement or absence of improvement
is visible.

### REQ-BM-5: External Independent Redocking
The system shall run a redocking benchmark on a set of public RCSB PDB complexes
selected by a documented, method-agnostic rule (not hand-picked to favour the
method), and shall record the selection rule in the published output.

### REQ-BM-6: Skipped Cases Are Reported
The system shall report complexes whose ligand cannot be rebuilt or prepared as
`skipped`, with the reason, in the published results. Skipped cases shall never
be silently omitted from counts.

### REQ-BM-7: Reproducibility Scripts
The system shall ship the scripts that produce every published number, runnable
on CPU, so a third party can regenerate the results independently.

### REQ-BM-8: Honest Scope Statement
The `/benchmarks` page shall carry an explicit scope statement declaring: these
are in-silico benchmarks of a docking pipeline, not a clinical or experimental
validation; docking scores are weak predictors of true affinity; results are
reported as-is including failures.

### REQ-BM-9: Public Page and API
The system shall expose the benchmark results at a public `/benchmarks` page and
via `GET /api/benchmarks`, reading from stored generated results rather than
recomputing on request.

## Constraints
- CPU only (8 GB VPS, no GPU). Long-running benchmarks execute offline via script,
  not inside an HTTP request.
- No cherry-picking: the external complex selection rule is fixed before running.
- Results are stored as JSON artifacts in the repo/data dir and served read-only.
- Every reported metric states its sample size.
