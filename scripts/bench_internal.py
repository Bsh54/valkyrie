"""Internal validation on a registry target.

Writes data/benchmarks/internal.json with redocking RMSD, reproducibility spread,
positive and negative controls, and enrichment for both scoring functions.

    python scripts/bench_internal.py --target pf-dhfr --exhaustiveness 8
"""

from __future__ import annotations

import argparse
import json
import statistics
from datetime import datetime, timezone
from pathlib import Path

from rdkit import Chem, RDLogger

from drugforge.analytics.benchmarks import (
    RMSD_SUCCESS_THRESHOLD,
    compute_auc,
    compute_enrichment_factor,
    compute_rmsd,
)
from drugforge.chem.crystal import find_primary_ligand
from drugforge.chem.ligand import prepare_ligand
from drugforge.chem.molblock import build_mol_from_atoms
from drugforge.chem.receptor import get_receptor_pdbqt
from drugforge.config import BENCHMARK_SETS_DIR, BENCHMARKS_DIR
from drugforge.docking.consensus import compute_consensus
from drugforge.docking.engine import dock
from drugforge.docking.rescoring import rescore_vinardo
from drugforge.domain.targets import get_target

RDLogger.DisableLog("rdApp.*")

NEGATIVE_CONTROLS = {
    "glucose": "OCC1OC(O)C(O)C(O)C1O",
    "ethanol": "CCO",
}


def score(smiles: str, target, receptor: Path, exhaustiveness: int):
    """Dock and rescore one molecule."""
    _, ligand_pdbqt = prepare_ligand(smiles)
    docked = dock(
        ligand_pdbqt=ligand_pdbqt,
        receptor_pdbqt_path=receptor,
        box=target.box,
        exhaustiveness=exhaustiveness,
        template_smiles=smiles,
    )
    vinardo = rescore_vinardo(docked.best_pose_pdbqt, receptor, target.box)
    return docked, vinardo


def _skipped(pdb_id: str, reason: str) -> dict:
    return {
        "evaluated": 0,
        "skipped": 1,
        "results": [{"pdb_id": pdb_id, "status": "skipped", "reason": reason}],
        "success_rate_under_threshold": None,
    }


def measure_redocking(target, receptor: Path, exhaustiveness: int) -> dict:
    """Redock the crystal ligand and compare with its experimental pose."""
    pdb_path = receptor.parent / f"{target.pdb_id}.pdb"
    if not pdb_path.exists():
        return _skipped(target.pdb_id, "structure_not_cached")

    found = find_primary_ligand(pdb_path.read_text(encoding="utf-8"))
    if found is None:
        return _skipped(target.pdb_id, "no_suitable_ligand")

    residue, atoms = found
    crystal = build_mol_from_atoms(atoms)
    if crystal is None:
        return _skipped(target.pdb_id, "ligand_rebuild_failed")

    try:
        docked, _ = score(target.reference.smiles, target, receptor, exhaustiveness)
    except Exception as exc:
        return _skipped(target.pdb_id, f"docking_failed: {type(exc).__name__}")

    pose = Chem.MolFromMolBlock(docked.best_pose_sdf, sanitize=False)
    rmsd = compute_rmsd(pose, crystal)
    if rmsd is None:
        return _skipped(target.pdb_id, "rmsd_atom_mismatch")

    return {
        "evaluated": 1,
        "skipped": 0,
        "results": [
            {
                "pdb_id": target.pdb_id,
                "ligand_residue": residue,
                "rmsd": rmsd,
                "status": "ok",
            }
        ],
        "success_rate_under_threshold": 1.0 if rmsd < RMSD_SUCCESS_THRESHOLD else 0.0,
        "threshold_angstrom": RMSD_SUCCESS_THRESHOLD,
        "note": (
            "The crystal ligand is rebuilt from coordinates without CONECT "
            "records, so its bond orders are inferred."
        ),
    }


def measure_reproducibility(target, receptor: Path, exhaustiveness: int, repeats: int) -> dict:
    """Repeat one docking to expose run-to-run variation."""
    scores = [
        score(target.reference.smiles, target, receptor, exhaustiveness)[0].best_affinity
        for _ in range(repeats)
    ]
    return {
        "n": repeats,
        "exhaustiveness": exhaustiveness,
        "scores": scores,
        "mean": round(statistics.fmean(scores), 3),
        "std": round(statistics.pstdev(scores), 3) if repeats > 1 else 0.0,
        "spread": round(max(scores) - min(scores), 3),
        "note": "Seeds are not fixed, so this measures genuine search variability.",
    }


