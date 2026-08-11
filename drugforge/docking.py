"""Docking engine — AutoDock Vina wrapper."""

import logging
import tempfile
from dataclasses import dataclass
from pathlib import Path

from rdkit import Chem

from drugforge.config import VINA_CPU
from drugforge.errors import DockingError
from drugforge.molblock import apply_template, build_mol_from_atoms, to_mol_block
from drugforge.targets import DockingBox

logger = logging.getLogger(__name__)


@dataclass
class DockingResult:
    """Results from a Vina docking run."""
    best_affinity: float        # kcal/mol (negative = better)
    all_affinities: list[float]
    best_pose_pdbqt: str        # native Vina output for traceability
    best_pose_sdf: str          # converted for 3Dmol.js display


_AUTODOCK_TO_ELEMENT = {
    "A": "C", "C": "C", "CG0": "C", "G0": "C",
    "N": "N", "NA": "N", "NS": "N",
    "O": "O", "OA": "O", "OS": "O",
    "S": "S", "SA": "S",
    "H": "H", "HD": "H", "HS": "H",
    "F": "F", "CL": "Cl", "BR": "Br", "I": "I",
    "P": "P", "SI": "Si", "B": "B",
    "FE": "Fe", "ZN": "Zn", "MG": "Mg", "MN": "Mn", "CA": "Ca",
    "CU": "Cu", "NI": "Ni", "CO": "Co", "K": "K", "NB": "Nb",
}


def _element_from_pdbqt_line(line: str) -> str:
    """Resolve a real element symbol from a PDBQT AutoDock atom type."""
    ad_type = line[77:79].strip().upper() if len(line) >= 79 else ""
    if ad_type in _AUTODOCK_TO_ELEMENT:
        return _AUTODOCK_TO_ELEMENT[ad_type]

    name = line[12:16].strip().upper()
    for candidate in (name[:2], name[:1]):
        if candidate in _AUTODOCK_TO_ELEMENT:
            return _AUTODOCK_TO_ELEMENT[candidate]
    return "C"


def _parse_first_model(pdbqt_string: str) -> list[tuple[str, float, float, float]]:
    """Extract (element, x, y, z) for the first MODEL of a PDBQT block."""
    atoms = []
    for line in pdbqt_string.splitlines():
        if line.startswith("ENDMDL"):
            break
        if not (line.startswith("ATOM") or line.startswith("HETATM")):
            continue
        try:
            x, y, z = float(line[30:38]), float(line[38:46]), float(line[46:54])
        except (ValueError, IndexError):
            continue
        atoms.append((_element_from_pdbqt_line(line), x, y, z))
    return atoms


def _pdbqt_to_sdf(pdbqt_string: str, template_smiles: str | None = None) -> str:
    """
    Convert a docked PDBQT pose into an SDF mol block for 3D display.

    PDBQT stores AutoDock atom types (A, OA, NA, SA, HD) rather than element
    symbols, so types are mapped to elements before parsing. Bonds are absent
    from PDBQT and are inferred by proximity; when a template SMILES is given
    and the heavy-atom count matches, bond orders are recovered from it.
    """
    atoms = _parse_first_model(pdbqt_string)
    if not atoms:
        return ""

    mol = build_mol_from_atoms(atoms)
    if mol is None:
        logger.warning("Could not build a molecule from the docked pose.")
        return ""

    if template_smiles:
        mol = apply_template(mol, template_smiles)

    return to_mol_block(mol)


def dock(
    ligand_pdbqt: str,
    receptor_pdbqt_path: Path,
    box: DockingBox,
    exhaustiveness: int = 8,
    n_poses: int = 5,
    template_smiles: str | None = None,
) -> DockingResult:
    """
    Dock a ligand against a receptor using AutoDock Vina.

    Args:
        ligand_pdbqt: PDBQT string of the prepared ligand.
        receptor_pdbqt_path: Path to the receptor PDBQT file.
        box: Docking box (center + size).
        exhaustiveness: Vina search exhaustiveness (default 8).
        n_poses: Number of poses to generate.
        template_smiles: Optional SMILES used to recover pose bond orders.

    Returns:
        DockingResult with affinity scores and poses.

    Raises:
        DockingError on Vina failure.
    """
    try:
        from vina import Vina
    except ImportError:
        raise DockingError(
            "AutoDock Vina Python bindings not installed. "
            "Install with: pip install vina"
        )

    try:
        v = Vina(sf_name="vina", cpu=VINA_CPU, verbosity=0)

        # Set receptor
        v.set_receptor(str(receptor_pdbqt_path))

        # Write ligand to temp file (Vina API needs file path)
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".pdbqt", delete=False
        ) as f:
            f.write(ligand_pdbqt)
            ligand_path = f.name

        v.set_ligand_from_file(ligand_path)

        # Set docking box
        v.compute_vina_maps(
            center=[box.center_x, box.center_y, box.center_z],
            box_size=[box.size_x, box.size_y, box.size_z],
        )

        # Run docking
        v.dock(exhaustiveness=exhaustiveness, n_poses=n_poses)

        # Get results
        energies = v.energies()
        if energies is None or len(energies) == 0:
            raise DockingError("Vina returned no poses.")

        all_affinities = [float(e[0]) for e in energies]
        best_affinity = all_affinities[0]

        # Get best pose as PDBQT
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".pdbqt", delete=False
        ) as f:
            output_path = f.name

        v.write_poses(output_path, n_poses=1, overwrite=True)
        best_pose_pdbqt = Path(output_path).read_text(encoding="utf-8")

        # Convert to SDF for 3Dmol.js
        best_pose_sdf = _pdbqt_to_sdf(best_pose_pdbqt, template_smiles)

        # Cleanup temp files
        try:
            Path(ligand_path).unlink(missing_ok=True)
            Path(output_path).unlink(missing_ok=True)
        except OSError:
            pass

        return DockingResult(
            best_affinity=best_affinity,
            all_affinities=all_affinities,
            best_pose_pdbqt=best_pose_pdbqt,
            best_pose_sdf=best_pose_sdf,
        )

    except DockingError:
        raise
    except Exception as e:
        raise DockingError(
            f"Vina docking failed: {type(e).__name__}: {e}"
        )
