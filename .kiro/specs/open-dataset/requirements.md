# Open Dataset — Requirements

## Feature
An open, reusable dataset layer linking traditional ethnobotanical knowledge to
in-silico molecular validation results, published as CSV + JSON under an explicit
open license, with a public download endpoint and a read-only query API.

## Requirements (EARS notation)

### REQ-OD-1: Dataset Assembly
The system shall assemble a machine-readable dataset (CSV + JSON) linking, for
each entry:
- plant scientific name and local name
- traditionally-treated disease
- region and people
- traditional preparation method and part used
- active compound name and SMILES
- disease protein target and PDB id
- full funnel results: Vina score, Vinardo score, consensus score, Boltz-2
  confirmation, ADMET/tox flags, comparison to the reference drug

### REQ-OD-2: Public Download Endpoint
The system shall expose a public download endpoint serving the dataset in both
CSV and JSON formats, with correct content types and download filenames.

### REQ-OD-3: Read-Only Query API
The system shall expose a simple read-only public API to query the dataset,
supporting filtering by disease, target, plant, and hit status, with documented
parameters and response shape.

### REQ-OD-4: Documentation
The system shall document the dataset schema (every column: name, type, unit,
meaning) and the query API, and shall publish that documentation alongside the
data.

### REQ-OD-5: Reproducibility Scripts
The system shall ship the scripts that regenerate the dataset from stored docking
results, so a third party can rebuild it independently.

### REQ-OD-6: Source Citation
The system shall cite every ethnobotanical source and every structural source
(PDB id) for each row. A row without a source shall be rejected at export time.

### REQ-OD-7: Open License
The system shall publish the dataset under an explicit open license (CC-BY-4.0
for data), stated in the export files, the download response, and the repository.

### REQ-OD-8: Disclaimer on All Exports
The system shall carry the in-silico-only, non-clinical disclaimer on every
export: in the JSON metadata block, as CSV header comment lines, and in the API
response envelope.

### REQ-OD-9: Schema Validity
The system shall validate the exported dataset against a declared schema before
publishing, failing the export if any required field is missing or mistyped.

### REQ-OD-10: Numeric Fidelity
The numbers in the export shall match the computed results stored in the
database exactly, with no rounding beyond the documented precision and no
placeholder or simulated values.

## Constraints
- CPU only, standard library `csv` and `json` (no pandas dependency).
- Dataset is generated from the SQLite results store plus the ethnobotanical
  registry; it is never hand-edited.
- Entries with no docking result yet are exported with explicit `null` funnel
  fields and a `status` marker, not omitted silently.
- License: CC-BY-4.0 for data; code remains under the repository license.
