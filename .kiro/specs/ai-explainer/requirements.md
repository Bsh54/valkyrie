# AI Explainer — Requirements

## Feature
A grounded natural-language explanation layer using the DeepSeek API (model
deepseek-v4-flash). Generates plain-language interpretations of docking results
using ONLY the data provided by Valkyrie.

## Requirements (EARS notation)

### REQ-AE-1: Grounded Explanation
The system shall generate a plain-language explanation of a docking result using
ONLY the data provided by Valkyrie: the affinity score, the drug-likeness
metrics, the comparison to the target's reference drug, the ADMET results, and
a curated per-disease fact sheet stored in the repo.

### REQ-AE-2: No External Citations
The system shall instruct the model to never cite any reference or fact not
present in the provided context, and to say "not enough data" when information
is missing. The model must not hallucinate sources, mechanisms, or claims.

### REQ-AE-3: API Key from Environment
The system shall read the DeepSeek API key from the `DEEPSEEK_API_KEY`
environment variable, never from source code. The key shall never appear in
logs, responses, or error messages.

### REQ-AE-4: Graceful Degradation
The system shall degrade gracefully when the API key is absent or the service
is unavailable: show the raw numbers without any generated explanation, and
indicate "AI explanation unavailable" in the response.

### REQ-AE-5: Scientific Caution
The system shall keep every explanation scientifically cautious: all language
must use "predicted", "in silico", "suggests" (not "proves", "works", "cures").
An honest-scope disclaimer must accompany every explanation.

### REQ-AE-6: Context Fidelity
The system shall ensure the prompt context sent to DeepSeek contains the real
computed numbers (affinity, drug-likeness, comparison values) — never placeholder
or template values.

### REQ-AE-7: Per-Disease Fact Sheet
The system shall load a curated per-disease fact sheet from `data/disease_facts/`
and include it in the prompt context to ground explanations in validated
background knowledge about the target disease and protein.

### REQ-AE-8: Interpretation, Not Restatement
The explanation shall interpret the result rather than restate the numbers
verbatim: it shall state how the molecule compares to the reference drug, name
the single biggest drug-likeness/ADMET strength and the single biggest
weakness, and close with one concrete, actionable takeaway consistent with the
computed verdict.

### REQ-AE-9: Traditional-Knowledge Bridge
When the docked molecule's canonical SMILES matches an entry in the
ethnobotanical library, the system shall include that entry's plant (scientific
and local name), traditional disease use, region, people, preparation and
source in the prompt context, and shall instruct the model to state cautiously
whether the in-silico result supports or nuances that traditional use, crediting
the plant and people. When there is no match, the system shall state plainly in
the context that no traditional-use record exists, rather than omitting the
section silently.

## Constraints
- DeepSeek API (model: deepseek-v4-flash) via standard OpenAI-compatible endpoint.
- API key from env var `DEEPSEEK_API_KEY`.
- Max response: 300 tokens (concise explanation, not an essay).
- Timeout: 15 seconds. Non-blocking for the main pipeline (async or optional).
- Never expose the API key or raw prompt in user-facing responses.
