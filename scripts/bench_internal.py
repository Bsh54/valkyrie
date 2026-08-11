"""Internal validation on registry targets.

Produces data/benchmarks/internal.json: redocking RMSD, reproducibility spread,
positive/negative controls, and enrichment (AUC + EF) for Vina and consensus.

Usage:
    python scripts/bench_internal.py [--target pf-dhfr] [--exhaustiveness 8]
                                     [--repeats 5] [--output PATH]
"""

import argparse
import json
import statistics
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from rdkit import RDLogger

from drugforge.benchmarks import compute_auc, compute_ef, compute_rmsd
from drugforge.config import BENCHMARK_SETS_DIR, BENCHMARKS_DIR
from drugforge.consensus import compute_consensus
from drugforge.docking import dock
from drugforge.ligand_prep import prepare_ligand
from drugforge.molblock import build_mol_from_atoms
from drugforge.pdb_ligand import pick_primary_ligand
from drugforge.receptor import get_receptor_pdbqt
from drugforge.rescoring import rescore_vinardo
from drugforge.targets import get_target

RDLogger.DisableLog("rdApp.*")


def _dock_smiles(smiles, target, receptor, exhaustiveness):
    _, ligand_pdbqt = prepare_ligand(smiles)
    result = dock(
        ligand_pdbqt=ligand_pdbqt,
        receptor_pdbqt_path=receptor,
        box=target.box,
        exhaustiveness=exhaustiveness,
        template_smiles=smiles,
    )
    vinardo = rescore_vinardo(result.best_pose_pdbqt, receptor, target.box)
    return result, vinardo


def redocking(target, receptor, exhaustiveness):
    pdb_path = receptor.parent / f"{target.pdb_id}.pdb"
    if not pdb_path.exists():
        return {"evaluated": 0, "skipped": 1,
                "results": [{"pdb_id": target.pdb_id, "status": "skipped",
                             "reason": "pdb_not_cached"}],
                "success_rate_under_2A": None}

    picked = pick_primary_ligand(pdb_path.read_text(encoding="utf-8"))
    if picked is None:
        return {"evaluated": 0, "skipped": 1,
                "results": [{"pdb_id": target.pdb_id, "status": "skipped",
                             "reason": "no_suitable_ligand"}],
                "success_rate_under_2A": None}

    res_name, atoms = picked
    crystal = build_mol_from_atoms(atoms)
    if crystal is None:
        return {"evaluated": 0, "skipped": 1,
                "results": [{"pdb_id": target.pdb_id, "status": "skipped",
                             "reason": "ligand_rebuild_failed"}],
                "success_rate_under_2A": None}

    from rdkit import Chem

    try:
        docked, _ = _dock_smiles(target.reference.smiles, target, receptor, exhaustiveness)
        pose = Chem.MolFromMolBlock(docked.best_pose_sdf, sanitize=False)
        rmsd = compute_rmsd(pose, crystal)
    except Exception as e:
        return {"evaluated": 0, "skipped": 1,
                "results": [{"pdb_id": target.pdb_id, "status": "skipped",
                             "reason": f"docking_failed: {type(e).__name__}"}],
                "success_rate_under_2A": None}

    if rmsd is None:
        return {"evaluated": 0, "skipped": 1,
                "results": [{"pdb_id": target.pdb_id, "status": "skipped",
                             "reason": "rmsd_atom_mismatch",
                             "ligand_residue": res_name}],
                "success_rate_under_2A": None}

    return {
        "evaluated": 1, "skipped": 0,
        "results": [{"pdb_id": target.pdb_id, "ligand_residue": res_name,
                     "rmsd": rmsd, "status": "ok"}],
        "success_rate_under_2A": 1.0 if rmsd < 2.0 else 0.0,
        "note": "Ligand rebuilt from PDB coordinates without CONECT records; "
                "bond orders are inferred.",
    }


def reproducibility(target, receptor, exhaustiveness, repeats):
    scores = []
    for _ in range(repeats):
        result, _ = _dock_smiles(target.reference.smiles, target, receptor, exhaustiveness)
        scores.append(result.best_affinity)
    return {
        "n": repeats,
        "exhaustiveness": exhaustiveness,
        "scores": scores,
        "mean": round(statistics.fmean(scores), 3),
        "std": round(statistics.pstdev(scores), 3) if repeats > 1 else 0.0,
        "spread": round(max(scores) - min(scores), 3),
    }


