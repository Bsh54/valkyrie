"""Exception hierarchy.

Every failure mode is typed so the web layer can map it to a status code
without inspecting messages.
"""


class ValkyrieError(Exception):
    """Base class for all Valkyrie failures."""

    def __init__(self, detail: str = ""):
        self.detail = detail
        super().__init__(detail)


class ValidationError(ValkyrieError):
    """Input could not be accepted."""


class ResolutionError(ValkyrieError):
    """A name or SMILES could not be resolved to a structure."""


class LigandPrepError(ValkyrieError):
    """3D embedding or PDBQT conversion failed."""


class ReceptorError(ValkyrieError):
    """Structure download or receptor preparation failed."""


class DockingError(ValkyrieError):
    """The docking engine failed."""


class TargetNotFoundError(ValkyrieError):
    """No such target in the registry."""


class StorageError(ValkyrieError):
    """Persistence failed."""


class PipelineError(ValkyrieError):
    """Wraps a stage failure with the stage that produced it."""

    def __init__(self, stage: str, cause: ValkyrieError):
        self.stage = stage
        self.cause = cause
        super().__init__(f"Pipeline failed at stage '{stage}': {cause.detail}")
