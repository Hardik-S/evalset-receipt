"""Create and verify privacy-preserving receipts for local JSONL datasets."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any


_RECEIPT_FIELDS = {"format_version", "sha256", "byte_count", "record_count"}
_SHA256_RE = re.compile(r"[0-9a-f]{64}\Z")


def _record_count(data: bytes) -> int:
    """Count LF-delimited records, including a final unterminated record."""
    if not data:
        return 0
    return data.count(b"\n") + (not data.endswith(b"\n"))


def create_receipt(dataset_path: Path) -> dict[str, Any]:
    """Return the version 1 receipt for the exact bytes at *dataset_path*."""
    data = Path(dataset_path).read_bytes()
    return {
        "format_version": 1,
        "sha256": hashlib.sha256(data).hexdigest(),
        "byte_count": len(data),
        "record_count": _record_count(data),
    }


def _reject_constant(value: str) -> None:
    raise ValueError("non-standard JSON constant")


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def _validate_receipt(value: Any) -> list[str]:
    """Return stable field-level diagnostics without exposing receipt values."""
    if not isinstance(value, dict):
        return ["receipt must be a JSON object"]

    diagnostics: list[str] = []
    keys = set(value)
    if keys != _RECEIPT_FIELDS:
        if keys - _RECEIPT_FIELDS:
            diagnostics.append("receipt has unexpected fields")
        if _RECEIPT_FIELDS - keys:
            diagnostics.append("receipt is missing required fields")

    version = value.get("format_version")
    if type(version) is not int or version != 1:
        diagnostics.append("format_version must be integer 1")

    digest = value.get("sha256")
    if not isinstance(digest, str) or _SHA256_RE.fullmatch(digest) is None:
        diagnostics.append("sha256 must be 64 lowercase hexadecimal characters")

    for field in ("byte_count", "record_count"):
        count = value.get(field)
        if type(count) is not int or count < 0:
            diagnostics.append(f"{field} must be a nonnegative integer")
    return diagnostics


def verify_receipt(dataset_path: Path, receipt_path: Path) -> dict[str, Any]:
    """Compare a dataset to a strict receipt, returning stable safe diagnostics.

    The returned mapping has ``matches`` (bool), ``status`` (stable code), and
    ``diagnostics`` (safe human-readable messages). Neither file's contents are
    included in diagnostics.
    """
    try:
        receipt_text = Path(receipt_path).read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return {
            "matches": False,
            "status": "invalid_receipt",
            "diagnostics": ["receipt could not be read as UTF-8"],
        }

    try:
        receipt = json.loads(
            receipt_text,
            object_pairs_hook=_unique_object,
            parse_constant=_reject_constant,
        )
    except (json.JSONDecodeError, ValueError):
        return {
            "matches": False,
            "status": "invalid_receipt",
            "diagnostics": ["receipt is not strict JSON"],
        }

    diagnostics = _validate_receipt(receipt)
    if diagnostics:
        return {"matches": False, "status": "invalid_receipt", "diagnostics": diagnostics}

    try:
        expected = create_receipt(Path(dataset_path))
    except OSError:
        return {
            "matches": False,
            "status": "dataset_unreadable",
            "diagnostics": ["dataset could not be read"],
        }

    differences = [
        field
        for field in ("sha256", "byte_count", "record_count", "format_version")
        if receipt[field] != expected[field]
    ]
    if differences:
        return {
            "matches": False,
            "status": "mismatch",
            "diagnostics": ["receipt does not match dataset: " + ", ".join(differences)],
        }
    return {"matches": True, "status": "match", "diagnostics": []}
