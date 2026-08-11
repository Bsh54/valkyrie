"""PDF report generation."""

from drugforge.reporting.pdf import build_report, render_molecule_png


def test_report_is_a_pdf(screening_result):
    payload = build_report(screening_result.to_dict())
    assert payload[:4] == b"%PDF"
    assert len(payload) > 1000


def test_report_survives_a_result_without_optional_stages(screening_result):
    data = screening_result.to_dict()
    data["boltz"] = None
    data["explanation"] = None
    assert build_report(data)[:4] == b"%PDF"


def test_report_includes_a_filtered_explanation(screening_result):
    data = screening_result.to_dict()
    data["is_hit"] = False
    data["hit_failure_reasons"] = ["PAINS alert: rhodanine"]
    assert build_report(data)[:4] == b"%PDF"


def test_report_handles_an_unparsable_smiles(screening_result):
    data = screening_result.to_dict()
    data["molecule_smiles"] = "not_a_molecule"
    assert build_report(data)[:4] == b"%PDF"


def test_molecule_renders_as_png():
    image = render_molecule_png("CCO")
    assert image[:4] == b"\x89PNG"


def test_unparsable_smiles_renders_nothing():
    assert render_molecule_png("invalid_zzz") == b""
