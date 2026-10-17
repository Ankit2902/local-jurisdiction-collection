# American Legal full-publication validation evidence

The selected final live run is `index-current-final`, captured with all six current production modules. `form-based-no-images-final` is the full native PDF/page-layer proof. Read `validation-summary.json` and `collector/README.md` before interpreting coverage.

The index has complete independently reconciled text (30 nodes,97 owned blocks,59 tables) and genuine native HTML, but1940 linked nonimage ordinance PDFs remain uncollected. The Cleveland form-based code has a54,780,031-byte native PDF and212 page-layer records; PDF legal-section order is unqualified. Neither run claims complete jurisdiction coverage. Images intentionally become `[IMAGE]`; there are zero separate image binary downloads.

`index-no-images-final` is retained current-policy resume proof. Earlier normalized outputs in `index-native-final`, `form-based-pdf-final`, and `ordinance-index-live` are superseded by the image policy. The last directory is used only as an independent raw renderer input, recomputed under current policy. `research/bulk-probe` contains whole Cleveland native scope proof without a completed independent nested TOC reconciliation. Initial access failures and prior executed revisions are preserved.

Run from this package root with normal Python dependencies:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r collector/requirements.txt
.venv/bin/python collector/verify.py collector/fixtures/nested-synthetic.zip --offline
.venv/bin/python collector/verify.py collector/fixtures/live-index.zip --offline --allow-incomplete
.venv/bin/python collector/compare.py collector/fixtures/live-index.zip collector/fixtures/renderer-reference-raw.zip
.venv/bin/python collector/test_faults.py
.venv/bin/python collector/verify.py form-based-no-images-final --offline --allow-incomplete
```

Verifiers read ZIPs without extraction or modification. PDF verification reparses every page and can take several minutes. `--allow-incomplete` preserves all incomplete flags and only adjusts the exit code for sound limited evidence. Without this switch both real runs return2; corruption returns1. The synthetic complete fixture returns0.

Retain `.venv` locally for testing, but exclude environments, bytecode caches and browser profiles from release. `freeze-manifest.json` lists portable artifact hashes, excluding itself and local environments.
