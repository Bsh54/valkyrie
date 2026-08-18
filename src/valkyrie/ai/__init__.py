"""Optional hosted AI services.

Both modules degrade to a status instead of raising, so the physics-based
result is never lost to an unavailable third party.
"""

from valkyrie.ai import boltz, explainer

__all__ = ["boltz", "explainer"]
