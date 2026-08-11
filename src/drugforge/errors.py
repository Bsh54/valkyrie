"""Exception hierarchy.

Every failure mode is typed so the web layer can map it to a status code
without inspecting messages.
"""


class DrugForgeError(Exception):
    """Base class for all DrugForge failures."""

    def __init__(self, detail: str = ""):
        self.detail = detail
        super().__init__(detail)


class ValidationError(DrugForgeError):
    """Input could not be accepted."""


class ResolutionError(DrugForgeError):
    """A name or SMILES could not be resolved to a structure."""


class LigandPrepError(DrugForgeError):
    """3D embedding or PDBQT conversion failed."""


class ReceptorError(DrugForgeError):
    """Structure download or receptor preparation failed."""


class DockingError(DrugForgeError):
    """The docking engine failed."""


class TargetNotFoundError(DrugForgeError):
    """No such target in the registry."""


class StorageError(DrugForgeError):
    """Persistence failed."""


class PipelineError(DrugForgeError):
    """Wraps a stage failure with the stage that produced it."""

    def __init__(self, stage: str, cause: DrugForgeError):
        self.stage = stage
        self.cause = cause
        super().__init__(f"Pipeline failed at stage '{stage}': {cause.detail}")
