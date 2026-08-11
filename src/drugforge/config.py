"""Runtime configuration.

All environment overrides are declared here so nothing else in the codebase
reads os.environ directly. Secrets are never given defaults.
"""

from __future__ import annotations

import os
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = PACKAGE_ROOT.parent.parent


def _path_from_env(name: str, default: Path) -> Path:
    value = os.environ.get(name)
    return Path(value).expanduser().resolve() if value else default


def _int_from_env(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, default))
    except ValueError:
        return default


DATA_DIR = _path_from_env("DRUGFORGE_DATA_DIR", PROJECT_ROOT / "data")
STATIC_DIR = _path_from_env("DRUGFORGE_STATIC_DIR", PROJECT_ROOT / "static")

RECEPTOR_CACHE_DIR = DATA_DIR / "receptors"
DISEASE_FACTS_DIR = DATA_DIR / "disease_facts"
BENCHMARK_SETS_DIR = DATA_DIR / "benchmark_sets"
BENCHMARKS_DIR = DATA_DIR / "benchmarks"
DATASET_DIR = DATA_DIR / "dataset"

COMPOUNDS_PATH = DATA_DIR / "compounds.json"
ETHNOBOTANICAL_PATH = DATA_DIR / "ethnobotanical.json"
DB_PATH = _path_from_env("DRUGFORGE_DB_PATH", DATA_DIR / "results.db")

DEFAULT_EXHAUSTIVENESS = 8
MIN_EXHAUSTIVENESS = 1
MAX_EXHAUSTIVENESS = 32
N_POSES = 5

# Bounded so a single request cannot saturate a small host.
VINA_CPU = _int_from_env("DRUGFORGE_VINA_CPU", 2)

RCSB_DOWNLOAD_URL = "https://files.rcsb.org/download/{pdb_id}.pdb"
PUBCHEM_SMILES_URL = (
    "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/"
    "{name}/property/CanonicalSMILES/JSON"
)
HTTP_TIMEOUT_S = _int_from_env("DRUGFORGE_HTTP_TIMEOUT", 15)

BOLTZ_API_URL = os.environ.get("BOLTZ_API_URL", "https://api.boltz.bio/v2/predict")
BOLTZ_API_TIMEOUT_S = _int_from_env("BOLTZ_API_TIMEOUT", 30)
BOLTZ_TOP_N = _int_from_env("BOLTZ_TOP_N", 3)

DEEPSEEK_API_URL = os.environ.get(
    "DEEPSEEK_API_URL", "https://api.deepseek.com/chat/completions"
)
DEEPSEEK_MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")
DEEPSEEK_TIMEOUT_S = _int_from_env("DEEPSEEK_TIMEOUT", 20)
DEEPSEEK_MAX_TOKENS = _int_from_env("DEEPSEEK_MAX_TOKENS", 320)


def deepseek_api_key() -> str:
    """Read the DeepSeek key at call time so tests can patch the environment."""
    return os.environ.get("DEEPSEEK_API_KEY", "").strip()


def boltz_api_key() -> str:
    return os.environ.get("BOLTZ_API_KEY", "").strip()


def ensure_directories() -> None:
    """Create the writable directories the application needs."""
    for directory in (DATA_DIR, RECEPTOR_CACHE_DIR, BENCHMARKS_DIR, DATASET_DIR):
        directory.mkdir(parents=True, exist_ok=True)
