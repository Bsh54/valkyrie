# DrugForge

An online molecular-docking laboratory for neglected tropical diseases: malaria,
Chagas disease, leishmaniasis and sleeping sickness.

You submit a molecule by common name or SMILES. It is docked in real time against
a validated disease protein target with AutoDock Vina, rescored, filtered, and
reported next to the target's reference drug.

**DrugForge prioritises candidate molecules. It does not discover or prove drugs,
and it never gives clinical advice.** Every number it produces is an in-silico
prediction that requires laboratory validation. Docking is the first step of many.

## What it does

The screening funnel is identical for every target:

| Stage | Tool | Runs on |
|---|---|---|
| Resolve name or SMILES | Local registry, then PubChem | CPU |
| Prepare ligand | RDKit ETKDGv3 + MMFF, Meeko, pH 7.4 | CPU |
| Prepare receptor | RCSB download, cofactors kept, Open Babel, pH 7.4 | CPU |
| Dock | AutoDock Vina | CPU |
| Rescore | Vinardo on the same pose | CPU |
| Consensus | Weighted, reference-normalised | CPU |
| Drug-likeness | Lipinski, Veber | CPU |
| ADMET and toxicity | PAINS, Brenk, NIH, ESOL | CPU |
| Compare to reference | Every metric, with deltas | CPU |
| Explanation | DeepSeek, grounded in the computed data and the plant's traditional use | remote |

The explanation stage is optional. Without an API key it reports its status and the
physics-based result is returned unchanged.

## Requirements

- Python 3.10 to 3.12. RDKit and the Vina bindings have no 3.13 wheels yet.
- Open Babel, for receptor preparation.

```bash
# Debian or Ubuntu
sudo apt install openbabel

# macOS
brew install open-babel
```

## Install

```bash
git clone <repository-url> drugforge
cd drugforge

python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install -e ".[dev]"
```

## Use

```bash
# List available targets
drugforge targets

# Screen a molecule against Plasmodium falciparum DHFR
drugforge screen artemisinin --target pf-dhfr

# Faster, less thorough search, useful while developing
drugforge screen cryptolepine --exhaustiveness 4

# Full result as JSON
drugforge screen "Nc1nc(N)c(-c2ccc(Cl)cc2)cn1" --json

# Serve the web interface at http://127.0.0.1:8100
drugforge serve
```

A screening run takes roughly one to two minutes on four cores. The first run for
a target also downloads and prepares its structure, and docks the reference drug.

## Configuration

Copy `.env.example` to `.env` and fill in what you need. Nothing is required: the
application runs without any API key.

| Variable | Default | Purpose |
|---|---|---|
| `DEEPSEEK_API_KEY` | unset | Enables the plain-language explanation (DeepSeek, ~free for the hackathon: 5M-token grant for a new account; the app runs fine without it) |
| `DRUGFORGE_VINA_CPU` | `2` | Cores per docking run |
| `DRUGFORGE_DATA_DIR` | `./data` | Writable data directory |
| `DRUGFORGE_DB_PATH` | `<data>/results.db` | SQLite database |

`DRUGFORGE_VINA_CPU` matters on small hosts: Vina otherwise uses every available
core, so one request can saturate the machine.

## Tests

```bash
pytest -m "not slow"    # fast suite, no docking engine
pytest                  # everything, including real Vina runs
```

Slow tests execute AutoDock Vina and take several minutes. The fast suite stubs
the engine and needs no network access or API keys.

## Architecture

```
src/drugforge/
├── domain/      models and the target registry, no I/O
├── chem/        resolution, preparation, descriptors, ADMET
├── docking/     Vina execution, rescoring, consensus
├── ai/          hosted services, always degradable
├── pipeline/    stage orchestration, reference comparison
├── storage/     SQLite schema and repository
├── analytics/   benchmark metrics
├── reporting/   PDF export
└── web/         FastAPI routers
```

Dependencies point inward. `domain` imports nothing from the other layers, and
`web` only handles transport. A new disease is one `Target` entry in
`domain/targets.py`; the pipeline is unchanged.

## The compound library

`data/ethnobotanical.json` links African medicinal-plant knowledge to specific
molecules. Each entry records the plant's scientific and local name, the disease
it is traditionally used for, the region and people, the preparation method, the
active compound, and a literature citation.

The intent is to bridge traditional knowledge to in-silico molecular validation,
with the source of every claim visible. A prediction is not a validation.

## Licence

Code under Apache-2.0. The ethnobotanical dataset is intended for release under
CC-BY-4.0 with full attribution.
