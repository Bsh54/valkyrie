"""HTTP contract: status codes, error mapping and payload shape."""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from drugforge.errors import DockingError, PipelineError, ValidationError
from drugforge.web import jobs
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


def test_screening_enqueues_a_job(client):
    with patch("drugforge.web.jobs.submit", return_value="jid123") as submit:
        response = client.post(
            "/api/screenings", json={"molecule": "ethanol", "target_id": "pf-dhfr"}
        )
    assert response.status_code == 200
    assert response.json() == {"job_id": "jid123", "status": "queued"}
    submit.assert_called_once()


def test_unknown_job_is_not_found(client):
    assert client.get("/api/jobs/absent").status_code == 404


def _run_job_now(job_id="test-job", molecule="ethanol"):
    """Seed and run one job synchronously, bypassing the worker thread."""
    jobs._jobs[job_id] = {"status": "queued", "position": 0, "result_id": None, "error": None}
    jobs._run(job_id, molecule, "pf-dhfr", 8)
    return job_id


def test_job_runs_stores_and_result_is_retrievable(client, screening_result):
    with patch("drugforge.web.jobs.run_screening", return_value=screening_result):
        job_id = _run_job_now()

    job = client.get(f"/api/jobs/{job_id}").json()
    assert job["status"] == "done"
    result_id = job["result_id"]
    assert result_id

    fetched = client.get(f"/api/screenings/{result_id}")
    assert fetched.status_code == 200
    assert fetched.json()["molecule_smiles"] == "CCO"


def test_report_downloads_as_pdf(client, screening_result):
    with patch("drugforge.web.jobs.run_screening", return_value=screening_result):
        job_id = _run_job_now(job_id="report-job")
    result_id = client.get(f"/api/jobs/{job_id}").json()["result_id"]

    response = client.get(f"/api/screenings/{result_id}/report")
    assert response.status_code == 200
    assert "application/pdf" in response.headers["content-type"]
    assert "attachment" in response.headers["content-disposition"]
    assert response.content[:4] == b"%PDF"


def test_missing_result_is_not_found(client):
    assert client.get("/api/screenings/absent").status_code == 404
    assert client.get("/api/screenings/absent/report").status_code == 404


@pytest.mark.parametrize(
    ("cause", "stage"),
    [
        (ValidationError("bad molecule"), "validate"),
        (DockingError("vina crashed"), "docking"),
    ],
)
def test_job_reports_pipeline_errors(screening_result, cause, stage):
    with patch(
        "drugforge.web.jobs.run_screening",
        side_effect=PipelineError(stage=stage, cause=cause),
    ):
        _run_job_now(job_id="err-job", molecule="x")

    job = jobs.get("err-job")
    assert job["status"] == "error"
    assert job["error"]["stage"] == stage
    assert job["error"]["detail"]


def test_cancelled_queued_job_is_skipped():
    with patch("drugforge.web.jobs.run_screening") as run:
        jobs._jobs["cancel-me"] = {"status": "queued", "position": 0, "result_id": None, "error": None}
        assert jobs.cancel("cancel-me") is True
        jobs._run("cancel-me", "CCO", "pf-dhfr", 8)
    assert jobs.get("cancel-me")["status"] == "cancelled"
    run.assert_not_called()


def test_cancel_route_reports_outcome(client):
    assert client.post("/api/jobs/absent/cancel").json() == {"job_id": "absent", "cancelled": False}


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
