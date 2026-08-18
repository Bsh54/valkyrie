"""AutoDock Vina execution and pose conversion."""

from __future__ import annotations

import logging
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from valkyrie.chem.molblock import Atom, apply_template, build_mol_from_atoms, to_mol_block
from valkyrie.config import N_POSES, VINA_CPU
from valkyrie.domain.models import DockingBox, DockingResult
from valkyrie.errors import DockingError

logger = logging.getLogger(__name__)

# PDBQT columns 78-79 hold AutoDock types, which are not element symbols.
_AUTODOCK_ELEMENTS = {
    "A": "C", "C": "C", "CG0": "C", "G0": "C",
    "N": "N", "NA": "N", "NS": "N",
    "O": "O", "OA": "O", "OS": "O",
    "S": "S", "SA": "S",
    "H": "H", "HD": "H", "HS": "H",
    "F": "F", "CL": "Cl", "BR": "Br", "I": "I",
    "P": "P", "SI": "Si", "B": "B",
    "FE": "Fe", "ZN": "Zn", "MG": "Mg", "MN": "Mn", "CA": "Ca",
    "CU": "Cu", "NI": "Ni", "CO": "Co", "K": "K",
}


@contextmanager
def _temporary_pdbqt(content: str = "") -> Iterator[Path]:
    """Provide a PDBQT path for Vina, which only accepts files, then clean up."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".pdbqt", delete=False
    ) as handle:
        handle.write(content)
        path = Path(handle.name)
    try:
        yield path
    finally:
        path.unlink(missing_ok=True)


def _element_for(line: str) -> str:
    autodock_type = line[77:79].strip().upper() if len(line) >= 79 else ""
    if autodock_type in _AUTODOCK_ELEMENTS:
        return _AUTODOCK_ELEMENTS[autodock_type]

    name = line[12:16].strip().upper()
    for candidate in (name[:2], name[:1]):
        if candidate in _AUTODOCK_ELEMENTS:
            return _AUTODOCK_ELEMENTS[candidate]
    return "C"


def parse_first_model(pdbqt: str) -> list[Atom]:
    """Read elements and coordinates from the first MODEL of a PDBQT block."""
    atoms: list[Atom] = []
    for line in pdbqt.splitlines():
        if line.startswith("ENDMDL"):
            break
        if not line.startswith(("ATOM", "HETATM")):
            continue
        try:
            x, y, z = float(line[30:38]), float(line[38:46]), float(line[46:54])
        except (ValueError, IndexError):
            continue
        atoms.append((_element_for(line), x, y, z))
    return atoms


def first_model_only(pdbqt: str) -> str:
    """Strip trailing models so scoring tools receive a single pose."""
    lines: list[str] = []
    inside = False
    for line in pdbqt.splitlines():
        if line.startswith("MODEL"):
            if inside:
                break
            inside = True
            continue
        if line.startswith("ENDMDL"):
            break
        lines.append(line)
    return "\n".join(lines) + "\n" if lines else pdbqt


def pose_to_mol_block(pdbqt: str, template_smiles: str | None = None) -> str:
    """Convert a docked pose into an SDF mol block for 3D display."""
    atoms = parse_first_model(pdbqt)
    if not atoms:
        return ""

    mol = build_mol_from_atoms(atoms)
    if mol is None:
        logger.warning("Could not rebuild a molecule from the docked pose.")
        return ""

    if template_smiles:
        mol = apply_template(mol, template_smiles)
    return to_mol_block(mol)


def dock(
    ligand_pdbqt: str,
    receptor_pdbqt_path: Path,
    box: DockingBox,
    exhaustiveness: int,
    n_poses: int = N_POSES,
    template_smiles: str | None = None,
) -> DockingResult:
    """Dock a prepared ligand into a prepared receptor."""
    try:
        from vina import Vina
    except ImportError as exc:
        raise DockingError(
            "AutoDock Vina bindings are not installed. Install with: pip install vina"
        ) from exc

    try:
        engine = Vina(sf_name="vina", cpu=VINA_CPU, verbosity=0)
        engine.set_receptor(str(receptor_pdbqt_path))

        with _temporary_pdbqt(ligand_pdbqt) as ligand_path:
            engine.set_ligand_from_file(str(ligand_path))
            engine.compute_vina_maps(center=box.center, box_size=box.size)
            engine.dock(exhaustiveness=exhaustiveness, n_poses=n_poses)

            energies = engine.energies()
            if energies is None or len(energies) == 0:
                raise DockingError("Vina returned no poses.")

            with _temporary_pdbqt() as output_path:
                engine.write_poses(str(output_path), n_poses=1, overwrite=True)
                best_pose = output_path.read_text(encoding="utf-8")

        affinities = [float(row[0]) for row in energies]
        return DockingResult(
            best_affinity=affinities[0],
            all_affinities=affinities,
            best_pose_pdbqt=best_pose,
            best_pose_sdf=pose_to_mol_block(best_pose, template_smiles),
        )
    except DockingError:
        raise
    except Exception as exc:
        raise DockingError(f"Vina docking failed: {type(exc).__name__}: {exc}") from exc
