# Boltz-2 Confirmation — Design

#[[file:.kiro/specs/boltz-confirmation/requirements.md]]

---

## 1. Boltz-2 Integration Architecture

```
Pipeline (normal flow):
  ... → consensus → drug-likeness → ADMET → compare → store → respond

Pipeline (with Boltz-2, top-N only):
  ... → consensus → drug-likeness → ADMET → compare → BOLTZ-2 → store → respond
                                                          ↓
                                               Only if:
                                               - BOLTZ_API_KEY is set
                                               - candidate is top-N by consensus
                                               - candidate passed ADMET filter
                                               - API is reachable

  If Boltz-2 unavailable:
    → skip, mark boltz_status = "unavailable", keep physics scores
```

---

## 2. Module Design

### `drugforge/boltz.py`

```python
@dataclass
class BoltzResult:
    """AI-based binding confirmation from Boltz-2 cloud API."""
    predicted_affinity: float | None    # AI-predicted binding affinity
    confidence: float | None            # model confidence (0-1)
    status: str                         # "success" | "unavailable" | "error" | "skipped"
    error_detail: str | None            # reason if status != "success"
    disclaimer: str = (
        "AI-predicted affinity from Boltz-2 is experimental and independent "
        "of the physics-based Vina score. It serves as supplementary confirmation "
        "only. Laboratory validation is required."
    )

BOLTZ_TOP_N: int = 3  # configurable

def is_boltz_available() -> bool:
    """Check if API key is set and service appears reachable."""

def call_boltz_api(
    smiles: str,
    target_pdb_id: str,
    pose_sdf: str,
) -> BoltzResult:
    """
    Call the Boltz-2 hosted API for a single molecule.
    
    - Reads BOLTZ_API_KEY from environment.
    - Timeout: 30 seconds.
    - Returns BoltzResult with status indicating outcome.
    - NEVER raises — all errors caught and returned as status.
    """

def should_run_boltz(
    rank: int,
    passed_admet: bool,
    top_n: int = BOLTZ_TOP_N,
) -> bool:
    """Determine if Boltz-2 should be invoked for this candidate."""
    return rank <= top_n and passed_admet and is_boltz_available()
```

---

## 3. API Request/Response to Boltz-2

### Outbound request (to Boltz-2 cloud)
```
POST https://api.boltz.bio/v2/predict
Headers:
  Authorization: Bearer $BOLTZ_API_KEY
  Content-Type: application/json
Body:
{
  "smiles": "...",
  "target_pdb_id": "1J3I",
  "pose_sdf": "...",           // optional: docked pose for context
  "prediction_type": "affinity"
}
```

### Inbound response (from Boltz-2)
```json
{
  "predicted_affinity_kcal_mol": -7.8,
  "confidence": 0.82,
  "model_version": "boltz-2.1"
}
```

**Note:** The exact Boltz-2 API spec will be configured when API access is
provisioned. The module is designed to adapt to the actual endpoint schema.

---

## 4. Pipeline Integration

### Single-molecule mode (`POST /api/dock`)
- Boltz-2 is called if:
  - `BOLTZ_API_KEY` is set
  - Molecule passed ADMET
  - Caller explicitly requests it OR molecule meets threshold

### Batch/library mode (future)
- Dock all, rank by consensus, take top-N, send only those to Boltz-2.

### PipelineResult extension
```python
@dataclass
class PipelineResult:
    # ... existing fields ...
    boltz: BoltzResult | None     # None if skipped
```

---

## 5. Response Format

`POST /api/dock` response with Boltz-2:
```json
{
  "affinity_kcal_mol": -8.3,
  "consensus_score": 0.72,
  "boltz": {
    "predicted_affinity": -7.8,
    "confidence": 0.82,
    "status": "success",
    "disclaimer": "AI-predicted affinity from Boltz-2 is experimental..."
  }
}
```

Without Boltz-2 (graceful degradation):
```json
{
  "affinity_kcal_mol": -8.3,
  "consensus_score": 0.72,
  "boltz": {
    "predicted_affinity": null,
    "confidence": null,
    "status": "unavailable",
    "error_detail": "BOLTZ_API_KEY not set"
  }
}
```

---

## 6. Error Handling

| Scenario | Behavior |
|----------|----------|
| `BOLTZ_API_KEY` not set | status="unavailable", pipeline continues |
| API timeout (>30s) | status="error", error_detail="timeout", pipeline continues |
| API returns 429 (rate limit) | status="error", error_detail="rate_limited" |
| API returns 5xx | status="error", error_detail from response |
| Invalid JSON response | status="error", error_detail="invalid_response" |
| Network unreachable | status="error", error_detail="network_error" |

**None of these crash the pipeline.** The BoltzResult always has a `status` field.

---

## 7. Testing Strategy

### Test: Missing API key does not crash
```
Given: BOLTZ_API_KEY is not set (or empty)
When: pipeline runs
Then: boltz.status == "unavailable", pipeline completes normally with physics scores
```

### Test: Top-N gating
```
Given: a library of 10 molecules ranked by consensus
When: Boltz-2 is available
Then: only the top 3 (default N=3) are sent to the API, the rest have boltz=None
```

### Test: Graceful API failure
```
Given: BOLTZ_API_KEY is set but API returns 500
When: pipeline runs
Then: boltz.status == "error", error_detail present, pipeline completes
```

### Test: ADMET-filtered molecules skipped
```
Given: a molecule that failed ADMET
When: it would rank in top-N
Then: Boltz-2 is NOT called (should_run_boltz returns False)
```
