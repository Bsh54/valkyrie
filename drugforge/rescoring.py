"""Vinardo rescoring — rescore a docked pose with the Vinardo scoring function."""

import logging
import tempfile
from pathlib import Path

from drugforge.errors import DockingError
from drugforge.targets import DockingBox

logger = logging.getLogger(__name__)


def rescore_vinardo(
    ligand_pdbqt: str,
    receptor_pdbqt_path: Path,
    box: DockingBox,
) -> float:
    """
    Rescore a docked ligand pose using the Vinardo scoring function.

    This provides a second, independent score on the same pose without
    re-docking. Vinardo uses a different energy model than Vina's default.

    Args:
        ligand_pdbqt: PDBQT string of the docked pose (may contain multi-MODEL).
        receptor_pdbqt_path: Path to receptor PDBQT file.
        box: Docking box (needed for Vina map computation).

    Returns:
        Vinardo score in kcal/mol (negative = better binding).

    Raises:
        DockingError on failure.
    """
    try:
        from vina import Vina
    except ImportError:
        raise DockingError("Vina Python bindings not installed.")

    try:
        # Extract first MODEL only (Vina output may contain multiple models)
        first_model_lines = []
        in_model = False
        for line in ligand_pdbqt.splitlines():
            if line.startswith("MODEL"):
                if in_model:
                    break  # stop at second MODEL
                in_model = True
                continue
            if line.startswith("ENDMDL"):
                break
            first_model_lines.append(line)

        # If no MODEL tags, use the whole string
        if not first_model_lines:
            single_pose = ligand_pdbqt
        else:
            single_pose = "\n".join(first_model_lines) + "\n"

        v = Vina(sf_name="vinardo", verbosity=0)
        v.set_receptor(str(receptor_pdbqt_path))

        # Write ligand to temp file
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".pdbqt", delete=False
        ) as f:
            f.write(single_pose)
            ligand_path = f.name

        v.set_ligand_from_file(ligand_path)

        # Compute maps for scoring
        v.compute_vina_maps(
            center=[box.center_x, box.center_y, box.center_z],
            box_size=[box.size_x, box.size_y, box.size_z],
        )

        # Score the pose (no docking, just scoring)
        energy = v.score()

        # Cleanup
        try:
            Path(ligand_path).unlink(missing_ok=True)
        except OSError:
            pass

        # energy is a list: [total, inter, intra, ...]
        vinardo_score = float(energy[0])
        return vinardo_score

    except DockingError:
        raise
    except Exception as e:
        raise DockingError(f"Vinardo rescoring failed: {type(e).__name__}: {e}")
