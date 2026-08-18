"""Valkyrie: molecular docking for neglected tropical diseases.

Layers, from inner to outer:
    domain      pure models and the target registry
    chem        cheminformatics: resolution, preparation, descriptors, ADMET
    docking     Vina execution, rescoring, consensus
    ai          optional hosted services, always degradable
    pipeline    stage orchestration and reference comparison
    storage     SQLite persistence
    analytics   benchmark metrics
    reporting   PDF export
    web         HTTP transport

Results are in-silico predictions and never clinical advice.
"""

__version__ = "0.2.0"
