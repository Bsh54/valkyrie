"""External independent redocking benchmark.

Runs the fixed complex list in data/benchmark_sets/external_complexes.json and
writes data/benchmarks/external.json. Complexes that cannot be processed are
recorded as skipped with a reason; none is dropped.

This is the heavy job. Prefer running it on Colab (see notebooks/) and uploading
the artifact, rather than on a small VPS.

Usage:
    python scripts/bench_external.py [--limit N] [--exhaustiveness 8] [--output PATH]
"""

import argparse
import json
import statistics
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import requests
from rdkit import Chem, RDLogger

from drugforge.benchmarks import compute_rmsd
from drugforge.config import BENCHMARK_SETS_DIR, BENCHMARKS_DIR, RECEPTOR_CACHE_DIR
from drugforge.docking import dock
from drugforge.ligand_prep import prepare_ligand
from drugforge.molblock import build_mol_from_atoms
from drugforge.pdb_ligand import centroid, pick_primary_ligand
from drugforge.receptor import _prepare_receptor_pdbqt
from drugforge.targets import DockingBox

RDLogger.DisableLog("rdApp.*")

BOX_SIZE = 20.0


def _download_pdb(pdb_id: str) -> Path:
    cache_dir = RECEPTOR_CACHE_DIR / pdb_id
    cache_dir.mkdir(parents=True, exist_ok=True)
    pdb_path = cache_dir / f"{pdb_id}.pdb"
    if not pdb_path.exists():
        resp = requests.get(f"https://files.rcsb.org/download/{pdb_id}.pdb", timeout=60)
        resp.raise_for_status()
        pdb_path.write_text(resp.text, encoding="utf-8")
    return pdb_path


def _skip(pdb_id: str, reason: str) -> dict:
    return {"pdb_id": pdb_id, "status": "skipped", "reason": reason}


def evaluate(pdb_id: str, exhaustiveness: int) -> dict:
    try:
        pdb_path = _download_pdb(pdb_id)
    except Exception:
        return _skip(pdb_id, "download_failed")

    pdb_text = pdb_path.read_text(encoding="utf-8")
    picked = pick_primary_ligand(pdb_text)
    if picked is None:
        return _skip(pdb_id, "no_suitable_ligand")

    res_name, atoms = picked
    crystal = build_mol_from_atoms(atoms)
    if crystal is None:
        return _skip(pdb_id, "ligand_rebuild_failed")

    try:
        smiles = Chem.MolToSmiles(crystal)
        if not smiles:
            return _skip(pdb_id, "ligand_rebuild_failed")
        _, ligand_pdbqt = prepare_ligand(smiles)
    except Exception:
        return _skip(pdb_id, "ligand_rebuild_failed")

    receptor_path = pdb_path.parent / f"{pdb_id}_receptor.pdbqt"
    try:
        if not receptor_path.exists():
            _prepare_receptor_pdbqt(pdb_path, receptor_path)
    except Exception:
        return _skip(pdb_id, "receptor_prep_failed")

    cx, cy, cz = centroid(atoms)
    box = DockingBox(cx, cy, cz, BOX_SIZE, BOX_SIZE, BOX_SIZE)

    try:
        result = dock(
            ligand_pdbqt=ligand_pdbqt,
            receptor_pdbqt_path=receptor_path,
            box=box,
            exhaustiveness=exhaustiveness,
            template_smiles=smiles,
        )
    except Exception:
        return _skip(pdb_id, "docking_failed")

    pose = Chem.MolFromMolBlock(result.best_pose_sdf, sanitize=False)
    rmsd = compute_rmsd(pose, crystal)
    if rmsd is None:
        return _skip(pdb_id, "rmsd_atom_mismatch")

    return {
        "pdb_id": pdb_id,
        "ligand_residue": res_name,
        "vina": result.best_affinity,
        "rmsd": rmsd,
        "status": "ok",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--exhaustiveness", type=int, default=8)
    parser.add_argument("--output", default=None)
    args = parser.parse_args()

    spec = json.loads(
        (BENCHMARK_SETS_DIR / "external_complexes.json").read_text(encoding="utf-8")
    )
    pdb_ids = spec["pdb_ids"][: args.limit] if args.limit else spec["pdb_ids"]

    results = []
    for i, pdb_id in enumerate(pdb_ids, 1):
        entry = evaluate(pdb_id, args.exhaustiveness)
        results.append(entry)
        detail = entry.get("rmsd", entry.get("reason"))
        print(f"[{i}/{len(pdb_ids)}] {pdb_id} {entry['status']} {detail}", flush=True)

    evaluated = [r for r in results if r["status"] == "ok"]
    skipped = [r for r in results if r["status"] == "skipped"]
    rmsds = [r["rmsd"] for r in evaluated]

    breakdown: dict[str, int] = {}
    for r in skipped:
        breakdown[r["reason"]] = breakdown.get(r["reason"], 0) + 1

    artifact = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "set_name": spec.get("name"),
        "citation": spec.get("citation"),
        "selection_rule": (
            "Fixed third-party complex list committed before the run; no complex "
            "added or removed after results were seen. See "
            "data/benchmark_sets/external_selection.md"
        ),
        "config": {"exhaustiveness": args.exhaustiveness, "box_size_angstrom": BOX_SIZE},
        "attempted": len(results),
        "evaluated": len(evaluated),
        "skipped": len(skipped),
        "skip_reasons": breakdown,
        "success_rate_under_2A": (
            round(sum(1 for v in rmsds if v < 2.0) / len(rmsds), 3) if rmsds else None
        ),
        "median_rmsd": round(statistics.median(rmsds), 3) if rmsds else None,
        "mean_rmsd": round(statistics.fmean(rmsds), 3) if rmsds else None,
        "denominator_note": (
            "success_rate_under_2A and median_rmsd are computed over evaluated "
            "complexes only. Skipped complexes are listed separately."
        ),
        "results": results,
    }

    output = Path(args.output) if args.output else BENCHMARKS_DIR / "external.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(artifact, indent=2), encoding="utf-8")

    print(f"\nattempted={len(results)} evaluated={len(evaluated)} skipped={len(skipped)}")
    print(f"skip_reasons={breakdown}")
    print(f"wrote {output}")


if __name__ == "__main__":
    main()
