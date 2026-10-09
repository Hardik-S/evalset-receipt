# EvalSet Receipt

Create a small portable receipt for the exact bytes of a local evaluation JSONL file. Verify it later without uploading the dataset or printing its contents.

## Quickstart

Requires Python 3.10 or newer. From a fresh checkout:

```console
python -m pip install .
evalset-receipt create examples/dataset.jsonl --output receipt.json
evalset-receipt verify examples/dataset.jsonl receipt.json
```

The receipt contains only a format version, SHA-256 digest, byte count, and LF-delimited record count. Matching content exits 0; changed content exits 1; malformed inputs/receipts exit 2.

## Scope

The CLI hashes exact file bytes; line endings and whitespace are part of the digest. Record count is the number of LF-delimited records, counting a non-newline-terminated final record once; an empty file has zero records. This is a local content receipt, not a dataset registry or experiment tracker.

No network, model/provider, dataset parsing, evaluation, quality, or benchmark claims. Public examples use synthetic data only.
