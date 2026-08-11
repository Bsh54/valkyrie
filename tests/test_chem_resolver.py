"""Molecule resolution and input validation."""

from unittest.mock import patch

import pytest

from drugforge.chem.resolver import canonicalize, resolve
from drugforge.chem.validator import validate_molecule
from drugforge.errors import ResolutionError, ValidationError


def test_curated_name_resolves():
    assert resolve("pyrimethamine")


def test_name_lookup_ignores_case_and_whitespace():
    assert resolve("  Artemisinin  ") == resolve("artemisinin")


def test_library_compound_name_resolves():
    """Names from the plant registry must resolve, not only compounds.json."""
    assert resolve("cryptolepine")


def test_smiles_passes_through_canonicalised():
    assert resolve("CCO") == "CCO"


def test_blank_input_is_rejected():
    for value in ("", "   ", "\n"):
        with pytest.raises(ResolutionError):
            resolve(value)


@patch("drugforge.chem.resolver._lookup_pubchem", return_value=None)
def test_unresolvable_input_raises(mock_lookup):
    with pytest.raises(ResolutionError):
        resolve("definitely_not_a_molecule_zzz")
    mock_lookup.assert_called_once()


@patch("drugforge.chem.resolver._lookup_pubchem", return_value="CCO")
def test_pubchem_is_the_last_resort(mock_lookup):
    assert resolve("some unknown trade name") == "CCO"
    mock_lookup.assert_called_once()


def test_canonicalize_rejects_non_structures():
    assert canonicalize("not a molecule") is None
    assert canonicalize("") is None


def test_validator_wraps_resolution_failures():
    with pytest.raises(ValidationError):
        validate_molecule("@#$%^&*()")


def test_validator_rejects_non_strings():
    with pytest.raises(ValidationError):
        validate_molecule(None)


@pytest.mark.parametrize(
    "value",
    ["", " ", "\t", "!!!", "a" * 600, "C" * 200 + "INVALID", "\x00\x01"],
)
def test_validator_never_leaks_other_exceptions(value):
    with patch("drugforge.chem.resolver._lookup_pubchem", return_value=None):
        try:
            validate_molecule(value)
        except ValidationError:
            pass
