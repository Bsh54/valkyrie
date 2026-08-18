"""Independent rescoring of an existing pose with the Vinardo function.

Rescoring is not redocking: the pose is fixed and only the energy model changes,
which is what makes the two scores worth combining.
"""

from __future__ import annotations

import logging
from pathlib import Path

from valkyrie.config import VINA_CPU
from valkyrie.docking.engine import _temporary_pdbqt, first_model_only
from valkyrie.domain.models import DockingBox
from valkyrie.errors import DockingError

logger = logging.getLogger(__name__)


def rescore_vinardo(
    pose_pdbqt: str, receptor_pdbqt_path: Path, box: DockingBox
) -> float:
    """Score a single docked pose with Vinardo, in kcal/mol."""
    try:
        from vina import Vina
    except ImportError as exc:
        raise DockingError("AutoDock Vina bindings are not installed.") from exc

    try:
        engine = Vina(sf_name="vinardo", cpu=VINA_CPU, verbosity=0)
        engine.set_receptor(str(receptor_pdbqt_path))

        with _temporary_pdbqt(first_model_only(pose_pdbqt)) as ligand_path:
            engine.set_ligand_from_file(str(ligand_path))
            engine.compute_vina_maps(center=box.center, box_size=box.size)
            energy = engine.score()

        return float(energy[0])
    except DockingError:
        raise
    except Exception as exc:
        raise DockingError(
            f"Vinardo rescoring failed: {type(exc).__name__}: {exc}"
        ) from exc
