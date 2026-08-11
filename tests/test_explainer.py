"""Tests for the AI explainer module."""

import pytest
from unittest.mock import patch, MagicMock

from drugforge.explainer import (
    Explanation,
    build_prompt,
    generate_explanation,
    is_explainer_available,
    load_disease_facts,
)


def _make_result_dict():
    """Create a minimal result dict for testing."""
    return {
        "molecule_smiles": "CCO",
        "target_id": "pf-dhfr",
        "affinity_kcal_mol": -8.1,
        "vinardo_score": -7.2,
        "consensus_score": 1.03,
        "verdict": "Promising",
        "is_hit": True,
        "drug_likeness": {
            "molecular_weight": 232.5,
            "logp": 2.8,
            "hbd": 1,
            "hba": 3,
            "tpsa": 45.2,
            "rotatable_bonds": 2,
            "lipinski_violations": 0,
        },
        "admet": {
            "esol_logs": -3.1,
            "gi_absorption": "High",
            "pains_alerts": [],
            "passes_filter": True,
        },
        "comparisons": [
            {"metric": "affinity", "molecule_value": -8.1, "reference_value": -7.9},
        ],
    }


def test_prompt_contains_real_numbers():
    """Built prompt must contain the actual computed values."""
    result = _make_result_dict()
    prompt = build_prompt(result, "Some disease facts")

    assert "-8.1" in prompt
    assert "-7.2" in prompt
    assert "1.03" in prompt
    assert "232.5" in prompt
    assert "2.8" in prompt
    assert "Promising" in prompt
    assert "HIT" in prompt


def test_prompt_contains_disease_facts():
    """Disease facts text should be included in the prompt."""
    result = _make_result_dict()
    facts = "Malaria kills 600000 people per year."
    prompt = build_prompt(result, facts)

    assert "Malaria kills 600000" in prompt


@patch.dict("os.environ", {"DEEPSEEK_API_KEY": ""}, clear=False)
def test_missing_api_key_no_crash():
    """Missing API key returns unavailable, no crash."""
    result = _make_result_dict()
    explanation = generate_explanation(result, "pf-dhfr")

    assert isinstance(explanation, Explanation)
    assert explanation.status == "unavailable"
    assert explanation.error_detail == "DEEPSEEK_API_KEY not set"


@patch.dict("os.environ", {"DEEPSEEK_API_KEY": ""}, clear=False)
def test_explainer_unavailable_no_key():
    """is_explainer_available() returns False without key."""
    assert is_explainer_available() is False


@patch.dict("os.environ", {"DEEPSEEK_API_KEY": "test-key"}, clear=False)
def test_explainer_available_with_key():
    """is_explainer_available() returns True with key."""
    assert is_explainer_available() is True


def test_load_disease_facts_pf_dhfr():
    """Disease fact sheet for pf-dhfr should load and mention Plasmodium."""
    facts = load_disease_facts("pf-dhfr")
    assert len(facts) > 0
    assert "Plasmodium" in facts or "DHFR" in facts


def test_load_disease_facts_unknown():
    """Unknown target returns fallback message."""
    facts = load_disease_facts("nonexistent-target")
    assert "No disease fact sheet" in facts


def test_explanation_disclaimer():
    """Every Explanation has a non-empty disclaimer about predictions."""
    expl = Explanation(text="test", status="success")
    assert expl.disclaimer
    assert "prediction" in expl.disclaimer.lower() or "in silico" in expl.disclaimer.lower()


@patch.dict("os.environ", {"DEEPSEEK_API_KEY": "fake-key"}, clear=False)
@patch("drugforge.explainer.requests.post")
def test_successful_api_call(mock_post):
    """Mocked successful API call returns explanation text."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "choices": [{"message": {"content": "This molecule shows promise..."}}]
    }
    mock_post.return_value = mock_resp

    result = _make_result_dict()
    explanation = generate_explanation(result, "pf-dhfr")

    assert explanation.status == "success"
    assert "promise" in explanation.text.lower()


@patch.dict("os.environ", {"DEEPSEEK_API_KEY": "fake-key"}, clear=False)
@patch("drugforge.explainer.requests.post")
def test_api_error_handled(mock_post):
    """API error returns error status, no crash."""
    mock_resp = MagicMock()
    mock_resp.status_code = 500
    mock_post.return_value = mock_resp

    result = _make_result_dict()
    explanation = generate_explanation(result, "pf-dhfr")

    assert explanation.status == "error"
    assert "500" in explanation.error_detail
