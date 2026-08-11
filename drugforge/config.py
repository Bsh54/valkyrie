"""Application configuration and path constants."""

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

# Boltz-2 API configuration
BOLTZ_API_URL = "https://api.boltz.bio/v2/predict"
BOLTZ_API_TIMEOUT = 30  # seconds
BOLTZ_TOP_N = 3  # only send top-N candidates to Boltz

# Ensure directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
RECEPTOR_CACHE_DIR.mkdir(parents=True, exist_ok=True)
