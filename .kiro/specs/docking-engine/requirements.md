# Docking Engine — Requirements

## Feature
A molecular docking engine with a target registry, covering four neglected
tropical diseases: malaria, Chagas disease, leishmaniasis and sleeping sickness.
Adding a disease is one registry entry; the pipeline stays unchanged.

## Requirements (EARS notation)

### REQ-1: Molecule Input
The system shall accept a molecule as a common name or a SMILES string.

### REQ-2: pH 7.4 Protonation
The system shall protonate the ligand to its dominant state at pH 7.4 before 3D
embedding, using Open Babel, falling back to the input SMILES unchanged if
protonation fails for any reason. This mirrors the ionisation state the molecule
would carry in the body and never fails the pipeline.

### REQ-3: 3D Embedding and PDBQT
The system shall embed the protonated molecule in 3D (RDKit ETKDGv3 + MMFF) and
convert it to PDBQT (Meeko) when a docking request is made.

### REQ-4: Docking Execution
The system shall dock the molecule against the selected target using AutoDock
Vina and return the best affinity score (kcal/mol) and the 3D pose.

### REQ-5: Drug-Likeness
The system shall compute drug-likeness (molecular weight, logP, H-bond
donors/acceptors, TPSA, Lipinski violations).

### REQ-6: Reference Comparison
The system shall report each score relative to the target's reference drug.

### REQ-7: Target Registry
The system shall load targets from a registry where each target declares its
PDB id, docking box (derived from the co-crystallised ligand centroid, capped at
22.5 A per axis to keep the search focused and CPU-light), and reference drug.

### REQ-8: Cofactor Retention
The system shall retain functionally essential cofactors (haem, NAD(P),
flavins, iron-sulfur clusters, PLP) in the prepared receptor as HETATM records,
while still removing water, ions and the co-crystallised inhibitor. Docking a
cofactor-dependent target (e.g. a CYP51 haem enzyme) without its cofactor
produces a physically meaningless pocket.

### REQ-9: Receptor Preparation Without Gasteiger Charges
The system shall prepare the receptor PDBQT without Gasteiger partial charges.
AutoDock Vina scores by atom type, not partial charge, and Gasteiger charge
assignment fails on cofactor metals (for example the haem iron), which can
silently drop the cofactor or empty the receptor entirely.

### REQ-10: Empty Receptor Guard
The system shall reject a prepared receptor that contains no ATOM or HETATM
records after preparation, raising a clear error instead of docking against an
empty structure and reporting a meaningless affinity.

### REQ-11: Input Validation
The system shall reject an invalid SMILES with a clear error and no crash.

## Target Registry

| id | disease | PDB | reference drug | box (A, per axis) |
|---|---|---|---|---|
| pf-dhfr | malaria | 1J3I | pyrimethamine | 20.0 |
| tc-cyp51 | Chagas disease | 3K1O | fluconazole | 22.5 |
| lm-ptr1 | leishmaniasis | 1E7W | methotrexate | 22.5 |
| tb-ptr1 | sleeping sickness | 2WD8 | methotrexate | 22.5 |

Note on the Chagas reference: posaconazole was the first choice but its
repeated docking exceeded the benchmark timeout on the 8 GB VPS. Fluconazole is
a smaller clinical azole that also targets CYP51, docks in roughly one minute,
and is used instead for both the benchmark and every lab run against tc-cyp51.

## Constraints
- 8 GB VPS, no GPU — all computation runs on CPU, one molecule at a time.
- No simulated or hard-coded results — docking must actually run.
- Prefer standard library and well-established scientific packages.
