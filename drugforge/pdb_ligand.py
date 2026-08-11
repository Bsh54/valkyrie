"""Extract a co-crystallised ligand from a PDB file.

Used by the redocking benchmarks to recover the crystal pose. PDB files carry no
bond table for ligands, so the molecule is rebuilt by distance-based perception.
"""

from typing import Optional

from drugforge.molblock import Atom, build_mol_from_atoms

_SOLVENTS = {"HOH", "DOD", "WAT", "SOL"}

_IONS = {
    "NA", "CL", "K", "MG", "CA", "ZN", "FE", "MN", "CU", "NI", "CO", "CD",
    "BR", "IOD", "SO4", "PO4", "NO3", "ACT", "EDO", "GOL", "PEG", "DMS",
    "MPD", "TRS", "EPE", "FMT", "CIT", "TLA", "MES", "IPA", "BME", "SCN",
}

_ELEMENT_FIX = {"CL": "Cl", "BR": "Br", "FE": "Fe", "ZN": "Zn", "MG": "Mg",
                "MN": "Mn", "NA": "Na", "CA": "Ca", "CU": "Cu", "SE": "Se"}

MIN_HEAVY_ATOMS = 6


def _element_from_pdb_line(line: str) -> Optional[str]:
    raw = line[76:78].strip().upper() if len(line) >= 78 else ""
    if not raw:
        raw = line[12:16].strip().upper()[:1]
    if not raw or raw == "H":
        return None
    return _ELEMENT_FIX.get(raw, raw.capitalize() if len(raw) > 1 else raw)


def extract_hetatm_residues(pdb_text: str) -> dict[tuple[str, str, str], list[Atom]]:
    """Group HETATM records by (residue name, chain, sequence number)."""
    residues: dict[tuple[str, str, str], list[Atom]] = {}
    for line in pdb_text.splitlines():
        if not line.startswith("HETATM"):
            continue
        res_name = line[17:20].strip().upper()
        if res_name in _SOLVENTS or res_name in _IONS:
            continue
        element = _element_from_pdb_line(line)
        if element is None:
            continue
        try:
            x, y, z = float(line[30:38]), float(line[38:46]), float(line[46:54])
        except (ValueError, IndexError):
            continue
        key = (res_name, line[21:22].strip(), line[22:26].strip())
        residues.setdefault(key, []).append((element, x, y, z))
    return residues


def pick_primary_ligand(pdb_text: str) -> Optional[tuple[str, list[Atom]]]:
    """Return the largest plausible ligand residue as (residue name, atoms)."""
    residues = extract_hetatm_residues(pdb_text)
    if not residues:
        return None
    key, atoms = max(residues.items(), key=lambda item: len(item[1]))
    if len(atoms) < MIN_HEAVY_ATOMS:
        return None
    return key[0], atoms


def centroid(atoms: list[Atom]) -> tuple[float, float, float]:
    n = len(atoms)
    return (
        round(sum(a[1] for a in atoms) / n, 3),
        round(sum(a[2] for a in atoms) / n, 3),
        round(sum(a[3] for a in atoms) / n, 3),
    )


def crystal_ligand_mol(pdb_text: str):
    """Rebuild the primary ligand as an RDKit molecule, or None."""
    picked = pick_primary_ligand(pdb_text)
    if picked is None:
        return None
    return build_mol_from_atoms(picked[1])
