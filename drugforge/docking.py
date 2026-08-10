"""Docking engine — AutoDock Vina wrapper."""

import logging
import tempfile
from dataclasses import dataclass
from pathlib import Path

from rdkit import Chem
from rdkit.Chem import AllChem

from drugforge.errors import DockingError
from drugforge.targets import DockingBox

logger = logging.getLogger(__name__)


@dataclass
class DockingResult:
    """Results from a Vina docking run."""
    best_affinity: float        # kcal/mol (negative = better)
    all_affinities: list[float]
    best_pose_pdbqt: str        # native Vina output for traceability
    best_pose_sdf: str          # converted for 3Dmol.js display


def _pdbqt_to_sdf(pdbqt_string: str, template_smiles: str | None = None) -> str:
    """
    Convert a PDBQT pose to SDF format.

    Uses coordinate extraction and RDKit for format conversion.
    """
    # Extract coordinates from PDBQT ATOM/HETATM lines
    atoms = []
    coords = []
    for line in pdbqt_string.splitlines():
        if line.startswith("ATOM") or line.startswith("HETATM"):
            try:
                x = float(line[30:38])
                y = float(line[38:46])
                z = float(line[46:54])
                atom_name = line[12:16].strip()
                # Get element from atom type column or atom name
                element = line[77:79].strip() if len(line) >= 79 else ""
                if not element:
                    element = atom_name[0] if atom_name else "C"
                atoms.append(element)
                coords.append((x, y, z))
            except (ValueError, IndexError):
                continue

    if not atoms:
        return ""

    # Build a simple PDB block and convert via RDKit
    pdb_lines = []
    for i, (element, (x, y, z)) in enumerate(zip(atoms, coords), 1):
        pdb_lines.append(
            f"HETATM{i:5d} {element:<4s} LIG A   1    "
            f"{x:8.3f}{y:8.3f}{z:8.3f}  1.00  0.00          {element:>2s}"
        )
    pdb_lines.append("END")
    pdb_block = "\n".join(pdb_lines)

    mol = Chem.MolFromPDBBlock(pdb_block, sanitize=False, removeHs=False)
    if mol is None:
        # Fallback: return raw coordinates as a minimal SDF-like block
        return pdb_block

    try:
        sdf_string = Chem.MolToMolBlock(mol)
        return sdf_string
    except Exception:
        return pdb_block


def dock(
    ligand_pdbqt: str,
    receptor_pdbqt_path: Path,
    box: DockingBox,
    exhaustiveness: int = 8,
    n_poses: int = 5,
) -> DockingResult:
    """
    Dock a ligand against a receptor using AutoDock Vina.

    Args:
        ligand_pdbqt: PDBQT string of the prepared ligand.
        receptor_pdbqt_path: Path to the receptor PDBQT file.
        box: Docking box (center + size).
        exhaustiveness: Vina search exhaustiveness (default 8).
        n_poses: Number of poses to generate.

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
        v = Vina(sf_name="vina", verbosity=0)

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
        best_pose_sdf = _pdbqt_to_sdf(best_pose_pdbqt)

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
