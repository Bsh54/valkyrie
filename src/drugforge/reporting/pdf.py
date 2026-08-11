"""PDF report generation.

Runs on CPU with no headless browser, so a report costs about as much as
rendering a molecule image.
"""

from __future__ import annotations

import logging
import tempfile
from io import BytesIO
from pathlib import Path

from rdkit import Chem
from rdkit.Chem import Draw

from drugforge.domain.models import IN_SILICO_DISCLAIMER

logger = logging.getLogger(__name__)

_BANNER = "IN-SILICO PREDICTION - NOT FOR CLINICAL USE"
_HIGHLIGHT = (255, 243, 205)


def render_molecule_png(smiles: str, size: tuple[int, int] = (350, 250)) -> bytes:
    """Render a 2D depiction, or empty bytes when the SMILES is unusable."""
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return b""
    buffer = BytesIO()
    Draw.MolToImage(mol, size=size).save(buffer, format="PNG")
    return buffer.getvalue()


def build_report(result: dict) -> bytes:
    """Render a screening result as a two-page PDF."""
    from fpdf import FPDF

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    _summary_page(pdf, result)
    _detail_page(pdf, result)
    return bytes(pdf.output())


def _block(pdf, text: str, height: float, **kwargs) -> None:
    """Write a full-width block and return the cursor to the left margin.

    fpdf2 leaves the cursor to the right of a multi_cell by default, which
    starves the next full-width write of horizontal space.
    """
    from fpdf.enums import XPos, YPos

    pdf.multi_cell(0, height, text, new_x=XPos.LMARGIN, new_y=YPos.NEXT, **kwargs)


def _banner(pdf, text: str) -> None:
    pdf.set_fill_color(*_HIGHLIGHT)
    pdf.set_font("Helvetica", "B", 10)
    _block(pdf, text, 6, align="C", fill=True)
    pdf.ln(2)


def _heading(pdf, text: str) -> None:
    pdf.set_font("Helvetica", "B", 12)
    _block(pdf, text, 7)


def _line(pdf, text: str) -> None:
    pdf.set_font("Helvetica", "", 10)
    _block(pdf, text, 5)


def _summary_page(pdf, result: dict) -> None:
    pdf.add_page()
    _banner(pdf, _BANNER)

    pdf.set_font("Helvetica", "B", 16)
    _block(pdf, "DrugForge screening report", 10)
    _line(pdf, f"Result: {result.get('result_id', 'not stored')}")
    _line(pdf, f"Generated: {result.get('timestamp', 'unknown')}")
    pdf.ln(3)

    _heading(pdf, "Molecule")
    smiles = result.get("molecule_smiles", "unknown")
    _line(pdf, f"SMILES: {smiles}")
    _line(pdf, f"Target: {result.get('target_id', 'unknown')}")
    pdf.ln(2)

    image = render_molecule_png(smiles)
    if image:
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as handle:
            handle.write(image)
            image_path = Path(handle.name)
        try:
            pdf.image(str(image_path), x=10, w=70)
            pdf.ln(3)
        finally:
            image_path.unlink(missing_ok=True)

    pdf.set_font("Helvetica", "B", 14)
    _block(pdf, f"Verdict: {result.get('verdict', 'unknown')}", 9)
    pdf.ln(1)

    _heading(pdf, "Scores")
    _line(pdf, f"Vina affinity: {result.get('affinity_kcal_mol', 'n/a')} kcal/mol")
    _line(pdf, f"Vinardo score: {result.get('vinardo_score', 'n/a')} kcal/mol")
    _line(pdf, f"Consensus vs reference: {result.get('consensus_score', 'n/a')}")
    pdf.ln(2)

    _heading(pdf, "Pipeline")
    for label, value in _funnel_rows(result):
        _line(pdf, f"  {label}: {value}")


def _funnel_rows(result: dict) -> list[tuple[str, str]]:
    admet = result.get("admet") or {}
    drug_likeness = result.get("drug_likeness") or {}
    boltz = result.get("boltz") or {}

    admet_state = "clean"
    if admet.get("passes_filter") is False:
        admet_state = "; ".join(admet.get("failure_reasons") or ["filtered"])

    boltz_state = boltz.get("status", "not invoked")
    if boltz_state == "success":
        boltz_state = f"{boltz.get('predicted_affinity')} kcal/mol"

    return [
        ("Vina docking", f"{result.get('affinity_kcal_mol', 'n/a')} kcal/mol"),
        ("Vinardo rescoring", f"{result.get('vinardo_score', 'n/a')} kcal/mol"),
        ("Consensus", str(result.get("consensus_score", "n/a"))),
        (
            "Drug-likeness",
            f"{drug_likeness.get('lipinski_violations', 'n/a')} Lipinski violations",
        ),
        ("ADMET filter", admet_state),
        ("Boltz-2 confirmation", boltz_state),
    ]


def _detail_page(pdf, result: dict) -> None:
    pdf.add_page()

    _heading(pdf, "Comparison with the reference drug")
    widths = (45, 33, 33, 25, 30)
    headers = ("Metric", "Molecule", "Reference", "Delta", "Verdict")

    pdf.set_font("Helvetica", "B", 9)
    for width, header in zip(widths, headers, strict=True):
        pdf.cell(width, 6, header, border=1)
    pdf.ln()

    pdf.set_font("Helvetica", "", 9)
    for comparison in result.get("comparisons") or []:
        cells = (
            str(comparison.get("metric", "")),
            str(comparison.get("molecule_value", "")),
            str(comparison.get("reference_value", "")),
            str(comparison.get("delta", "")),
            str(comparison.get("verdict", "")),
        )
        for width, cell in zip(widths, cells, strict=True):
            pdf.cell(width, 5, cell, border=1)
        pdf.ln()
    pdf.ln(4)

    admet = result.get("admet") or {}
    _heading(pdf, "ADMET profile")
    _line(pdf, f"Predicted log S: {admet.get('esol_logs', 'n/a')}")
    _line(pdf, f"GI absorption: {admet.get('gi_absorption', 'n/a')}")
    _line(pdf, f"PAINS alerts: {_joined(admet.get('pains_alerts'))}")
    _line(pdf, f"Brenk alerts: {_joined(admet.get('brenk_alerts'))}")
    _line(pdf, f"Reactive groups: {_joined(admet.get('reactive_groups'))}")
    _line(pdf, f"Hit: {'yes' if result.get('is_hit') else 'no'}")

    reasons = result.get("hit_failure_reasons") or []
    if reasons:
        _line(pdf, f"Filtered because: {'; '.join(reasons)}")
    pdf.ln(3)

    explanation = result.get("explanation") or {}
    if explanation.get("status") == "success" and explanation.get("text"):
        _heading(pdf, "Explanation")
        pdf.set_font("Helvetica", "I", 9)
        _block(pdf, explanation["text"], 4)
        pdf.ln(2)
        pdf.set_font("Helvetica", "", 8)
        _block(pdf, explanation.get("disclaimer", ""), 4)
        pdf.ln(2)

    _banner(pdf, IN_SILICO_DISCLAIMER)


def _joined(values: object) -> str:
    return ", ".join(values) if isinstance(values, list) and values else "none"
