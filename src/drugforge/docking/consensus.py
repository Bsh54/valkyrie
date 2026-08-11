"""Consensus scoring across two energy models.

Each score is expressed as a ratio against the target's reference drug, so a
consensus of 1.0 means "as good as the reference". Because binding energies are
negative, a ratio above 1.0 indicates stronger predicted binding.
"""

from drugforge.domain.models import ConsensusResult

VINA_WEIGHT = 0.6
VINARDO_WEIGHT = 0.4


def _ratio(value: float, reference: float) -> float:
    return value / reference if reference else 1.0


def compute_consensus(
    vina_score: float,
    vinardo_score: float,
    reference_vina: float,
    reference_vinardo: float,
    vina_weight: float = VINA_WEIGHT,
    vinardo_weight: float = VINARDO_WEIGHT,
) -> ConsensusResult:
    """Combine two scores into one weighted, reference-normalised score."""
    consensus = (
        vina_weight * _ratio(vina_score, reference_vina)
        + vinardo_weight * _ratio(vinardo_score, reference_vinardo)
    )
    return ConsensusResult(
        vina_score=vina_score,
        vinardo_score=vinardo_score,
        consensus_score=round(consensus, 4),
    )