def controls(target, receptor, exhaustiveness):
    negatives = {"glucose": "OCC1OC(O)C(O)C(O)C1O", "ethanol": "CCO"}
    reference, _ = _dock_smiles(target.reference.smiles, target, receptor, exhaustiveness)

    results = []
    for name, smiles in negatives.items():
        try:
            docked, _ = _dock_smiles(smiles, target, receptor, exhaustiveness)
            results.append({"name": name, "vina": docked.best_affinity})
        except Exception as e:
            results.append({"name": name, "status": "skipped",
                            "reason": type(e).__name__})

    scored = [r["vina"] for r in results if "vina" in r]
    return {
        "reference": {"name": target.reference.name, "vina": reference.best_affinity},
        "negatives": results,
        "ordering_held": all(reference.best_affinity < v for v in scored) if scored else None,
    }


def enrichment(target, receptor, exhaustiveness):
    set_path = BENCHMARK_SETS_DIR / f"{target.id}_chembl.json"
    if not set_path.exists():
        return {"status": "not_run", "reason": "benchmark_set_missing"}

    data = json.loads(set_path.read_text(encoding="utf-8"))
    reference, ref_vinardo = _dock_smiles(
        target.reference.smiles, target, receptor, exhaustiveness
    )

    rows, skipped = [], []
    for group, is_active in (("actives", True), ("inactives", False)):
        for entry in data.get(group, []):
            try:
                docked, vinardo = _dock_smiles(
                    entry["smiles"], target, receptor, exhaustiveness
                )
                consensus = compute_consensus(
                    docked.best_affinity, vinardo,
                    reference.best_affinity, ref_vinardo,
                ).consensus_score
                rows.append({"name": entry["name"], "is_active": is_active,
                             "vina": docked.best_affinity, "consensus": consensus})
            except Exception as e:
                skipped.append({"name": entry["name"], "group": group,
                                "reason": type(e).__name__})

    if not rows:
        return {"status": "not_run", "reason": "all_compounds_skipped",
                "skipped": skipped}

    act_vina = [r["vina"] for r in rows if r["is_active"]]
    inact_vina = [r["vina"] for r in rows if not r["is_active"]]
    # Consensus is a ratio where higher means stronger binding, so negate it to
    # keep the shared "lower is better" convention of the metric helpers.
    act_cons = [-r["consensus"] for r in rows if r["is_active"]]
    inact_cons = [-r["consensus"] for r in rows if not r["is_active"]]

    vina_pairs = [(r["vina"], r["is_active"]) for r in rows]
    cons_pairs = [(-r["consensus"], r["is_active"]) for r in rows]

    vina_auc = compute_auc(act_vina, inact_vina)
    cons_auc = compute_auc(act_cons, inact_cons)

    return {
        "status": "available",
        "n_actives": len(act_vina),
        "n_inactives": len(inact_vina),
        "skipped": skipped,
        "vina": {"auc": vina_auc,
                 "ef1": compute_ef(vina_pairs, 0.01),
                 "ef10": compute_ef(vina_pairs, 0.10)},
        "consensus": {"auc": cons_auc,
                      "ef1": compute_ef(cons_pairs, 0.01),
                      "ef10": compute_ef(cons_pairs, 0.10)},
        "consensus_improves": (
            None if vina_auc is None or cons_auc is None else cons_auc > vina_auc
        ),
        "inactives_note": data.get("note", ""),
        "rows": rows,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", default="pf-dhfr")
    parser.add_argument("--exhaustiveness", type=int, default=8)
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--output", default=None)
    args = parser.parse_args()

    target = get_target(args.target)
    receptor = get_receptor_pdbqt(target)

    print(f"target={target.id} exhaustiveness={args.exhaustiveness}")
    print("redocking...")
    redock = redocking(target, receptor, args.exhaustiveness)
    print("reproducibility...")
    repro = reproducibility(target, receptor, args.exhaustiveness, args.repeats)
    print("controls...")
    ctrl = controls(target, receptor, args.exhaustiveness)
    print("enrichment...")
    enrich = enrichment(target, receptor, args.exhaustiveness)

    try:
        import vina
        vina_version = getattr(vina, "__version__", "unknown")
    except Exception:
        vina_version = "unknown"

    artifact = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "target_id": target.id,
        "target_name": target.name,
        "pdb_id": target.pdb_id,
        "reference_drug": target.reference.name,
        "config": {"exhaustiveness": args.exhaustiveness, "vina_version": vina_version},
        "redocking": redock,
        "reproducibility": repro,
        "controls": ctrl,
        "enrichment": enrich,
    }

    output = Path(args.output) if args.output else BENCHMARKS_DIR / "internal.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(artifact, indent=2), encoding="utf-8")
    print(f"wrote {output}")


if __name__ == "__main__":
    main()
