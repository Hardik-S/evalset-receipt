# Independent release review — EvalSet Receipt v0.1.0

**Recommendation: PASS**
**Reviewed code commit:** `cd6eab95662306a4448eeb0b1022cf409e7f1e51`
**PR:** [#4](https://github.com/Hardik-S/evalset-receipt/pull/4)
**Review issue:** [#5](https://github.com/Hardik-S/evalset-receipt/issues/5)

A bounded independent reviewer tested the exact commit and returned PASS. The reviewer could not write files in its delegated environment; this artifact records its evidence without changing the recommendation.

## Evidence

- `python -m pytest -q`: **21 passed**.
- Fresh Python virtual environment: `python -m pip install .` succeeded; the installed CLI ran from the environment's `site-packages`.
- Installed CLI quickstart: create and matching verify exited 0; modified synthetic dataset exited 1; malformed, duplicate-key, NaN, Infinity, boolean, unsupported, wrong-type, negative and missing inputs exited 2.
- Exact-byte SHA-256, byte counts and LF record counts matched independently calculated results for empty files, LF and CRLF data, and terminated and unterminated final records. Repeated receipt creation was deterministic.
- Synthetic private markers did not appear in create, match, mismatch or invalid-input output.
- Runtime behavior uses the Python standard library; no network, provider, model or dataset parsing is involved. README and launch commands matched observed behavior.
- Exact-head GitHub Actions run [37961836021](https://github.com/Hardik-S/evalset-receipt/actions/runs/37961836021) passed Ubuntu and Windows on Python 3.10 and 3.13, including the installed CLI quickstart. GitGuardian passed.

## Scope and limits

The tool records and verifies exact file bytes and LF-delimited line counts. It does not validate JSONL semantics, evaluate data, track datasets or runs, or make quality, benchmark or novelty claims. Public examples are synthetic.

No product blocker remains. The independent reviewer made no product edits.
