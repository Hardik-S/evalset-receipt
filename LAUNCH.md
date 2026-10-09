# Launch and smoke-check

Run from the repository root with Python 3.10 or newer. Install the package in the active environment:

```console
python -m pip install .
```

Create a receipt and verify it locally:

```console
evalset-receipt create examples/dataset.jsonl --output examples/receipt.json
evalset-receipt verify examples/dataset.jsonl examples/receipt.json
```

The `create` command writes JSON containing the format version, SHA-256 digest, byte count, and LF-delimited record count. `verify` reports `match` or `mismatch`; a match exits 0 and a mismatch exits 1. Invalid paths, unreadable files, or invalid receipt data exit 2 with a safe generic diagnostic. Dataset lines are not parsed or validated.

The commands operate on local files. Terminal output contains status and receipt metadata only; dataset lines and parser exception text are not displayed.
