"""Boltz-2 AI confirmation — cloud API client for binding affinity prediction."""

import logging
import os
from dataclasses import dataclass, field, asdict
from typing import Optional

import requests

from drugforge.config import BOLTZ_API_URL, BOLTZ_API_TIMEOUT, BOLTZ_TOP_N

logger = logging.getLogger(__name__)

_DISCLAIMER = (
    "AI-predicted affinity from Boltz-2 is experimental and independent "
    "of the physics-based Vina score. It serves as supplementary confirmation "
    "only. Laboratory validation is required."
)


@dataclass
class BoltzResult:
    """AI-based binding confirmation from Boltz-2 cloud API."""
    predicted_affinity: Optional[float] = None
    confidence: Optional[float] = None
    status: str = "unavailable"  # "success" | "unavailable" | "error" | "skipped"
    error_detail: Optional[str] = None
    disclaimer: str = field(default=_DISCLAIMER)

    def to_dict(self) -> dict:
        return {
            "predicted_affinity": self.predicted_affinity,
            "confidence": self.confidence,
            "status": self.status,
            "error_detail": self.error_detail,
            "disclaimer": self.disclaimer,
        }


def is_boltz_available() -> bool:
    """Check if the Boltz-2 API key is configured."""
    key = os.environ.get("BOLTZ_API_KEY", "").strip()
    return len(key) > 0


def should_run_boltz(
    rank: int,
    passed_admet: bool,
    top_n: int = BOLTZ_TOP_N,
) -> bool:
    """
    Determine if Boltz-2 should be invoked for this candidate.

    Only top-N candidates that passed ADMET and have an available API key
    are sent to the Boltz-2 API.
    """
    return rank <= top_n and passed_admet and is_boltz_available()


def call_boltz_api(
    smiles: str,
    target_pdb_id: str,
    pose_sdf: str = "",
) -> BoltzResult:
    """
    Call the Boltz-2 hosted API for a single molecule.

    Reads BOLTZ_API_KEY from environment. Timeout: configurable (default 30s).
    Returns BoltzResult with status indicating outcome.
    NEVER raises — all errors caught and returned as status.
    """
    api_key = os.environ.get("BOLTZ_API_KEY", "").strip()
    if not api_key:
        return BoltzResult(
            status="unavailable",
            error_detail="BOLTZ_API_KEY not set",
        )

    try:
        payload = {
            "smiles": smiles,
            "target_pdb_id": target_pdb_id,
            "pose_sdf": pose_sdf,
            "prediction_type": "affinity",
        }

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        resp = requests.post(
            BOLTZ_API_URL,
            json=payload,
            headers=headers,
            timeout=BOLTZ_API_TIMEOUT,
        )

        if resp.status_code == 429:
            return BoltzResult(
                status="error",
                error_detail="rate_limited",
            )

        if resp.status_code >= 500:
            return BoltzResult(
                status="error",
                error_detail=f"server_error_{resp.status_code}",
            )

        if resp.status_code != 200:
            return BoltzResult(
                status="error",
                error_detail=f"http_{resp.status_code}: {resp.text[:200]}",
            )

        data = resp.json()
        return BoltzResult(
            predicted_affinity=data.get("predicted_affinity_kcal_mol"),
            confidence=data.get("confidence"),
            status="success",
        )

    except requests.Timeout:
        return BoltzResult(
            status="error",
            error_detail="timeout",
        )
    except requests.ConnectionError:
        return BoltzResult(
            status="error",
            error_detail="network_error",
        )
    except (ValueError, KeyError) as e:
        return BoltzResult(
            status="error",
            error_detail=f"invalid_response: {e}",
        )
    except Exception as e:
        return BoltzResult(
            status="error",
            error_detail=f"{type(e).__name__}: {e}",
        )
