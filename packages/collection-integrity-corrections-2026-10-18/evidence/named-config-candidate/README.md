# Isolated named enCodePlus configuration binding correction

This candidate closes the actual Overland scope fingerprint omission. It has not been promoted into production. Production launcher, registry, QA and readiness files remained unchanged; the fresh Flagstaff common job can continue on its captured source.

The minimal patch changes three shared source files:

- `collectors/registry/dispatch.py` exposes the named configuration source path and selected key for named enCodePlus targets only. Collection argv stays identical.
- `collectors/ops/launcher.py` includes `collectors/encodeplus/targets.json` in enCodePlus component fingerprints and records the selected exact dictionary in job/verification bindings.
- `collectors/qa/readiness_binding.py` fingerprints that input file and includes the current selected dictionary plus whole-file SHA in the selected-configuration descriptor. It re-reads the input even if the command plan was retained before a mutation.

The focused suite reproduces the original missing binding using the captured baseline, then proves an actual `overland.scope` mutation changes both corrected fingerprints. Missing file, missing/wrong key, unexpected path and ambiguous configuration sources fail closed. Named selection binds the exact dictionary and entire file; editing an unselected entry also changes the file fingerprint. Native/custom enCodePlus plans and other-family selection controls preserve their prior behavior. Changing shared code itself on promotion necessarily changes shared source fingerprints for all families; this candidate does not exempt old proofs from that current-code binding.

Eleven focused tests passed (2.021 seconds), and all sixteen existing readiness-binding regressions passed (0.772 seconds), with Python 3.12.14. Focused tests use a socket tripwire and temporary repositories only. No publisher access, live validation, image acquisition, image decoding, rendering, OCR, Git operation or readiness-status promotion occurred.

Review `named-config-binding.patch` and `validation-summary.json`. The promotion whitelist is exactly the three files listed above, copied from `candidate/`. The captured production baseline hashes must still match before a later authorized promotion. Do not copy baseline files, fixtures or test reports over production.

Run the portable read-only evidence verifier from any location:

```sh
python3 -B /path/to/ep-named-config-binding-candidate-v1/verify_candidate.py
```

Run the actual regression checks without touching source/evidence:

```sh
python3 -B /path/to/ep-named-config-binding-candidate-v1/test_named_binding.py
python3 -B /path/to/ep-named-config-binding-candidate-v1/candidate/collectors/qa/test_readiness_binding.py
```

All required test inputs and three source baselines are included. `source-baseline.json` additionally binds the actual publisher target configuration file. `finalize.py` is provenance of packaging in the development workspace; the portable commands above do not use its development path.
