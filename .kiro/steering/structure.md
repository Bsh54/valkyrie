Every disease target is one entry in a target registry. Each target declares:
PDB structure id, binding pocket / docking box (from co-crystallized ligand),
reference drug, validation datasets. Adding a disease = adding one registry entry
plus its spec. The screening pipeline is a multi-stage FUNNEL, identical across all
targets: prepare target -> dock (Vina) -> consensus rescoring -> Boltz-2 AI
confirmation (cloud API, top candidates only) -> ADMET/tox filter -> compare to
reference drug. Compute constraint: 8GB VPS, no GPU — Vina/RDKit/consensus/ADMET run
on CPU one molecule at a time; Boltz-2 is cloud API only. The molecule library is
ETHNOBOTANICAL: African medicinal-plant compounds each carry plant name (scientific
+ local), traditionally-treated disease, region/people, preparation method, active
compound, and cited source. DrugForge bridges traditional knowledge to in-silico
molecular validation.
