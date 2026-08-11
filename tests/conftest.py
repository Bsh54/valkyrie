"""Shared fixtures.

External services are disabled by default so no test can silently depend on a
network call or an API key present in the developer's environment.
"""

import pytest
from rdkit import Chem, RDLogger

from drugforge.domain.models import (
    ADMETResult,
    Comparison,
    DrugLikeness,
    ScreeningResult,
)

RDLogger.DisableLog("rdApp.*")

PYRIMETHAMINE_SMILES = "c1ccc(c(c1)Cl)c2cnc(nc2N)N"
CRYPTOLEPINE_SMILES = "Cn1c2ccccc2c2c1c1ccccc1[nH]2"


@pytest.fixture(autouse=True)
def no_external_services(monkeypatch):
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    monkeypatch.delenv("BOLTZ_API_KEY", raising=False)


@pytest.fixture(autouse=True)
def isolated_database(tmp_path, monkeypatch):
    monkeypatch.setattr("drugforge.storage.database.DB_PATH", tmp_path / "results.db")


@pytest.fixture
def clear_reference_cache():
    from drugforge.pipeline.comparison import clear_reference_cache

    clear_reference_cache()
    yield
    clear_reference_cache()


@pytest.fixture
def pyrimethamine():
    return Chem.AddHs(Chem.MolFromSmiles(PYRIMETHAMINE_SMILES))


@pytest.fixture
def drug_likeness():
    return DrugLikeness(
        molecular_weight=248.71,
        logp=1.94,
        hbd=2,
        hba=4,
        tpsa=77.82,
        rotatable_bonds=2,
        lipinski_violations=0,
    )


@pytest.fixture
def clean_admet():
    return ADMETResult(
        esol_logs=-2.8,
        gi_absorption="High",
        pains_alerts=[],
        brenk_alerts=[],
        nih_alerts=[],
        reactive_groups=[],
        passes_filter=True,
        failure_reasons=[],
    )


@pytest.fixture
def screening_result(drug_likeness, clean_admet):
    return ScreeningResult(
        molecule_smiles="CCO",
        target_id="pf-dhfr",
        affinity_kcal_mol=-8.123,
        vinardo_score=-7.2,
        consensus_score=1.03,
        all_affinities=[-8.123, -7.9],
        pose_sdf="mol block",
        pose_pdbqt="pdbqt block",
        drug_likeness=drug_likeness,
        admet=clean_admet,
        is_hit=True,
        hit_failure_reasons=[],
        comparisons=[
            Comparison(
                metric="affinity",
                molecule_value=-8.123,
                reference_value=-7.9,
                delta=-0.223,
                ratio=1.028,
                verdict="better",
            )
        ],
        verdict="Promising",
    )
