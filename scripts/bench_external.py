"""Independent redocking benchmark over a fixed third-party complex list.

Writes data/benchmarks/external.json. Complexes that cannot be processed are
recorded as skipped with a reason; none is dropped, and success rates are always
published beside their denominator.

This is the expensive job. Prefer a Colab runtime over a small server:

    python scripts/bench_external.py --limit 5      # smoke test
    python scripts/bench_external.py                # full set
"""

from __future__ import annotations

import argparse
import json
import statistics
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import requests
from rdkit import Chem, RDLogger

from drugforge.analytics.benchmarks import RMSD_SUCCESS_THRESHOLD, compute_rmsd
from drugforge.chem.crystal import centroid, find_primary_ligand
from drugforge.chem.ligand import prepare_ligand
from drugforge.chem.molblock import build_mol_from_atoms
from drugforge.chem.receptor import prepare_receptor
from drugforge.config import (
    BENCHMARK_SETS_DIR,
    BENCHMARKS_DIR,
    HTTP_TIMEOUT_S,
    RCSB_DOWNLOAD_URL,
    RECEPTOR_CACHE_DIR,
)
from drugforge.domain.models import DockingBox
from drugforge.docking.engine import dock

RDLogger.DisableLog("rdApp.*")

BOX_SIZE_ANGSTROM = 20.0


def fetch_structure(pdb_id: str) -> Path:
    cache_dir = RECEPTOR_CACHE_DIR / pdb_id
    cache_dir.mkdir(parents=True, exist_ok=True)
    pdb_path = cache_dir / f"{pdb_id}.pdb"

    if not pdb_path.exists():
        response = requests.get(
            RCSB_DOWNLOAD_URL.format(pdb_id=pdb_id), timeout=HTTP_TIMEOUT_S * 4
        )
        response.raise_for_status()
        pdb_path.write_text(response.text, encoding="utf-8")
    return pdb_path


def skipped(pdb_id: str, reason: str) -> dict:
    return {"pdb_id": pdb_id, "status": "skipped", "reason": reason}


def evaluate(pdb_id: str, exhaustiveness: int) -> dict:
    """Redock one complex and measure the deviation from its crystal pose."""
    try:
        pdb_path = fetch_structure(pdb_id)
    except requests.RequestException:
        return skipped(pdb_id, "download_failed")

    found = find_primary_ligand(pdb_path.read_text(encoding="utf-8"))
    if found is None:
        return skipped(pdb_id, "no_suitable_ligand")

    residue, atoms = found
    crystal = build_mol_from_atoms(atoms)
    if crystal is None:
        return skipped(pdb_id, "ligand_rebuild_failed")

    try:
        smiles = Chem.MolToSmiles(crystal)
        if not smiles:
            return skipped(pdb_id, "ligand_rebuild_failed")
        _, ligand_pdbqt = prepare_ligand(smiles)
    except Exception:
        return skipped(pdb_id, "ligand_rebuild_failed")

    receptor_path = pdb_path.parent / f"{pdb_id}_receptor.pdbqt"
    try:
        if not receptor_path.exists():
            prepare_receptor(pdb_path, receptor_path)
    except Exception:
        return skipped(pdb_id, "receptor_prep_failed")

    x, y, z = centroid(atoms)
    box = DockingBox(x, y, z, BOX_SIZE_ANGSTROM, BOX_SIZE_ANGSTROM, BOX_SIZE_ANGSTROM)

    try:
        docked = dock(
            ligand_pdbqt=ligand_pdbqt,
            receptor_pdbqt_path=receptor_path,
            box=box,
            exhaustiveness=exhaustiveness,
            template_smiles=smiles,
        )
    except Exception:
        return skipped(pdb_id, "docking_failed")

    pose = Chem.MolFromMolBlock(docked.best_pose_sdf, sanitize=False)
    rmsd = compute_rmsd(pose, crystal)
    if rmsd is None:
        return skipped(pdb_id, "rmsd_atom_mismatch")

    return {
        "pdb_id": pdb_id,
        "ligand_residue": residue,
        "vina": docked.best_affinity,
        "rmsd": rmsd,
        "status": "ok",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--exhaustiveness", type=int, default=8)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    spec = json.loads(
        (BENCHMARK_SETS_DIR / "external_complexes.json").read_text(encoding="utf-8")
    )
    pdb_ids = spec["pdb_ids"][: args.limit] if args.limit else spec["pdb_ids"]

    results = []
    for index, pdb_id in enumerate(pdb_ids, start=1):
        entry = evaluate(pdb_id, args.exhaustiveness)
        results.append(entry)
        detail = entry.get("rmsd", entry.get("reason", ""))
        print(f"[{index}/{len(pdb_ids)}] {pdb_id} {entry['status']} {detail}", flush=True)

    evaluated = [entry for entry in results if entry["status"] == "ok"]
    skips = [entry for entry in results if entry["status"] == "skipped"]
    rmsds = [entry["rmsd"] for entry in evaluated]

    artifact = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "set_name": spec.get("name"),
        "citation": spec.get("citation"),
        "selection_rule": (
            "Fixed third-party complex list committed before the run. No complex "
            "was added or removed after results were seen. See "
            "data/benchmark_sets/external_selection.md"
        ),
        "config": {
            "exhaustiveness": args.exhaustiveness,
            "box_size_angstrom": BOX_SIZE_ANGSTROM,
        },
        "attempted": len(results),
        "evaluated": len(evaluated),
        "skipped": len(skips),
        "skip_reasons": dict(Counter(entry["reason"] for entry in skips)),
        "threshold_angstrom": RMSD_SUCCESS_THRESHOLD,
        "success_rate_under_threshold": (
            round(sum(1 for v in rmsds if v < RMSD_SUCCESS_THRESHOLD) / len(rmsds), 3)
            if rmsds
            else None
        ),
        "median_rmsd": round(statistics.median(rmsds), 3) if rmsds else None,
        "mean_rmsd": round(statistics.fmean(rmsds), 3) if rmsds else None,
        "denominator_note": (
            "Rates are computed over evaluated complexes only. Skipped complexes "
            "are reported separately and are never hidden."
        ),
        "results": results,
    }

    output = args.output or BENCHMARKS_DIR / "external.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(artifact, indent=2), encoding="utf-8")

    print(f"\nattempted {len(results)}, evaluated {len(evaluated)}, skipped {len(skips)}")
    print(f"skip reasons: {artifact['skip_reasons']}")
    print(f"wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
