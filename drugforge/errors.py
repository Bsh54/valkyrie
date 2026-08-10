"""Custom exception hierarchy for DrugForge."""


class DrugForgeError(Exception):
    """Base for all DrugForge errors."""

    def __init__(self, detail: str = ""):
        self.detail = detail
        super().__init__(detail)


class ValidationError(DrugForgeError):
    """Invalid molecule input."""
    pass


class ResolutionError(DrugForgeError):
    """Could not resolve name to SMILES."""
    pass


class LigandPrepError(DrugForgeError):
    """3D embedding or PDBQT conversion failed."""
    pass


class ReceptorError(DrugForgeError):
    """PDB download or receptor preparation failed."""
    pass


class DockingError(DrugForgeError):
    """Vina execution failed."""
    pass


class TargetNotFoundError(DrugForgeError):
    """Unknown target_id."""
    pass


class PipelineError(DrugForgeError):
    """Wraps stage errors with pipeline context."""

    def __init__(self, stage: str, cause: DrugForgeError):
        self.stage = stage
        self.cause = cause
        detail = f"Pipeline failed at stage '{stage}': {cause.detail}"
        super().__init__(detail)
