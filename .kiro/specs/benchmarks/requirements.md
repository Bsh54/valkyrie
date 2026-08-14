# Benchmarks — Requirements

## Feature
A public `/benchmarks` page reporting internal validation per disease target
(malaria, Chagas disease, leishmaniasis, sleeping sickness), with a target
switcher and an honest scope statement. All numbers are produced by reproducible
scripts shipped in the repository.

## Status
The external independent redocking benchmark (REQ-BM-5 as originally written)
is cancelled for this release. It required a fixed Astex-derived complex list
and a multi-hour Colab run that was not completed; the benchmarks page does not
show an external section. If revived later, it must follow REQ-BM-5 through
REQ-BM-7 unchanged: a pre-committed, method-agnostic complex list, honest
skip reporting, and shipped reproduction scripts.

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
The system shall report enrichment on a ChEMBL-derived actives/inactives set as
AUC-ROC and enrichment factor (EF1%, EF10%), reported separately for the Vina
score and the consensus score so any improvement or absence of improvement is
visible. This requirement currently applies to pf-dhfr only, since only
`pf-dhfr_chembl.json` exists; the other three targets report enrichment as
"not run" honestly rather than omitting the section.

### REQ-BM-4b: Multi-Target Reporting
The system shall report internal validation per target, one artifact per
target id (`internal.json` for the primary target, `internal_<target_id>.json`
for each additional target), and shall expose all available targets through a
`targets` list in the API response so the page can switch between diseases.
The top-level `internal` field is kept for backward compatibility and always
mirrors the primary target's report.

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
recomputing on request. Since the redocking RMSD for a cofactor target can be
skipped for a documented structural reason (for example the co-crystallised
ligand cannot be rebuilt while the essential cofactor is present), that skip
shall be reported as a known limitation on the page, not hidden or averaged away.

### REQ-BM-10: ROC Curve
The `/benchmarks` page shall render an ROC curve for the active target,
computed client-side from the enrichment ranking (Vina and consensus scores
against the actives/inactives labels already present in the artifact), so the
separation between actives and decoys is visible, not just the summary AUC.

## Constraints
- CPU only (8 GB VPS, no GPU). Long-running benchmarks execute offline via script,
  not inside an HTTP request.
- No cherry-picking: the external complex selection rule is fixed before running.
- Results are stored as JSON artifacts in the repo/data dir and served read-only.
- Every reported metric states its sample size.
