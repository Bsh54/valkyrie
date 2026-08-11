"""Target registry.

Adding a disease means adding one Target entry. Python validates the shape at
import time, so no schema parser is needed.
"""

from drugforge.domain.models import DockingBox, ReferenceDrug, Target
from drugforge.errors import TargetNotFoundError

TARGETS: dict[str, Target] = {
    "pf-dhfr": Target(
        id="pf-dhfr",
        name="PfDHFR",
        disease="malaria",
        pdb_id="1J3I",
        box=DockingBox(
            center_x=18.0,
            center_y=15.0,
            center_z=25.0,
            size_x=20.0,
            size_y=20.0,
            size_z=20.0,
        ),
        reference=ReferenceDrug(
            name="pyrimethamine",
            smiles="c1ccc(c(c1)Cl)c2cnc(nc2N)N",
        ),
    ),
}


def get_target(target_id: str) -> Target:
    """Look up a target, raising TargetNotFoundError when unknown."""
    try:
        return TARGETS[target_id]
    except KeyError:
        raise TargetNotFoundError(
            f"Unknown target '{target_id}'. Available: {sorted(TARGETS)}"
        ) from None


def list_targets() -> list[Target]:
    return list(TARGETS.values())