def measure_controls(target, receptor: Path, exhaustiveness: int) -> dict:
    """Check the reference drug beats biologically inert molecules."""
    reference, _ = score(target.reference.smiles, target, receptor, exhaustiveness)

    negatives = []
    for name, smiles in NEGATIVE_CONTROLS.items():
        try:
            docked, _ = score(smiles, target, receptor, exhaustiveness)
            negatives.append({"name": name, "vina": docked.best_affinity})
        except Exception as exc:
            negatives.append(
                {"name": name, "status": "skipped", "reason": type(exc).__name__}
            )

    scored = [entry["vina"] for entry in negatives if "vina" in entry]
    return {
        "reference": {"name": target.reference.name, "vina": reference.best_affinity},
        "negatives": negatives,
        "ordering_held": (
            all(reference.best_affinity < value for value in scored) if scored else None
        ),
    }


def measure_enrichment(target, receptor: Path, exhaustiveness: int) -> dict:
    """Rank a known actives and inactives set with both scoring functions."""
    set_path = BENCHMARK_SETS_DIR / f"{target.id}_chembl.json"
    if not set_path.exists():
        return {"status": "not_run", "reason": "benchmark_set_missing"}

    data = json.loads(set_path.read_text(encoding="utf-8"))
    reference, reference_vinardo = score(
        target.reference.smiles, target, receptor, exhaustiveness
    )

    rows, skipped = [], []
    for group, is_active in (("actives", True), ("inactives", False)):
        for entry in data.get(group, []):
            try:
                docked, vinardo = score(entry["smiles"], target, receptor, exhaustiveness)
            except Exception as exc:
                skipped.append(
                    {"name": entry["name"], "group": group, "reason": type(exc).__name__}
                )
                continue

            consensus = compute_consensus(
                docked.best_affinity,
                vinardo,
                reference.best_affinity,
                reference_vinardo,
            ).consensus_score
            rows.append(
                {
                    "name": entry["name"],
                    "is_active": is_active,
                    "vina": docked.best_affinity,
                    "consensus": consensus,
                }
            )

    if not rows:
        return {"status": "not_run", "reason": "all_compounds_skipped", "skipped": skipped}

    # Consensus rises with stronger binding, so it is negated to share the
    # "lower is better" convention the metric helpers expect.
    vina_pairs = [(row["vina"], row["is_active"]) for row in rows]
    consensus_pairs = [(-row["consensus"], row["is_active"]) for row in rows]

    vina_auc = compute_auc(
        [row["vina"] for row in rows if row["is_active"]],
        [row["vina"] for row in rows if not row["is_active"]],
    )
    consensus_auc = compute_auc(
        [-row["consensus"] for row in rows if row["is_active"]],
        [-row["consensus"] for row in rows if not row["is_active"]],
    )

    return {
        "status": "available",
        "n_actives": sum(1 for row in rows if row["is_active"]),
        "n_inactives": sum(1 for row in rows if not row["is_active"]),
        "skipped": skipped,
        "vina": {
            "auc": vina_auc,
            "ef1": compute_enrichment_factor(vina_pairs, 0.01),
            "ef10": compute_enrichment_factor(vina_pairs, 0.10),
        },
        "consensus": {
            "auc": consensus_auc,
            "ef1": compute_enrichment_factor(consensus_pairs, 0.01),
            "ef10": compute_enrichment_factor(consensus_pairs, 0.10),
        },
        "consensus_improves": (
            None
            if vina_auc is None or consensus_auc is None
            else consensus_auc > vina_auc
        ),
        "inactives_note": data.get("note", ""),
        "rows": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", default="pf-dhfr")
    parser.add_argument("--exhaustiveness", type=int, default=8)
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    target = get_target(args.target)
    receptor = get_receptor_pdbqt(target)

    print(f"target {target.id}, exhaustiveness {args.exhaustiveness}")
    print("redocking")
    redocking = measure_redocking(target, receptor, args.exhaustiveness)
    print("reproducibility")
    reproducibility = measure_reproducibility(
        target, receptor, args.exhaustiveness, args.repeats
    )
    print("controls")
    controls = measure_controls(target, receptor, args.exhaustiveness)
    print("enrichment")
    enrichment = measure_enrichment(target, receptor, args.exhaustiveness)

    try:
        import vina

        vina_version = getattr(vina, "__version__", "unknown")
    except ImportError:
        vina_version = "unknown"

    artifact = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "target_id": target.id,
        "target_name": target.name,
        "pdb_id": target.pdb_id,
        "reference_drug": target.reference.name,
        "config": {"exhaustiveness": args.exhaustiveness, "vina_version": vina_version},
        "redocking": redocking,
        "reproducibility": reproducibility,
        "controls": controls,
        "enrichment": enrichment,
    }

    output = args.output or BENCHMARKS_DIR / "internal.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(artifact, indent=2), encoding="utf-8")
    print(f"wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
