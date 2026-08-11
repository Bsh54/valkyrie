# ADMET Filter — Requirements

## Feature
Add an ADMET/toxicity filtering stage after scoring. Flag candidates as hits only
if they pass both drug-likeness and ADMET/tox filters. Show clear reasons for
filtering and carry an honest in-silico disclaimer on all outputs.

## Requirements (EARS notation)

### REQ-AF-1: ADMET Property Computation
The system shall compute, on CPU using RDKit-based models, ADMET-style properties
when a candidate molecule is scored. Properties include:
- Absorption/solubility proxies (ESOL predicted logS, GI absorption estimate)
- Structural toxicity alerts (PAINS filters, Brenk alerts)
- Reactive group flags (Michael acceptors, alkyl halides, etc.)

### REQ-AF-2: Hit Determination
The system shall flag a candidate as a "hit" only if it passes both drug-likeness
(Lipinski + Veber) and the ADMET/toxicity filter when reporting results.

### REQ-AF-3: Filter Transparency
The system shall clearly show WHY a molecule was filtered (which specific alert
fired, which threshold was exceeded) when a candidate fails the ADMET check.

### REQ-AF-4: Honest Disclaimer
All outputs shall carry an honest, in-silico-only, non-clinical disclaimer. The
system shall never claim a filtered/passing result constitutes medical evidence.

### REQ-AF-5: Toxicophore Detection
The system shall detect known structural toxicophores (PAINS substructures, Brenk
unwanted fragments) and report them by name when present in a candidate molecule.

### REQ-AF-6: Clean Molecule Pass-Through
The system shall allow a clean drug-like molecule (no alerts, passes all filters)
to proceed to final ranking without false-positive filtration.

## Constraints
- CPU only, RDKit-based. No external ADMET API calls.
- Use RDKit's built-in filter catalogs (PAINS, BRENK, NIH, ZINC).
- Never present ADMET predictions as clinical toxicology data.
