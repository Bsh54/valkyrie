"""Input validation boundary.

Guarantees the caller only ever sees ValidationError, never a library
exception leaking from RDKit or the network.
"""

from drugforge.chem.resolver import resolve
from drugforge.errors import ResolutionError, ValidationError


def validate_molecule(molecule_input: object) -> str:
    """Return canonical SMILES for a user input, or raise ValidationError."""
    if not isinstance(molecule_input, str):
        raise ValidationError("Molecule input must be a string.")

    try:
        return resolve(molecule_input)
    except ResolutionError as exc:
        raise ValidationError(exc.detail) from exc
    except Exception as exc:
        raise ValidationError(
            f"Unexpected error validating input: {type(exc).__name__}: {exc}"
        ) from exc
