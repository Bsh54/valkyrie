# External Redocking Benchmark — Selection Rule

This rule was fixed and committed **before** any result was generated.

## Source
PDB complexes from the **Astex Diverse Set** (Hartshorn et al., *J Med Chem*
2007, 50:726-741), a third-party curated redocking benchmark that predates and
is independent of DrugForge. It was not assembled by us and not chosen by
inspecting our own results.

## Rules
1. The complex list in `external_complexes.json` is committed before the first
   run and is not edited afterwards.
2. Every listed complex is attempted. None is removed because it scored badly.
3. A complex that cannot be processed is reported with `status: "skipped"` and
   an enumerated reason. Skips are never silently dropped.
4. Success rates are computed over `evaluated` only, and `attempted`,
   `evaluated` and `skipped` are always published together so the denominator
   is unambiguous.
5. Docking parameters are identical for every complex: box = 20 A cube centred
   on the crystal ligand centroid, exhaustiveness as recorded in the artifact.

## Enumerated skip reasons
- `download_failed` — RCSB fetch failed
- `no_suitable_ligand` — no non-water, non-ion HETATM residue of >= 6 heavy atoms
- `ligand_rebuild_failed` — RDKit could not rebuild a valid ligand
- `receptor_prep_failed` — receptor PDBQT preparation failed
- `docking_failed` — Vina returned no pose
- `rmsd_atom_mismatch` — docked pose and crystal ligand not comparable

## Known limitations
Ligands are rebuilt from PDB coordinates without CONECT records, so bond orders
are inferred. Complexes with covalently bound ligands, heavy metals in the
binding site, or severe alternate conformations are expected to fail rebuild and
appear as skipped. This inflates the skip count relative to tools that use
curated ligand definitions, and we report it rather than working around it.
