"""Boltz-2 binding confirmation through the hosted API.

Never runs locally: the deployment target has no GPU. Every failure path returns
a status instead of raising, so the physics-based result always survives.
"""

from __future__ import annotations

import logging

import requests

from valkyrie.config import (
    BOLTZ_API_TIMEOUT_S,
    BOLTZ_API_URL,
    BOLTZ_TOP_N,
    boltz_api_key,
)
from valkyrie.domain.models import BoltzResult

logger = logging.getLogger(__name__)


def is_available() -> bool:
    return bool(boltz_api_key())


def should_run(rank: int, passed_admet: bool, top_n: int = BOLTZ_TOP_N) -> bool:
    """Gate the API to top-ranked candidates that cleared the ADMET filter."""
    return rank <= top_n and passed_admet and is_available()


def confirm_binding(
    smiles: str, target_pdb_id: str, pose_sdf: str = ""
) -> BoltzResult:
    """Request an AI affinity estimate for one molecule."""
    api_key = boltz_api_key()
    if not api_key:
        return BoltzResult(status="unavailable", error_detail="BOLTZ_API_KEY is not set")

    payload = {
        "smiles": smiles,
        "target_pdb_id": target_pdb_id,
        "pose_sdf": pose_sdf,
        "prediction_type": "affinity",
    }

    try:
        response = requests.post(
            BOLTZ_API_URL,
            json=payload,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            timeout=BOLTZ_API_TIMEOUT_S,
        )
    except requests.Timeout:
        return BoltzResult(status="error", error_detail="timeout")
    except requests.ConnectionError:
        return BoltzResult(status="error", error_detail="network_error")
    except requests.RequestException as exc:
        return BoltzResult(status="error", error_detail=type(exc).__name__)

    if response.status_code == 429:
        return BoltzResult(status="error", error_detail="rate_limited")
    if response.status_code >= 500:
        return BoltzResult(
            status="error", error_detail=f"server_error_{response.status_code}"
        )
    if response.status_code != 200:
        return BoltzResult(status="error", error_detail=f"http_{response.status_code}")

    try:
        data = response.json()
    except ValueError:
        return BoltzResult(status="error", error_detail="invalid_response")

    return BoltzResult(
        predicted_affinity=data.get("predicted_affinity_kcal_mol"),
        confidence=data.get("confidence"),
        status="success",
    )
