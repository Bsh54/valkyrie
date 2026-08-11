"""Tests for the PDF report export module."""

import pytest
from unittest.mock import patch, MagicMock

from drugforge.report import generate_report, render_molecule_image


def _make_result_dict():
    """Create a minimal result dict for testing."""
    return {
        "result_id": "test-uuid-123",
        "timestamp": "2026-08-08T12:00:00Z",
        "molecule_smiles": "CCO",
        "target_id": "pf-dhfr",
        "affinity_kcal_mol": -8.1,
        "vinardo_score": -7.2,
        "consensus_score": 1.03,
        "verdict": "Promising",
        "is_hit": True,
        "drug_likeness": {
            "molecular_weight": 46.07,
            "logp": -0.31,
            "hbd": 1,
            "hba": 1,
            "tpsa": 20.23,
            "rotatable_bonds": 0,
            "lipinski_violations": 0,
        },
        "admet": {
            "esol_logs": -1.0,
            "gi_absorption": "High",
            "pains_alerts": [],
            "brenk_alerts": [],
            "reactive_groups": [],
            "passes_filter": True,
            "failure_reasons": [],
        },
        "comparisons": [
            {
                "metric": "affinity",
                "molecule_value": -8.1,
                "reference_value": -7.9,
                "delta": -0.2,
                "verdict": "better",
            }
        ],
        "boltz": None,
        "explanation": None,
    }


def test_report_produced():
    """Report generation returns non-empty PDF."""
    result = _make_result_dict()
    pdf_output = generate_report(result)

    # fpdf2 returns bytearray
    assert len(pdf_output) > 0
    # PDF magic bytes
    assert bytes(pdf_output)[:4] == b"%PDF"


def test_report_is_valid_pdf():
    """Generated output starts with PDF header."""
    result = _make_result_dict()
    pdf_output = generate_report(result)
    pdf_bytes = bytes(pdf_output)
    assert pdf_bytes.startswith(b"%PDF-1.")


def test_render_molecule_image():
    """Molecule image renders as PNG bytes."""
    img_bytes = render_molecule_image("CCO")
    assert isinstance(img_bytes, bytes)
    assert len(img_bytes) > 0
    # PNG magic bytes
    assert img_bytes[:4] == b"\x89PNG"


def test_render_invalid_smiles():
    """Invalid SMILES returns empty bytes."""
    img_bytes = render_molecule_image("invalid_xyz!!!")
    assert img_bytes == b""


def test_report_nonzero_size():
    """PDF should be a reasonable size (> 1KB for a real report)."""
    result = _make_result_dict()
    pdf_output = generate_report(result)
    assert len(pdf_output) > 1000


def test_report_api_endpoint():
    """GET /api/result/{id}/report returns PDF."""
    from fastapi.testclient import TestClient
    from drugforge.api import app

    result = _make_result_dict()
    with patch("drugforge.api.get_result", return_value=result):
        client = TestClient(app)
        response = client.get("/api/result/test-uuid-123/report")
        assert response.status_code == 200
        assert "application/pdf" in response.headers["content-type"]
        assert response.content[:4] == b"%PDF"


def test_report_api_not_found():
    """GET /api/result/{id}/report returns 404 for missing result."""
    from fastapi.testclient import TestClient
    from drugforge.api import app

    with patch("drugforge.api.get_result", return_value=None):
        client = TestClient(app)
        response = client.get("/api/result/nonexistent/report")
        assert response.status_code == 404
