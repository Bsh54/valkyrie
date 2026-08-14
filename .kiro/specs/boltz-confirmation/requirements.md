# Boltz-2 Confirmation — RETIRED

## Status: cancelled, not built

This feature was designed (see the previous version of this document in git
history) but is not implemented. Boltz-2 needs a GPU and is not a free API;
neither is available in this deployment (8 GB VPS, CPU only). The stage does
not appear anywhere in the pipeline, the funnel, or the UI.

The `boltz` field remains on `ScreeningResult`
(`src/drugforge/domain/models.py`) and an unused stub exists at
`src/drugforge/ai/boltz.py`, kept only for forward compatibility so a future
implementation does not require a schema migration. Nothing populates the
field in normal operation, and nothing in the frontend reads it
(`web-ui` REQ-UI-17).

If this feature is revived, the original requirements (top-N gating, cloud-only
execution, graceful degradation, clear "predictive/experimental" labelling, and
a non-crash guarantee on API failure) remain the right design and should be
restored rather than redesigned from scratch.
