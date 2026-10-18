The helper accepts an existing exact Flagstaff operational collection and invokes only the chosen common `verify` action. The standard family verifier performs its usual full raw replay into temporary scratch; the helper never acquires source or normalizes in place. All current acceptance fields, including false or null dimensions, remain unchanged. A successful adapter run exits 0 even when the valid common verification is incomplete (exit 2); inspect `terminal.json` and the preserved common acceptance result. Adapter refusal exits 1 and retains failure evidence.

Run from any directory, using ordinary Python or `-B`:

```sh
python verify_flagstaff_input.py --input /absolute/existing-flagstaff-collection --collector-root /absolute/collector-repository --runtime /absolute/owned-common-runtime --out /absolute/fresh-proof-directory
```

The output directory must be new and separate from the evidence, collector and runtime. Exact original common stdout is retained as `common-readonly.json`; the exact JSON family log is copied as `family-verification.json`. `read-only-proof.json` adds only the safe relative report path, its SHA256 and an explicit lineage object. The existing corpus writer can consume that proof without manually extracting an absolute log path. The original proof/config/acceptance/acquisition mode is preserved. This helper is outside the pure eight writer modules.

```sh
python -B -m unittest discover -s candidate -p test_verify_flagstaff_input.py -v
```

The 25 tests use controlled common subprocess fixtures, including two ordinary-Python CLI executions. The actual full Flagstaff helper has deliberately not been run during this independent candidate review. `actual-entry-source-review-final` binds the source-only common verify-path inspection and exact current originals binding parity. The initial untested helper and earlier test/source-review receipts remain under explicit history/prior names. No production file or Git state was changed.
