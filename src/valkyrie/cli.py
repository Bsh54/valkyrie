"""Command line interface."""

from __future__ import annotations

import argparse
import json
import logging
import sys

from valkyrie import __version__
from valkyrie.config import DEFAULT_EXHAUSTIVENESS
from valkyrie.domain.targets import list_targets
from valkyrie.errors import PipelineError


def _configure_logging(verbose: bool) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
    )


def _cmd_targets(_: argparse.Namespace) -> int:
    for target in list_targets():
        print(f"{target.id:12} {target.name:10} {target.disease:12} PDB {target.pdb_id}")
    return 0


def _cmd_screen(args: argparse.Namespace) -> int:
    from valkyrie.pipeline.runner import run_screening
    from valkyrie.storage import repository

    try:
        result = run_screening(
            molecule_input=args.molecule,
            target_id=args.target,
            exhaustiveness=args.exhaustiveness,
            with_explanation=not args.no_explanation,
        )
    except PipelineError as exc:
        print(f"failed at stage '{exc.stage}': {exc.cause.detail}", file=sys.stderr)
        return 1

    if not args.no_store:
        repository.save(result)

    payload = result.to_dict()
    if args.json:
        payload.pop("pose_pdbqt", None)
        print(json.dumps(payload, indent=2))
        return 0

    print(f"molecule    {result.molecule_smiles}")
    print(f"target      {result.target_id}")
    print(f"vina        {result.affinity_kcal_mol} kcal/mol")
    print(f"vinardo     {result.vinardo_score} kcal/mol")
    print(f"consensus   {result.consensus_score}")
    print(f"verdict     {result.verdict}")
    print(f"hit         {'yes' if result.is_hit else 'no'}")
    if result.hit_failure_reasons:
        print(f"filtered    {'; '.join(result.hit_failure_reasons)}")
    if result.result_id:
        print(f"result id   {result.result_id}")
    return 0


def _cmd_serve(args: argparse.Namespace) -> int:
    import uvicorn

    uvicorn.run(
        "valkyrie.web.app:app", host=args.host, port=args.port, reload=args.reload
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="valkyrie",
        description="Molecular docking for neglected tropical diseases. "
        "All output is an in-silico prediction, never clinical advice.",
    )
    parser.add_argument("--version", action="version", version=__version__)
    parser.add_argument("-v", "--verbose", action="store_true")

    subparsers = parser.add_subparsers(dest="command", required=True)

    targets = subparsers.add_parser("targets", help="list available targets")
    targets.set_defaults(handler=_cmd_targets)

    screen = subparsers.add_parser("screen", help="screen one molecule")
    screen.add_argument("molecule", help="compound name or SMILES")
    screen.add_argument("-t", "--target", default="pf-dhfr")
    screen.add_argument(
        "-e", "--exhaustiveness", type=int, default=DEFAULT_EXHAUSTIVENESS
    )
    screen.add_argument("--json", action="store_true", help="print the full result")
    screen.add_argument("--no-store", action="store_true", help="do not persist")
    screen.add_argument("--no-explanation", action="store_true", help="skip the AI stage")
    screen.set_defaults(handler=_cmd_screen)

    serve = subparsers.add_parser("serve", help="run the web application")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8100)
    serve.add_argument("--reload", action="store_true")
    serve.set_defaults(handler=_cmd_serve)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    _configure_logging(args.verbose)
    return args.handler(args)


if __name__ == "__main__":
    raise SystemExit(main())
