# Boltz-2 Confirmation — Requirements

## Feature
Add an AI confirmation stage using the Boltz-2 cloud API for the top consensus
candidates only. Provides an independent AI-based binding prediction alongside
the physics-based Vina/consensus scores.

## Requirements (EARS notation)

### REQ-BC-1: Top-N Only
The system shall send only the top-N candidates (configurable, default N=3) to
the Boltz-2 API to obtain an AI binding-affinity / confidence estimate when
processing batch results or when explicitly requested for a single molecule.

### REQ-BC-2: Cloud API Only
The system shall NEVER run Boltz locally (no GPU on the 8 GB VPS). It shall call
the hosted Boltz-2 API endpoint, reading the API key from the `BOLTZ_API_KEY`
environment variable.

### REQ-BC-3: Graceful Degradation
The system shall degrade gracefully when the API key is missing or the service
is unavailable: skip the AI stage entirely, keep the physics-based scores as
the primary result, and indicate in the response that AI confirmation was
unavailable.

### REQ-BC-4: Clear Labeling
The system shall clearly label AI-derived numbers as "predictive/experimental"
and keep the physics-based result (Vina + consensus) as the primary score. AI
scores are presented as independent confirmation, never as replacement.

### REQ-BC-5: Invocation Efficiency
The system shall invoke the Boltz-2 API only for top-N candidates — never for
the entire compound library, individual low-scoring molecules, or molecules that
failed the ADMET filter.

### REQ-BC-6: Non-Crash Guarantee
The system shall never crash due to Boltz-2 API failures (timeout, rate limit,
invalid response). All API errors are caught, logged, and the pipeline continues
with physics scores only.

## Constraints
- Boltz-2 is a cloud API — subject to rate limits, latency, and cost.
- API key stored in env var `BOLTZ_API_KEY`, never committed to code.
- The AI score is supplementary; physics-based score remains authoritative.
- Timeout: 30 seconds per API call.
