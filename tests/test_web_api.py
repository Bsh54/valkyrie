"""HTTP contract: status codes, error mapping and payload shape."""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from drugforge.errors import (
    DockingError,
    PipelineError,
    ReceptorError,
    TargetNotFoundError,
    ValidationError,
)
from drugforge.web.app import create_app


@pytest.fixture
def client():
    return TestClient(create_app())


def test_health_reports_a_disclaimer(client):
    body = client.get("/api/health").json()
    assert body["status"] == "ok"
    assert body["disclaimer"]


def test_targets_are_listed(client):
    body = client.get("/api/targets").json()
    assert any(target["id"] == "pf-dhfr" for target in body)


def test_target_detail_exposes_the_box_and_reference(client):
    body = client.get("/api/targets/pf-dhfr").json()
    assert body["pdb_id"] == "1J3I"
    assert len(body["box"]["center"]) == 3
    assert body["reference"]["name"] == "pyrimethamine"


def test_unknown_target_is_not_found(client):
    assert client.get("/api/targets/nope").status_code == 404


def test_compounds_carry_framing_and_citations(client):
    body = client.get("/api/compounds").json()
    assert body["disclaimer"]
    assert body["compounds"]
    for compound in body["compounds"]:
        assert compound["source"]
        assert compound["plant"]["scientific_name"]


def test_unknown_compound_is_not_found(client):
    assert client.get("/api/compounds/nope").status_code == 404


def test_benchmarks_state_their_scope(client):
    body = client.get("/api/benchmarks").json()
    assert "in-silico" in body["scope_statement"].lower()
    assert body["internal_status"] in {"available", "not_run"}


@patch("drugforge.web.routes.screening.run_screening")
def test_successful_screening_returns_the_full_result(mock_run, client, screening_result):
    mock_run.return_value = screening_result
    response = client.post(
        "/api/screenings", json={"molecule": "ethanol", "target_id": "pf-dhfr"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["result_id"]
    assert body["affinity_kcal_mol"] == -8.123
    assert body["consensus_score"] == 1.03
    assert body["disclaimer"]


@patch("drugforge.web.routes.screening.run_screening")
def test_stored_result_is_retrievable(mock_run, client, screening_result):
    mock_run.return_value = screening_result
    created = client.post(
        "/api/screenings", json={"molecule": "ethanol", "target_id": "pf-dhfr"}
    ).json()

    fetched = client.get(f"/api/screenings/{created['result_id']}")
    assert fetched.status_code == 200
    assert fetched.json()["molecule_smiles"] == "CCO"


@patch("drugforge.web.routes.screening.run_screening")
def test_report_downloads_as_pdf(mock_run, client, screening_result):
    mock_run.return_value = screening_result
    created = client.post(
        "/api/screenings", json={"molecule": "ethanol", "target_id": "pf-dhfr"}
    ).json()

    response = client.get(f"/api/screenings/{created['result_id']}/report")
    assert response.status_code == 200
    assert "application/pdf" in response.headers["content-type"]
    assert "attachment" in response.headers["content-disposition"]
    assert response.content[:4] == b"%PDF"


def test_missing_result_is_not_found(client):
    assert client.get("/api/screenings/absent").status_code == 404
    assert client.get("/api/screenings/absent/report").status_code == 404


@pytest.mark.parametrize(
    ("cause", "expected_status"),
    [
        (ValidationError("bad molecule"), 422),
        (TargetNotFoundError("no target"), 404),
        (ReceptorError("rcsb down"), 502),
        (DockingError("vina crashed"), 500),
    ],
)
@patch("drugforge.web.routes.screening.run_screening")
def test_pipeline_failures_map_to_status_codes(
    mock_run, client, cause, expected_status
):
    mock_run.side_effect = PipelineError(stage="validate", cause=cause)
    response = client.post(
        "/api/screenings", json={"molecule": "x", "target_id": "pf-dhfr"}
    )
    assert response.status_code == expected_status
    assert response.json()["detail"]["stage"] == "validate"


def test_request_validation_rejects_an_empty_molecule(client):
    response = client.post(
        "/api/screenings", json={"molecule": "", "target_id": "pf-dhfr"}
    )
    assert response.status_code == 422


def test_request_validation_bounds_exhaustiveness(client):
    response = client.post(
        "/api/screenings",
        json={"molecule": "CCO", "target_id": "pf-dhfr", "exhaustiveness": 999},
    )
    assert response.status_code == 422
