"""Application configuration and path constants."""

import os
from pathlib import Path

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
RECEPTOR_CACHE_DIR = DATA_DIR / "receptors"
DB_PATH = DATA_DIR / "results.db"
COMPOUNDS_PATH = DATA_DIR / "compounds.json"
STATIC_DIR = BASE_DIR / "static"

# Docking defaults
DEFAULT_EXHAUSTIVENESS = 8
MIN_EXHAUSTIVENESS = 1
MAX_EXHAUSTIVENESS = 32
DOCKING_TIMEOUT_S = 300
N_POSES = 5

# Cores Vina may use per docking. Bounded so a request cannot saturate a small
# host; override with DRUGFORGE_VINA_CPU.
VINA_CPU = int(os.environ.get("DRUGFORGE_VINA_CPU", "2"))

# Boltz-2 API configuration
BOLTZ_API_URL = "https://api.boltz.bio/v2/predict"
BOLTZ_API_TIMEOUT = 30  # seconds
BOLTZ_TOP_N = 3  # only send top-N candidates to Boltz

# DeepSeek API configuration (AI explainer)
DEEPSEEK_API_URL = "https://api.deepseek.com/chat/completions"
DEEPSEEK_MODEL = "deepseek-chat"
DEEPSEEK_TIMEOUT = 15  # seconds

# Disease fact sheets directory
DISEASE_FACTS_DIR = DATA_DIR / "disease_facts"

# Benchmark artifacts and input sets
BENCHMARKS_DIR = DATA_DIR / "benchmarks"
BENCHMARK_SETS_DIR = DATA_DIR / "benchmark_sets"
DATASET_DIR = DATA_DIR / "dataset"

# Ensure directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
RECEPTOR_CACHE_DIR.mkdir(parents=True, exist_ok=True)
