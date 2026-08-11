"""Report export — PDF report generation for docking results."""

import logging
from io import BytesIO
from pathlib import Path

from rdkit import Chem
from rdkit.Chem import Draw

from drugforge.errors import DrugForgeError

logger = logging.getLogger(__name__)


def render_molecule_image(smiles: str, size=(350, 250)) -> bytes:
    """Render a 2D molecule depiction as PNG bytes."""
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return b""
    img = Draw.MolToImage(mol, size=size)
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def generate_report(result: dict) -> bytes:
    """
    Generate a PDF report from a stored docking result.

    Args:
        result: dict from store.get_result()

    Returns:
        PDF file content as bytes.
    """
    from fpdf import FPDF

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)

    # --- Page 1: Summary ---
    pdf.add_page()

    # Disclaimer header
    pdf.set_fill_color(255, 243, 205)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 8, "IN-SILICO PREDICTION - NOT FOR CLINICAL USE", ln=True,
             align="C", fill=True)
    pdf.ln(3)

    # Title
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "DrugForge - Molecular Docking Report", ln=True)
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(0, 5, f"Result ID: {result.get('result_id', 'N/A')}", ln=True)
    pdf.cell(0, 5, f"Generated: {result.get('timestamp', 'N/A')}", ln=True)
    pdf.ln(5)

    # Molecule identity
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 7, "Molecule Identity", ln=True)
    pdf.set_font("Helvetica", "", 10)
    smiles = result.get("molecule_smiles", "N/A")
    pdf.cell(0, 5, f"SMILES: {smiles}", ln=True)
    pdf.cell(0, 5, f"Target: {result.get('target_id', 'N/A')}", ln=True)
    pdf.ln(3)

    # Molecule image
    if smiles and smiles != "N/A":
        img_bytes = render_molecule_image(smiles)
        if img_bytes:
            img_path = Path("/tmp/drugforge_mol.png")
            img_path.write_bytes(img_bytes)
            pdf.image(str(img_path), x=10, w=70)
            pdf.ln(3)

    # Verdict
    verdict = result.get("verdict", "N/A")
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, f"VERDICT: {verdict}", ln=True)
    pdf.ln(2)

    # Scores
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 7, "Scores", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 5, f"Vina Affinity: {result.get('affinity_kcal_mol', 'N/A')} kcal/mol", ln=True)
    pdf.cell(0, 5, f"Vinardo Score: {result.get('vinardo_score', 'N/A')} kcal/mol", ln=True)
    pdf.cell(0, 5, f"Consensus Score: {result.get('consensus_score', 'N/A')}", ln=True)
    pdf.ln(3)

    # Pipeline Funnel
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 7, "Pipeline Funnel", ln=True)
    pdf.set_font("Helvetica", "", 10)

    affinity = result.get("affinity_kcal_mol", "N/A")
    vinardo = result.get("vinardo_score", "N/A")
    consensus = result.get("consensus_score", "N/A")
    dl = result.get("drug_likeness", {})
    admet = result.get("admet", {})
    boltz = result.get("boltz")

    pdf.cell(0, 5, f"  [PASS] Vina Docking: {affinity} kcal/mol", ln=True)
    pdf.cell(0, 5, f"  [PASS] Vinardo Rescore: {vinardo} kcal/mol", ln=True)
    pdf.cell(0, 5, f"  [PASS] Consensus: {consensus}", ln=True)

    lipinski = dl.get("lipinski_violations", 0)
    pdf.cell(0, 5, f"  [PASS] Drug-likeness: {lipinski} Lipinski violations", ln=True)

    admet_status = "PASS" if admet.get("passes_filter", True) else "FAIL"
    admet_reasons = admet.get("failure_reasons", [])
    if admet_status == "FAIL":
        pdf.cell(0, 5, f"  [FAIL] ADMET/Tox: {'; '.join(admet_reasons)}", ln=True)
    else:
        pdf.cell(0, 5, "  [PASS] ADMET/Tox: Clean", ln=True)

    if boltz:
        boltz_status = boltz.get("status", "unavailable")
        if boltz_status == "success":
            pdf.cell(0, 5, f"  [PASS] Boltz-2 AI: {boltz.get('predicted_affinity')} kcal/mol", ln=True)
        else:
            pdf.cell(0, 5, f"  [SKIP] Boltz-2 AI: {boltz_status}", ln=True)
    else:
        pdf.cell(0, 5, "  [SKIP] Boltz-2 AI: Not invoked", ln=True)

    # --- Page 2: Comparison + ADMET ---
    pdf.add_page()

    # Comparison table
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 7, "Comparison to Reference Drug", ln=True)
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(45, 6, "Metric", border=1)
    pdf.cell(35, 6, "Molecule", border=1)
    pdf.cell(35, 6, "Reference", border=1)
    pdf.cell(25, 6, "Delta", border=1)
    pdf.cell(30, 6, "Verdict", border=1, ln=True)

    pdf.set_font("Helvetica", "", 9)
    comparisons = result.get("comparisons", [])
    for comp in comparisons:
        if isinstance(comp, dict):
            pdf.cell(45, 5, str(comp.get("metric", "")), border=1)
            pdf.cell(35, 5, str(comp.get("molecule_value", "")), border=1)
            pdf.cell(35, 5, str(comp.get("reference_value", "")), border=1)
            pdf.cell(25, 5, str(comp.get("delta", "")), border=1)
            pdf.cell(30, 5, str(comp.get("verdict", "")), border=1, ln=True)
    pdf.ln(5)

    # ADMET details
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 7, "ADMET Profile", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 5, f"ESOL logS: {admet.get('esol_logs', 'N/A')}", ln=True)
    pdf.cell(0, 5, f"GI Absorption: {admet.get('gi_absorption', 'N/A')}", ln=True)
    pains = admet.get("pains_alerts", [])
    pdf.cell(0, 5, f"PAINS alerts: {', '.join(pains) if pains else 'None'}", ln=True)
    brenk = admet.get("brenk_alerts", [])
    pdf.cell(0, 5, f"Brenk alerts: {', '.join(brenk) if brenk else 'None'}", ln=True)
    reactive = admet.get("reactive_groups", [])
    pdf.cell(0, 5, f"Reactive groups: {', '.join(reactive) if reactive else 'None'}", ln=True)
    hit = result.get("is_hit", False)
    pdf.cell(0, 5, f"Hit status: {'PASS' if hit else 'FILTERED'}", ln=True)
    pdf.ln(5)

    # AI explanation
    explanation = result.get("explanation")
    if explanation and isinstance(explanation, dict):
        if explanation.get("status") == "success" and explanation.get("text"):
            pdf.set_font("Helvetica", "B", 12)
            pdf.cell(0, 7, "AI Explanation (DeepSeek)", ln=True)
            pdf.set_font("Helvetica", "I", 9)
            pdf.multi_cell(0, 4, explanation["text"])
            pdf.ln(3)

    # Footer disclaimer
    pdf.ln(5)
    pdf.set_fill_color(255, 243, 205)
    pdf.set_font("Helvetica", "B", 9)
    pdf.multi_cell(0, 5,
        "DISCLAIMER: All numbers are in-silico predictions based on "
        "computational models. This report does not constitute medical evidence. "
        "Laboratory validation is required before any clinical consideration.",
        fill=True)

    return pdf.output()
