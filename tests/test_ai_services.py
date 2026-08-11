"""Boltz-2 and the explainer: gating, grounding and graceful degradation."""

from unittest.mock import MagicMock, patch

import pytest
import requests

from drugforge.ai import boltz, explainer
from drugforge.domain.targets import get_target


@pytest.fixture
def target():
    return get_target("pf-dhfr")


@pytest.fixture
def result_payload(screening_result):
    return screening_result.to_dict()


def _with_key(monkeypatch, name="DEEPSEEK_API_KEY", value="test-key"):
    monkeypatch.setenv(name, value)


def test_boltz_is_unavailable_without_a_key():
    assert not boltz.is_available()


def test_boltz_becomes_available_with_a_key(monkeypatch):
    _with_key(monkeypatch, "BOLTZ_API_KEY")
    assert boltz.is_available()


def test_boltz_call_without_a_key_reports_status():
    result = boltz.confirm_binding("CCO", "1J3I")
    assert result.status == "unavailable"
    assert result.predicted_affinity is None


@pytest.mark.parametrize(
    ("rank", "passed", "expected"),
    [(1, True, True), (3, True, True), (4, True, False), (1, False, False)],
)
def test_boltz_gating(monkeypatch, rank, passed, expected):
    _with_key(monkeypatch, "BOLTZ_API_KEY")
    assert boltz.should_run(rank=rank, passed_admet=passed, top_n=3) is expected


def test_boltz_is_skipped_without_a_key_even_when_ranked_first():
    assert not boltz.should_run(rank=1, passed_admet=True)


@patch("drugforge.ai.boltz.requests.post")
def test_boltz_success(mock_post, monkeypatch):
    _with_key(monkeypatch, "BOLTZ_API_KEY")
    mock_post.return_value = MagicMock(
        status_code=200,
        json=lambda: {"predicted_affinity_kcal_mol": -7.8, "confidence": 0.82},
    )
    result = boltz.confirm_binding("CCO", "1J3I")
    assert result.status == "success"
    assert result.predicted_affinity == -7.8


@pytest.mark.parametrize(
    ("failure", "expected"),
    [
        (requests.Timeout(), "timeout"),
        (requests.ConnectionError(), "network_error"),
    ],
)
@patch("drugforge.ai.boltz.requests.post")
def test_boltz_network_failures_are_contained(mock_post, monkeypatch, failure, expected):
    _with_key(monkeypatch, "BOLTZ_API_KEY")
    mock_post.side_effect = failure
    result = boltz.confirm_binding("CCO", "1J3I")
    assert result.status == "error"
    assert result.error_detail == expected


@pytest.mark.parametrize(
    ("status_code", "expected"),
    [(429, "rate_limited"), (500, "server_error_500"), (404, "http_404")],
)
@patch("drugforge.ai.boltz.requests.post")
def test_boltz_http_failures_are_contained(mock_post, monkeypatch, status_code, expected):
    _with_key(monkeypatch, "BOLTZ_API_KEY")
    mock_post.return_value = MagicMock(status_code=status_code)
    result = boltz.confirm_binding("CCO", "1J3I")
    assert result.status == "error"
    assert result.error_detail == expected


def test_boltz_result_always_carries_a_disclaimer():
    assert boltz.confirm_binding("CCO", "1J3I").disclaimer


def test_explainer_prompt_contains_the_computed_numbers(result_payload, target):
    prompt = explainer.build_prompt(result_payload, target, "Malaria fact sheet.")
    for value in ("-8.123", "-7.2", "1.03", "248.71", "Promising"):
        assert value in prompt


def test_explainer_prompt_includes_the_fact_sheet(result_payload, target):
    facts = "DHFR reduces dihydrofolate to tetrahydrofolate."
    assert facts in explainer.build_prompt(result_payload, target, facts)


def test_explainer_prompt_names_the_reference_drug(result_payload, target):
    assert "pyrimethamine" in explainer.build_prompt(result_payload, target, "")


def test_explainer_marks_missing_values_explicitly(target):
    prompt = explainer.build_prompt({"molecule_smiles": "CCO"}, target, "")
    assert "not available" in prompt


def test_system_prompt_forbids_outside_claims():
    lowered = explainer.SYSTEM_PROMPT.lower()
    assert "only the data" in lowered
    assert "not enough data" in lowered


def test_missing_key_does_not_raise(result_payload, target):
    result = explainer.explain(result_payload, target)
    assert result.status == "unavailable"
    assert result.error_detail == "DEEPSEEK_API_KEY is not set"


@patch("drugforge.ai.explainer.requests.post")
def test_explainer_success(mock_post, monkeypatch, result_payload, target):
    _with_key(monkeypatch)
    mock_post.return_value = MagicMock(
        status_code=200,
        json=lambda: {"choices": [{"message": {"content": "Predicted binding..."}}]},
    )
    result = explainer.explain(result_payload, target)
    assert result.status == "success"
    assert "Predicted" in result.text


@patch("drugforge.ai.explainer.requests.post")
def test_explainer_http_failure_is_contained(mock_post, monkeypatch, result_payload, target):
    _with_key(monkeypatch)
    mock_post.return_value = MagicMock(status_code=500)
    assert explainer.explain(result_payload, target).status == "error"


@patch("drugforge.ai.explainer.requests.post")
def test_explainer_malformed_response_is_contained(
    mock_post, monkeypatch, result_payload, target
):
    _with_key(monkeypatch)
    mock_post.return_value = MagicMock(status_code=200, json=lambda: {"unexpected": 1})
    result = explainer.explain(result_payload, target)
    assert result.status == "error"
    assert result.error_detail == "invalid_response"


@patch("drugforge.ai.explainer.requests.post")
def test_explainer_timeout_is_contained(mock_post, monkeypatch, result_payload, target):
    _with_key(monkeypatch)
    mock_post.side_effect = requests.Timeout()
    assert explainer.explain(result_payload, target).error_detail == "timeout"


def test_fact_sheet_loads_for_a_known_target():
    facts = explainer.load_disease_facts("pf-dhfr")
    assert "Plasmodium" in facts or "DHFR" in facts


def test_unknown_target_returns_a_placeholder_fact_sheet():
    assert "No fact sheet" in explainer.load_disease_facts("no-such-target")
