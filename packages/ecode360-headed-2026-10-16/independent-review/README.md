# Independent offline review of fresh eCode360 headed acquisition

This package reviews retained public legal DOM and the delivered standalone importer without publisher network requests. `REVIEW.json` is the final qualified result; preliminary and baseline outputs are labeled separately. Actual fresh acquisition belongs to the adjacent `ecode360` package and its receipts. This review does not claim publisher PDF/Word download validation or complete city-code inventory coverage.

The meaningful controls are jurisdiction/customer/code/route binding, stable publisher identity before and after capture, retained source SHA, exact printed numbering and source anchors, complete sampled body order and word boundaries, preserved legal tables and cross-references, CSV/JSON/publication equality, source provenance, and clean versus interrupted/resumed equality. Negative metadata and mocked HTTP responses are regression tests, not live acquisition evidence.

Use Python 3.9+ in a fresh environment:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r reviewed-source/requirements.txt
.venv/bin/python review_controls.py --package reviewed-source --out rerun-controls
.venv/bin/python review_acceptance.py --package reviewed-source --receipt fixtures/fresh/foster-city-ca/receipt.json --out rerun-acceptance.json
.venv/bin/python review_fresh.py --package reviewed-source --receipts fresh-receipts.json --out rerun-semantic
.venv/bin/python compatibility.py --package reviewed-source --tests reviewed-tests
```

Run commands from this directory. Outputs must use fresh names; accepted evidence is immutable. No absolute runtime dependency is required. The recorded execution used the shared temporary review environment, whose package versions and Python version are recorded in `REVIEW.json`.

`baseline-source/`, `fixtures/baseline-foster/`, and `baseline-control-results/` preserve the prior behavior and actual older source used to reproduce the observed control defects. `proposed-source/`, `minimal-controls.patch`, and `patch-bindings.json` preserve the reviewed minimal proposal handed to the acquisition worker. Final tests use `reviewed-source/`, copied from the worker after its freeze. The original acquisition versions remain distinct from the final parser revision, and local replay is never relabeled as a fresh acquisition.

An accepted capture is a chapter DOM subtree with separately recorded publisher identity metadata and an explicitly documented synthetic parser wrapper. Its raw hash and capture scope remain visible; the wrapper is not described as downloaded full-page HTML. Full publisher export downloads require their own format, scope, identity, edition, and acquisition evidence before they can be admitted.

Final frozen results: **14 actual fresh headed DOM sources, 134 sampled provisions, 8 legal tables, 309 cross-references, 5/5 safety controls, 16/16 receipt/text checks, and 27/27 existing offline tests passed**. Fresh acquisitions started/finished on 2026-10-16 UTC. This reviewer made zero publisher requests.

| Jurisdiction slug | Sampled provisions | Publisher code | Publisher currency |
|---|---:|---|---|
| foster-city-ca | 7 | 337727 | 2026-01-26 |
| burlingame-ca | 1 | 332192 | 2026-04-20 |
| emeryville-ca | 7 | 336039 | 2026-06-02 |
| half-moon-bay-ca | 10 | 336191 | 2026-05-05 |
| malibu-ca | 28 | 336335 | 2026-06-22 |
| san-leandro-ca | 1 | 337882 | 2026-07-20 |
| santa-clara-ca | 4 | 329535 | 2026-01-27 |
| santa-monica-ca | 9 | 336847 | 2026-07-28 |
| santa-rosa-ca | 13 | 337811 | 2026-09-15 |
| south-san-francisco-ca | 8 | 336974 | 2026-09-09 |
| seatac-wa | 12 | 337588 | 2026-09-30 |
| sunnyvale-ca | 8 | 337833 | 2026-08-11 |
| tukwila-wa | 16 | 332495 | 2026-05-18 |
| west-hollywood-ca | 10 | 336663 | 2026-06-29 |
