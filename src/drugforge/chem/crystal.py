"""Extract a co-crystallised ligand from a PDB structure.

Used by redocking benchmarks to recover the experimental pose. PDB files carry
no bond table for heteroatoms, so the ligand is rebuilt by distance perception.
"""

from __future__ import annotations

from drugforge.chem.molblock import Atom, build_mol_from_atoms

MIN_LIGAND_HEAVY_ATOMS = 6

_SOLVENTS = {"HOH", "DOD", "WAT", "SOL"}

_NON_LIGANDS = {
    "NA", "CL", "K", "MG", "CA", "ZN", "FE", "MN", "CU", "NI", "CO", "CD",
    "BR", "IOD", "SO4", "PO4", "NO3", "ACT", "EDO", "GOL", "PEG", "DMS",
    "MPD", "TRS", "EPE", "FMT", "CIT", "TLA", "MES", "IPA", "BME", "SCN",
}

_TWO_LETTER_ELEMENTS = {
    "CL": "Cl", "BR": "Br", "FE": "Fe", "ZN": "Zn", "MG": "Mg", "MN": "Mn",
    "NA": "Na", "CA": "Ca", "CU": "Cu", "SE": "Se", "NI": "Ni", "CO": "Co",
}


def _element(line: str) -> str | None:
    raw = line[76:78].strip().upper() if len(line) >= 78 else ""
    if not raw:
        raw = line[12:16].strip().upper()[:1]
    if not raw or raw == "H":
        return None
    return _TWO_LETTER_ELEMENTS.get(raw, raw.capitalize() if len(raw) > 1 else raw)


def group_heteroatom_residues(pdb_text: str) -> dict[tuple[str, str, str], list[Atom]]:
    """Group candidate ligand residues by name, chain and sequence number."""
    residues: dict[tuple[str, str, str], list[Atom]] = {}

    for line in pdb_text.splitlines():
        if not line.startswith("HETATM"):
            continue

        residue_name = line[17:20].strip().upper()
        if residue_name in _SOLVENTS or residue_name in _NON_LIGANDS:
            continue

        element = _element(line)
        if element is None:
            continue

        try:
            x, y, z = float(line[30:38]), float(line[38:46]), float(line[46:54])
        except (ValueError, IndexError):
            continue

        key = (residue_name, line[21:22].strip(), line[22:26].strip())
        residues.setdefault(key, []).append((element, x, y, z))

    return residues


def find_primary_ligand(pdb_text: str) -> tuple[str, list[Atom]] | None:
    """Return the largest plausible ligand as (residue name, atoms)."""
    residues = group_heteroatom_residues(pdb_text)
    if not residues:
        return None

    key, atoms = max(residues.items(), key=lambda item: len(item[1]))
    if len(atoms) < MIN_LIGAND_HEAVY_ATOMS:
        return None
    return key[0], atoms


def centroid(atoms: list[Atom]) -> tuple[float, float, float]:
    count = len(atoms)
    return (
        round(sum(atom[1] for atom in atoms) / count, 3),
        round(sum(atom[2] for atom in atoms) / count, 3),
        round(sum(atom[3] for atom in atoms) / count, 3),
    )


def crystal_ligand(pdb_text: str):
    """Rebuild the primary ligand as an RDKit molecule, or None."""
    found = find_primary_ligand(pdb_text)
    return build_mol_from_atoms(found[1]) if found else None
