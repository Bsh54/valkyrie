"""Tests for the target registry."""

import pytest

from drugforge.targets import get_target, TARGETS, Target, DockingBox, ReferenceDrug
from drugforge.errors import TargetNotFoundError


def test_get_target_valid():
    """Known target ID returns a Target instance."""
    target = get_target("pf-dhfr")
    assert isinstance(target, Target)
    assert target.id == "pf-dhfr"
    assert target.disease == "malaria"
    assert target.pdb_id == "1J3I"


def test_get_target_has_docking_box():
    """Target has a properly defined docking box."""
    target = get_target("pf-dhfr")
    assert isinstance(target.box, DockingBox)
    assert target.box.size_x > 0
    assert target.box.size_y > 0
    assert target.box.size_z > 0


def test_get_target_has_reference_drug():
    """Target has a reference drug with name and SMILES."""
    target = get_target("pf-dhfr")
    assert isinstance(target.reference, ReferenceDrug)
    assert target.reference.name == "pyrimethamine"
    assert len(target.reference.smiles) > 0


def test_get_target_unknown_raises():
    """Unknown target ID raises TargetNotFoundError."""
    with pytest.raises(TargetNotFoundError) as exc_info:
        get_target("nonexistent-target")
    assert "nonexistent-target" in exc_info.value.detail


def test_targets_registry_not_empty():
    """Registry has at least one target."""
    assert len(TARGETS) >= 1


def test_target_is_frozen():
    """Target dataclass is immutable."""
    target = get_target("pf-dhfr")
    with pytest.raises(Exception):
        target.id = "modified"  # type: ignore
