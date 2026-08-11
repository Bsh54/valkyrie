"""Persistence, including migration of a legacy database."""

import sqlite3

from drugforge.domain.models import Explanation
from drugforge.storage import repository
from drugforge.storage.database import connect


def test_round_trip_preserves_values(screening_result):
    result_id = repository.save(screening_result)
    stored = repository.get(result_id)

    assert stored is not None
    assert stored["molecule_smiles"] == "CCO"
    assert stored["affinity_kcal_mol"] == -8.123
    assert stored["consensus_score"] == 1.03
    assert stored["verdict"] == "Promising"
    assert stored["is_hit"] is True
    assert stored["comparisons"][0]["metric"] == "affinity"


def test_explanation_is_persisted(screening_result):
    screening_result.explanation = Explanation(text="Grounded text.", status="success")
    stored = repository.get(repository.save(screening_result))

    assert stored["explanation"]["status"] == "success"
    assert stored["explanation"]["text"] == "Grounded text."


def test_absent_optional_stages_round_trip_as_none(screening_result):
    stored = repository.get(repository.save(screening_result))
    assert stored["boltz"] is None
    assert stored["explanation"] is None


def test_unknown_identifier_returns_none():
    assert repository.get("no-such-result") is None


def test_identifiers_are_unique(screening_result):
    first = repository.save(screening_result)
    screening_result.result_id = None
    second = repository.save(screening_result)
    assert first != second


def test_latest_result_wins(screening_result):
    screening_result.timestamp = "2026-01-01T00:00:00+00:00"
    repository.save(screening_result)

    screening_result.result_id = None
    screening_result.timestamp = "2026-06-01T00:00:00+00:00"
    screening_result.verdict = "Weak"
    repository.save(screening_result)

    latest = repository.latest_for("CCO", "pf-dhfr")
    assert latest["verdict"] == "Weak"


def test_stored_results_carry_a_disclaimer(screening_result):
    stored = repository.get(repository.save(screening_result))
    assert "in-silico" in stored["disclaimer"].lower()


def test_legacy_table_and_columns_are_migrated(tmp_path, monkeypatch):
    """A database from an earlier release must keep working after upgrade."""
    db_path = tmp_path / "legacy.db"
    monkeypatch.setattr("drugforge.storage.database.DB_PATH", db_path)

    legacy = sqlite3.connect(str(db_path))
    legacy.execute(
        "CREATE TABLE docking_results ("
        "id TEXT PRIMARY KEY, timestamp TEXT NOT NULL, "
        "molecule_smiles TEXT NOT NULL, target_id TEXT NOT NULL, "
        "affinity REAL NOT NULL, pose_sdf TEXT, pose_pdbqt TEXT, "
        "drug_likeness_json TEXT, comparison_json TEXT, verdict TEXT)"
    )
    legacy.execute(
        "INSERT INTO docking_results VALUES "
        "('old-1', '2026-01-01T00:00:00+00:00', 'CCO', 'pf-dhfr', -5.5, "
        "'', '', '{}', '[]', 'Weak')"
    )
    legacy.commit()
    legacy.close()

    with connect() as connection:
        columns = {
            row["name"] for row in connection.execute("PRAGMA table_info(screening_results)")
        }

    assert "explanation_json" in columns
    assert "consensus_score" in columns

    migrated = repository.get("old-1")
    assert migrated is not None
    assert migrated["verdict"] == "Weak"
    assert migrated["explanation"] is None
