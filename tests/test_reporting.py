"""PDF report generation."""

from valkyrie.domain.models import Explanation
from valkyrie.reporting.pdf import _encodable, build_report, render_molecule_png


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


def test_report_accepts_non_latin1_explanation_text(screening_result):
    """Model output routinely contains characters the core fonts cannot encode."""
    screening_result.explanation = Explanation(
        text=(
            "Predicted affinity is stronger \u2014 about 1.2 kcal/mol \u2265 the "
            "reference \u2018baseline\u2019, within 4.5 \u00c5 of the pocket "
            "\u00b5-site \u2026 see notes."
        ),
        status="success",
    )
    assert build_report(screening_result.to_dict())[:4] == b"%PDF"


def test_report_replaces_typographic_characters():
    assert _encodable("a \u2014 b \u2019c\u2026") == "a - b 'c..."


def test_report_survives_unknown_unicode():
    assert _encodable("\u4e2d\u6587") == "??"


def test_molecule_renders_as_png():
    image = render_molecule_png("CCO")
    assert image[:4] == b"\x89PNG"


def test_unparsable_smiles_renders_nothing():
    assert render_molecule_png("invalid_zzz") == b""
