# Docking Engine — Requirements

## Feature
A molecular docking engine with a target registry, implemented first for malaria
(target: Plasmodium falciparum DHFR, PfDHFR; reference drug: pyrimethamine).

## Requirements (EARS notation)

### REQ-1: Molecule Input
The system shall accept a molecule as a common name or a SMILES string when a
docking request is made. Common-name resolution shall use a local curated lookup
table (ethnobotanical compounds) first, with PubChem REST API as fallback.

### REQ-2: 3D Embedding & Ligand Preparation
The system shall embed the molecule in 3D (RDKit + MMFF force field) and convert
it to PDBQT format (Meeko) when a docking request is made.

### REQ-3: Docking Execution
The system shall dock the molecule against the selected target using AutoDock Vina
and return the best affinity score (kcal/mol) and the 3D pose. Default
exhaustiveness = 8, configurable (e.g. 4 for interactive demos).

### REQ-4: Pose Output
The system shall return the docked pose in SDF/MOL format for 3Dmol.js display.
The system shall also retain the native Vina PDBQT pose for traceability and
dataset archival.

### REQ-5: Drug-Likeness
The system shall compute drug-likeness descriptors: molecular weight, logP,
H-bond donors, H-bond acceptors, TPSA, number of rotatable bonds (Veber's rule),
and Lipinski violation count.

### REQ-6: Reference Comparison
The system shall report each score relative to the target's reference drug as a
side-by-side table (molecule vs reference) plus a simple derived delta/ratio to
drive a verdict badge.

### REQ-7: Target Registry
The system shall load targets from a Python registry module (`targets.py`) where
each target is a dataclass declaring: PDB id, docking box (center_x/y/z,
size_x/y/z), and reference drug (name + SMILES).

### REQ-8: PDB Retrieval & Caching
The system shall download the PDB structure from RCSB on first use and cache it
locally. Large receptor binaries shall not be committed to the repository — the
PDB id makes retrieval reproducible.

### REQ-9: Input Validation
The system shall reject an invalid SMILES with a clear error message and no crash
when a docking request is made with malformed input.

## Initial Target

| Disease | Target Protein | PDB | Reference Drug |
|---------|---------------|-----|----------------|
| Malaria | PfDHFR (Plasmodium falciparum dihydrofolate reductase) | 1J3I | Pyrimethamine |

## Constraints
- 8 GB VPS, no GPU — all computation (Vina, RDKit, ADMET) runs on CPU, one
  molecule at a time.
- No simulated or hard-coded results — docking must actually run.
- Prefer standard library and well-established scientific packages.
