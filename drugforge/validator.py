"""Input validation — wraps resolver to ensure clean error handling."""

from drugforge.errors import ValidationError, ResolutionError
from drugforge.resolver import resolve


def validate_molecule(molecule_input: str) -> str:
    """
    Validate and resolve molecule input to canonical SMILES.

    Returns canonical SMILES on success.
    Raises ValidationError with a clear detail message on failure.
    Never raises unhandled exceptions.
    """
    try:
        if molecule_input is None:
            raise ValidationError("Molecule input cannot be None.")
        return resolve(molecule_input)
    except ResolutionError as e:
        raise ValidationError(e.detail)
    except ValidationError:
        raise
    except Exception as e:
        # Catch-all: no unhandled exceptions should reach the caller
        raise ValidationError(
            f"Unexpected error validating input: {type(e).__name__}: {e}"
        )
