"""Command line interface for local EvalSet receipts."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from .receipt import create_receipt, verify_receipt


_METADATA_KEYS = ("format_version", "sha256", "byte_count", "record_count")


def _metadata(result: dict[str, Any]) -> dict[str, Any]:
    """Keep terminal output restricted to documented receipt metadata."""
    return {key: result[key] for key in _METADATA_KEYS if key in result}


def _emit(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, sort_keys=True))


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="evalset-receipt",
        description="Create and verify local receipts for JSONL evaluation datasets.",
    )
    commands = parser.add_subparsers(dest="command", required=True)

    create = commands.add_parser("create", help="Create a receipt for a dataset.")
    create.add_argument("dataset", type=Path, help="Path to the local JSONL dataset.")
    create.add_argument("--output", required=True, type=Path, help="Where to write the receipt JSON.")

    verify = commands.add_parser("verify", help="Verify a dataset against a receipt.")
    verify.add_argument("dataset", type=Path, help="Path to the local JSONL dataset.")
    verify.add_argument("receipt", type=Path, help="Path to the receipt JSON.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "create":
            result = create_receipt(args.dataset)
            args.output.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
            _emit({"status": "created", **_metadata(result)})
            return 0

        result = verify_receipt(args.dataset, args.receipt)
        status = result.get("status")
        if status == "match" and result.get("matches") is True:
            _emit({"status": "match"})
            return 0
        if status == "mismatch" and result.get("matches") is False:
            _emit({"status": "mismatch"})
            return 1
        if status in {"invalid_receipt", "dataset_unreadable"}:
            # The engine's diagnostics are deliberately value-free and safe to show.
            diagnostics = result.get("diagnostics", [])
            _emit({"status": "invalid", "diagnostics": diagnostics})
            return 2
        raise ValueError("Invalid verification result")
    except Exception:
        # Exception text can contain paths, record snippets, or parser details.
        print("evalset-receipt: invalid input or receipt", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
