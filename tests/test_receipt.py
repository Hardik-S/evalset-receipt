"""Acceptance tests for the byte-level receipt contract."""

import hashlib
import json
from pathlib import Path

import pytest

from evalset_receipt.receipt import create_receipt, verify_receipt


@pytest.mark.parametrize(
    ("payload", "records"),
    [
        (b"", 0),
        (b"one\n", 1),
        (b"one\ntwo\n", 2),
        (b"one\ntwo", 2),
        (b"one\r\ntwo\r\n", 2),
        (b"one\r\ntwo", 2),
    ],
)
def test_create_receipt_hashes_exact_bytes_and_counts_lf_records(tmp_path, payload, records):
    dataset = tmp_path / "synthetic.jsonl"
    dataset.write_bytes(payload)

    result = create_receipt(dataset)

    assert result == {
        "format_version": 1,
        "sha256": hashlib.sha256(payload).hexdigest(),
        "byte_count": len(payload),
        "record_count": records,
    }


def test_create_receipt_is_deterministic(tmp_path):
    dataset = tmp_path / "synthetic.jsonl"
    dataset.write_bytes(b'{"kind":"synthetic"}\n')

    assert create_receipt(dataset) == create_receipt(dataset)


def test_verify_receipt_reports_match_and_byte_mismatch_without_content(tmp_path):
    dataset = tmp_path / "synthetic.jsonl"
    receipt = tmp_path / "receipt.json"
    secret_marker = b"SYNTHETIC_PRIVATE_MARKER"
    dataset.write_bytes(b'{"text":"' + secret_marker + b'"}\n')
    receipt.write_text(json.dumps(create_receipt(dataset)), encoding="utf-8")

    matched = verify_receipt(dataset, receipt)
    assert matched["matches"] is True
    assert isinstance(matched.get("status"), str)

    dataset.write_bytes(b'{"text":"changed"}\n')
    mismatch = verify_receipt(dataset, receipt)
    assert mismatch["matches"] is False
    assert isinstance(mismatch.get("status"), str)
    assert secret_marker.decode() not in json.dumps(mismatch)


@pytest.mark.parametrize(
    "raw_receipt",
    [
        '{"private":"RECEIPT_PRIVATE_MARKER",',
        '{"format_version":1,"format_version":1,"sha256":"' + "0" * 64 + '","byte_count":0,"record_count":0}',
        '{"format_version":1,"sha256":"' + "0" * 64 + '","byte_count":NaN,"record_count":0}',
        json.dumps({"format_version": True, "sha256": "0" * 64, "byte_count": 0, "record_count": 0}),
        json.dumps({"format_version": 2, "sha256": "0" * 64, "byte_count": 0, "record_count": 0}),
        json.dumps({"format_version": 1, "sha256": "RECEIPT_PRIVATE_MARKER", "byte_count": 0, "record_count": 0}),
        json.dumps({"format_version": 1, "sha256": "0" * 64, "byte_count": -1, "record_count": 0}),
        json.dumps([1, 2, 3]),
    ],
)
def test_verify_rejects_invalid_receipts_safely(tmp_path, raw_receipt):
    dataset = tmp_path / "synthetic.jsonl"
    receipt = tmp_path / "receipt.json"
    marker = "SYNTHETIC_DATA_MUST_NOT_APPEAR"
    dataset.write_text(marker, encoding="utf-8")
    receipt.write_text(raw_receipt, encoding="utf-8")

    result = verify_receipt(dataset, receipt)

    assert result["matches"] is False
    assert isinstance(result.get("status"), str)
    assert marker not in json.dumps(result)
    assert "RECEIPT_PRIVATE_MARKER" not in json.dumps(result)


def test_verify_missing_dataset_or_receipt_returns_safe_failure(tmp_path):
    dataset = tmp_path / "missing.jsonl"
    receipt = tmp_path / "missing-receipt.json"
    result = verify_receipt(dataset, receipt)

    assert result["matches"] is False
    assert isinstance(result.get("status"), str)
    assert str(tmp_path) not in json.dumps(result)
