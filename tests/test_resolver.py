"""Tests for the molecule resolver."""

import pytest
from unittest.mock import patch, MagicMock

from drugforge.resolver import resolve
from drugforge.errors import ResolutionError


def test_resolve_local_lookup():
    """Known compound name resolves via local lookup."""
    smiles = resolve("pyrimethamine")
    assert smiles  # non-empty canonical SMILES
    assert isinstance(smiles, str)


def test_resolve_local_lookup_case_insensitive():
    """Local lookup is case-insensitive."""
    s1 = resolve("Artemisinin")
    s2 = resolve("artemisinin")
    assert s1 == s2


def test_resolve_direct_smiles():
    """Valid SMILES passes through directly."""
    smiles = resolve("CCO")  # ethanol
    assert smiles == "CCO"


def test_resolve_invalid_raises():
    """Invalid input that can't be resolved raises ResolutionError."""
    with pytest.raises(ResolutionError):
        resolve("not_a_real_molecule_xyz_12345!!!")


def test_resolve_empty_raises():
    """Empty string raises ResolutionError."""
    with pytest.raises(ResolutionError):
        resolve("")


def test_resolve_whitespace_only_raises():
    """Whitespace-only input raises ResolutionError."""
    with pytest.raises(ResolutionError):
        resolve("   ")


@patch("drugforge.resolver._lookup_pubchem")
def test_resolve_pubchem_fallback(mock_pubchem):
    """If local lookup and SMILES parse fail, PubChem is queried."""
    mock_pubchem.return_value = "CCO"
    result = resolve("some_unknown_compound_for_test")
    mock_pubchem.assert_called_once()
    assert result == "CCO"
