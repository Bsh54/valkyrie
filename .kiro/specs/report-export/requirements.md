# Report Export — Requirements

## Feature
A downloadable PDF report for any docking result, generated server-side on CPU.
Contains molecule identity, disease target, full funnel outcome, 3D pose image,
grounded natural-language explanation, and in-silico-only disclaimer.

## Requirements (EARS notation)

### REQ-RE-1: PDF Generation
The system shall generate a PDF report for any stored docking result when a user
requests a download via `GET /api/result/{id}/report`.

### REQ-RE-2: Report Content
The system shall include in the PDF report:
- Molecule identity (name/SMILES, canonical SMILES)
- Disease target (name, PDB id, reference drug)
- Full funnel outcome: Vina score, Vinardo score, consensus score, Boltz-2 AI
  confirmation (if available), ADMET filter results
- Verdict badge (Promising / Comparable / Weak / Discard)
- Comparison table (molecule vs reference drug, all metrics)
- 3D pose image (static render of the docked pose)
- Grounded natural-language explanation (from ai-explainer, if available)
- In-silico-only disclaimer (prominent, on every page)

### REQ-RE-3: Server-Side CPU
The system shall generate the PDF server-side using CPU-only libraries (no GPU,
no headless browser). Must complete within a reasonable time (<10s).

### REQ-RE-4: Real Data Only
The system shall populate the report with the actual computed numbers from the
stored result — never simulated, placeholder, or hard-coded values.

### REQ-RE-5: Disclaimer Prominence
The system shall place the in-silico-only disclaimer prominently at the top and
bottom of the report, and include a "NOT FOR CLINICAL USE" watermark or header.

### REQ-RE-6: Pose Image
The system shall generate a static 2D/3D image of the docked pose for the PDF.
If a full 3D render is not feasible on CPU, a 2D depiction of the molecule
(RDKit) with key binding metrics annotated is acceptable.

## Constraints
- CPU only (8 GB VPS, no GPU, no headless Chrome/Puppeteer).
- Use `reportlab` or `fpdf2` for PDF generation (lightweight, no wkhtmltopdf).
- Use RDKit's `Draw` module for molecule 2D depiction.
- Report must be self-contained (no external dependencies at read time).
