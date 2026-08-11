"""Consensus scoring — combine Vina and Vinardo into a single ranked score."""

from dataclasses import dataclass, asdict


@dataclass
class ConsensusResult:
    """Combined consensus score from multiple scoring functions."""
    vina_score: float
    vinardo_score: float
    consensus_score: float  # normalized combination; lower = better

    def to_dict(self) -> dict:
        return asdict(self)


def compute_consensus(
    vina_score: float,
    vinardo_score: float,
    ref_vina: float,
    ref_vinardo: float,
    w1: float = 0.6,
    w2: float = 0.4,
) -> ConsensusResult:
    """
    Compute a consensus score from Vina and Vinardo scores.

    The consensus is a weighted combination of normalized scores, where
    normalization is relative to the reference drug (ratio). Lower = better.

    Formula:
        normalized_vina = vina_score / ref_vina
        normalized_vinardo = vinardo_score / ref_vinardo
        consensus = w1 * normalized_vina + w2 * normalized_vinardo

    A consensus of 1.0 means equal to reference; < 1.0 means better.

    Args:
        vina_score: Vina affinity (kcal/mol, negative)
        vinardo_score: Vinardo affinity (kcal/mol, negative)
        ref_vina: Reference drug Vina score
        ref_vinardo: Reference drug Vinardo score
        w1: Weight for Vina (default 0.6)
        w2: Weight for Vinardo (default 0.4)

    Returns:
        ConsensusResult with all scores.
    """
    # Normalize relative to reference (both scores are negative, ratio works)
    if ref_vina != 0:
        norm_vina = vina_score / ref_vina
    else:
        norm_vina = 1.0

    if ref_vinardo != 0:
        norm_vinardo = vinardo_score / ref_vinardo
    else:
        norm_vinardo = 1.0

    consensus = (w1 * norm_vina) + (w2 * norm_vinardo)

    return ConsensusResult(
        vina_score=vina_score,
        vinardo_score=vinardo_score,
        consensus_score=round(consensus, 4),
    )
