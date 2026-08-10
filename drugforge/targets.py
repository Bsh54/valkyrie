"""Target registry — each disease target is a frozen dataclass entry."""

from dataclasses import dataclass

from drugforge.errors import TargetNotFoundError


@dataclass(frozen=True)
class DockingBox:
    """Docking search space defined by center and size in Angstroms."""
    center_x: float
    center_y: float
    center_z: float
    size_x: float
    size_y: float
    size_z: float


@dataclass(frozen=True)
class ReferenceDrug:
    """Known active compound used as positive control."""
    name: str
    smiles: str


@dataclass(frozen=True)
class Target:
    """A validated disease protein target for molecular docking."""
    id: str
    name: str
    disease: str
    pdb_id: str
    box: DockingBox
    reference: ReferenceDrug


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

TARGETS: dict[str, Target] = {
    "pf-dhfr": Target(
        id="pf-dhfr",
        name="PfDHFR",
        disease="malaria",
        pdb_id="1J3I",
        # Docking box derived from co-crystallized pyrimethamine in PDB 1J3I
        # Center: approximate centroid of pyrimethamine in chain A
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
    """Retrieve a target by ID. Raises TargetNotFoundError if unknown."""
    if target_id not in TARGETS:
        raise TargetNotFoundError(
            f"Unknown target '{target_id}'. Available: {list(TARGETS.keys())}"
        )
    return TARGETS[target_id]
