"""CLI acceptance tests; subprocesses exercise the installed module entry."""

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run_cli(*args):
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / "src") + os.pathsep + env.get("PYTHONPATH", "")
    return subprocess.run(
        [sys.executable, "-m", "evalset_receipt.cli", *map(str, args)],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def test_cli_create_emits_deterministic_json_with_exact_digest(tmp_path):
    dataset = tmp_path / "synthetic.jsonl"
    receipt_a = tmp_path / "a.json"
    receipt_b = tmp_path / "b.json"
    payload = b'{"example":"synthetic"}\r\n'
    dataset.write_bytes(payload)

    first = run_cli("create", dataset, "--output", receipt_a)
    second = run_cli("create", dataset, "--output", receipt_b)

    assert first.returncode == second.returncode == 0
    assert receipt_a.read_bytes() == receipt_b.read_bytes()
    doc = json.loads(receipt_a.read_text(encoding="utf-8"))
    assert doc == {
        "format_version": 1,
        "sha256": hashlib.sha256(payload).hexdigest(),
        "byte_count": len(payload),
        "record_count": 1,
    }
    assert payload.decode() not in first.stdout + first.stderr


def test_cli_verify_match_is_zero_and_mismatch_is_one_without_dataset_echo(tmp_path):
    dataset = tmp_path / "synthetic.jsonl"
    receipt = tmp_path / "receipt.json"
    marker = "SYNTHETIC_PRIVATE_MARKER"
    dataset.write_text('{"text":"' + marker + '"}\n', encoding="utf-8")
    created = run_cli("create", dataset, "--output", receipt)
    assert created.returncode == 0

    matched = run_cli("verify", dataset, receipt)
    assert matched.returncode == 0
    assert marker not in matched.stdout + matched.stderr

    dataset.write_text('{"text":"different"}\n', encoding="utf-8")
    mismatch = run_cli("verify", dataset, receipt)
    assert mismatch.returncode == 1
    assert marker not in mismatch.stdout + mismatch.stderr


def test_cli_invalid_receipts_and_missing_files_exit_two_without_content_echo(tmp_path):
    dataset = tmp_path / "synthetic.jsonl"
    receipt = tmp_path / "receipt.json"
    marker = "SYNTHETIC_PRIVATE_MARKER"
    dataset.write_text(marker, encoding="utf-8")
    receipt.write_text('{"format_version":1,"format_version":1}', encoding="utf-8")

    invalid = run_cli("verify", dataset, receipt)
    missing_dataset = run_cli("verify", tmp_path / "absent.jsonl", receipt)
    missing_receipt = run_cli("verify", dataset, tmp_path / "absent-receipt.json")

    for result in (invalid, missing_dataset, missing_receipt):
        assert result.returncode == 2
        assert marker not in result.stdout + result.stderr


def test_checked_in_synthetic_example_and_receipt_verify():
    result = run_cli("verify", ROOT / "examples" / "dataset.jsonl", ROOT / "examples" / "receipt.json")
    assert result.returncode == 0
    assert json.loads(result.stdout) == {"status": "match"}
