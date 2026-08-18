"""Domain models and the target registry."""

import dataclasses

import pytest

from valkyrie.domain.models import IN_SILICO_DISCLAIMER, DockingBox, Target
from valkyrie.domain.targets import TARGETS, get_target, list_targets
from valkyrie.errors import TargetNotFoundError


def test_registry_is_not_empty():
    assert list_targets()


def test_known_target_is_complete():
    target = get_target("pf-dhfr")
    assert isinstance(target, Target)
    assert target.disease == "malaria"
    assert target.pdb_id == "1J3I"
    assert target.reference.name == "pyrimethamine"
    assert target.reference.smiles


def test_unknown_target_names_the_alternatives():
    with pytest.raises(TargetNotFoundError) as exc_info:
        get_target("does-not-exist")
    assert "does-not-exist" in exc_info.value.detail
    assert "pf-dhfr" in exc_info.value.detail


def test_targets_are_immutable():
    target = get_target("pf-dhfr")
    with pytest.raises(dataclasses.FrozenInstanceError):
        target.id = "mutated"


def test_docking_box_exposes_vina_vectors():
    box = DockingBox(1.0, 2.0, 3.0, 20.0, 21.0, 22.0)
    assert box.center == [1.0, 2.0, 3.0]
    assert box.size == [20.0, 21.0, 22.0]


def test_every_registered_target_has_a_positive_box():
    for target in TARGETS.values():
        assert min(target.box.size) > 0


def test_result_serialisation_carries_the_disclaimer(screening_result):
    assert screening_result.to_dict()["disclaimer"] == IN_SILICO_DISCLAIMER
