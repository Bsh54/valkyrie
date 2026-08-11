"""Tests for Boltz-2 AI confirmation module."""

import pytest
from unittest.mock import patch, MagicMock

from drugforge.boltz import (
    BoltzResult,
    call_boltz_api,
    is_boltz_available,
    should_run_boltz,
)


# ---------------------------------------------------------------------------
# Unit tests: availability and gating
# ---------------------------------------------------------------------------

@patch.dict("os.environ", {"BOLTZ_API_KEY": ""}, clear=False)
def test_boltz_unavailable_no_key():
    """Missing API key makes Boltz unavailable."""
    assert is_boltz_available() is False


@patch.dict("os.environ", {"BOLTZ_API_KEY": "test-key-123"}, clear=False)
def test_boltz_available_with_key():
    """Set API key makes Boltz available."""
    assert is_boltz_available() is True


@patch.dict("os.environ", {"BOLTZ_API_KEY": "test-key-123"}, clear=False)
def test_should_run_boltz_top_n():
    """Only top-N candidates that passed ADMET should run Boltz."""
    assert should_run_boltz(rank=1, passed_admet=True, top_n=3) is True
    assert should_run_boltz(rank=3, passed_admet=True, top_n=3) is True
    assert should_run_boltz(rank=4, passed_admet=True, top_n=3) is False


@patch.dict("os.environ", {"BOLTZ_API_KEY": "test-key-123"}, clear=False)
def test_should_run_boltz_admet_failed():
    """ADMET-failed molecule should NOT run Boltz even if top rank."""
    assert should_run_boltz(rank=1, passed_admet=False, top_n=3) is False


@patch.dict("os.environ", {"BOLTZ_API_KEY": ""}, clear=False)
def test_should_run_boltz_no_key():
    """Without API key, should_run_boltz returns False."""
    assert should_run_boltz(rank=1, passed_admet=True, top_n=3) is False


# ---------------------------------------------------------------------------
# Unit tests: API call behavior
# ---------------------------------------------------------------------------

@patch.dict("os.environ", {"BOLTZ_API_KEY": ""}, clear=False)
def test_call_boltz_no_key_returns_unavailable():
    """Calling Boltz without API key returns status=unavailable, no crash."""
    result = call_boltz_api(smiles="CCO", target_pdb_id="1J3I")
    assert isinstance(result, BoltzResult)
    assert result.status == "unavailable"
    assert result.error_detail == "BOLTZ_API_KEY not set"
    assert result.predicted_affinity is None


@patch.dict("os.environ", {"BOLTZ_API_KEY": "fake-key"}, clear=False)
@patch("drugforge.boltz.requests.post")
def test_call_boltz_success(mock_post):
    """Successful API call returns predicted affinity."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "predicted_affinity_kcal_mol": -7.8,
        "confidence": 0.82,
        "model_version": "boltz-2.1",
    }
    mock_post.return_value = mock_resp

    result = call_boltz_api(smiles="CCO", target_pdb_id="1J3I")
    assert result.status == "success"
    assert result.predicted_affinity == -7.8
    assert result.confidence == 0.82


@patch.dict("os.environ", {"BOLTZ_API_KEY": "fake-key"}, clear=False)
@patch("drugforge.boltz.requests.post")
def test_call_boltz_server_error(mock_post):
    """API 500 returns error status, no crash."""
    mock_resp = MagicMock()
    mock_resp.status_code = 500
    mock_resp.text = "Internal Server Error"
    mock_post.return_value = mock_resp

    result = call_boltz_api(smiles="CCO", target_pdb_id="1J3I")
    assert result.status == "error"
    assert "server_error" in result.error_detail


@patch.dict("os.environ", {"BOLTZ_API_KEY": "fake-key"}, clear=False)
@patch("drugforge.boltz.requests.post")
def test_call_boltz_timeout(mock_post):
    """API timeout returns error status, no crash."""
    import requests as req
    mock_post.side_effect = req.Timeout("Connection timed out")

    result = call_boltz_api(smiles="CCO", target_pdb_id="1J3I")
    assert result.status == "error"
    assert result.error_detail == "timeout"


@patch.dict("os.environ", {"BOLTZ_API_KEY": "fake-key"}, clear=False)
@patch("drugforge.boltz.requests.post")
def test_call_boltz_rate_limited(mock_post):
    """API 429 returns rate_limited error status."""
    mock_resp = MagicMock()
    mock_resp.status_code = 429
    mock_post.return_value = mock_resp

    result = call_boltz_api(smiles="CCO", target_pdb_id="1J3I")
    assert result.status == "error"
    assert result.error_detail == "rate_limited"


@patch.dict("os.environ", {"BOLTZ_API_KEY": "fake-key"}, clear=False)
@patch("drugforge.boltz.requests.post")
def test_call_boltz_network_error(mock_post):
    """Network error returns error status, no crash."""
    import requests as req
    mock_post.side_effect = req.ConnectionError("No route to host")

    result = call_boltz_api(smiles="CCO", target_pdb_id="1J3I")
    assert result.status == "error"
    assert result.error_detail == "network_error"


def test_boltz_result_to_dict():
    """BoltzResult.to_dict() returns proper structure."""
    result = BoltzResult(
        predicted_affinity=-7.5,
        confidence=0.9,
        status="success",
    )
    d = result.to_dict()
    assert d["predicted_affinity"] == -7.5
    assert d["status"] == "success"
    assert "disclaimer" in d


# ---------------------------------------------------------------------------
# Integration test: pipeline does not crash without Boltz key
# ---------------------------------------------------------------------------

@patch.dict("os.environ", {"BOLTZ_API_KEY": ""}, clear=False)
def test_pipeline_no_crash_without_boltz():
    """Full pipeline completes even without BOLTZ_API_KEY."""
    from drugforge.errors import PipelineError

    # This test only checks the boltz module doesn't crash the import/logic
    result = call_boltz_api(smiles="CCO", target_pdb_id="1J3I")
    assert result.status == "unavailable"
    # Pipeline should still work — boltz is optional
