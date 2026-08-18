"""Target registry.

Adding a disease means adding one Target entry. Python validates the shape at
import time, so no schema parser is needed.
"""

from valkyrie.domain.models import DockingBox, ReferenceDrug, Target
from valkyrie.errors import TargetNotFoundError

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
    "tc-cyp51": Target(
        id="tc-cyp51",
        name="TcCYP51",
        disease="chagas disease",
        pdb_id="3K1O",
        box=DockingBox(
            center_x=-43.5,
            center_y=7.8,
            center_z=-13.0,
            size_x=22.5,
            size_y=22.5,
            size_z=22.5,
        ),
        reference=ReferenceDrug(
            name="fluconazole",
            smiles="C1=CC(=C(C=C1F)F)C(CN2C=NC=N2)(CN3C=NC=N3)O",
        ),
    ),
    "lm-ptr1": Target(
        id="lm-ptr1",
        name="LmPTR1",
        disease="leishmaniasis",
        pdb_id="1E7W",
        box=DockingBox(
            center_x=8.2,
            center_y=13.2,
            center_z=20.9,
            size_x=22.5,
            size_y=22.5,
            size_z=22.5,
        ),
        reference=ReferenceDrug(
            name="methotrexate",
            smiles="CN(CC1=CN=C2C(=N1)C(=NC(=N2)N)N)C3=CC=C(C=C3)C(=O)NC(CCC(=O)O)C(=O)O",
        ),
    ),
    "tb-ptr1": Target(
        id="tb-ptr1",
        name="TbPTR1",
        disease="sleeping sickness",
        pdb_id="2WD8",
        box=DockingBox(
            center_x=-8.1,
            center_y=3.1,
            center_z=17.6,
            size_x=22.5,
            size_y=22.5,
            size_z=22.5,
        ),
        reference=ReferenceDrug(
            name="methotrexate",
            smiles="CN(CC1=CN=C2C(=N1)C(=NC(=N2)N)N)C3=CC=C(C=C3)C(=O)NC(CCC(=O)O)C(=O)O",
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
