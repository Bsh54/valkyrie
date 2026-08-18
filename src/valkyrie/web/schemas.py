"""Request and response models for the HTTP layer."""

from pydantic import BaseModel, Field

from valkyrie.config import (
    DEFAULT_EXHAUSTIVENESS,
    MAX_EXHAUSTIVENESS,
    MIN_EXHAUSTIVENESS,
)


class ScreeningRequest(BaseModel):
    molecule: str = Field(
        ..., min_length=1, max_length=500,
        description="Compound name or SMILES string",
    )
    target_id: str = Field(..., description="Target identifier, for example pf-dhfr")
    exhaustiveness: int = Field(
        default=DEFAULT_EXHAUSTIVENESS,
        ge=MIN_EXHAUSTIVENESS,
        le=MAX_EXHAUSTIVENESS,
        description="Vina search effort; lower is faster and less thorough",
    )


class ErrorResponse(BaseModel):
    error: str
    detail: str
    stage: str | None = None
