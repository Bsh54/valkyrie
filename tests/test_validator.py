"""Tests for the input validator."""

import pytest

from drugforge.validator import validate_molecule
from drugforge.errors import ValidationError


def test_validate_valid_smiles():
    """Valid SMILES returns canonical SMILES."""
    result = validate_molecule("CCO")
    assert result == "CCO"


def test_validate_known_name():
    """Known compound name resolves successfully."""
    result = validate_molecule("pyrimethamine")
    assert isinstance(result, str)
    assert len(result) > 0


def test_validate_invalid_smiles():
    """Invalid SMILES raises ValidationError."""
    with pytest.raises(ValidationError) as exc_info:
        validate_molecule("not_a_molecule!!!")
    assert exc_info.value.detail


def test_validate_empty_string():
    """Empty string raises ValidationError."""
    with pytest.raises(ValidationError):
        validate_molecule("")


def test_validate_none():
    """None input raises ValidationError."""
    with pytest.raises(ValidationError):
        validate_molecule(None)  # type: ignore


def test_validate_special_characters():
    """Special characters that aren't valid SMILES raise ValidationError."""
    with pytest.raises(ValidationError):
        validate_molecule("@#$%^&*()")


def test_validate_never_crashes():
    """Validator should never raise anything other than ValidationError."""
    bad_inputs = [
        "", " ", "\n", "\t", "!!!",
        "a" * 1000,
        "C" * 500 + "INVALID",
        "\x00\x01\x02",
    ]
    for inp in bad_inputs:
        try:
            validate_molecule(inp)
        except ValidationError:
            pass  # Expected
        # Any other exception is a test failure
