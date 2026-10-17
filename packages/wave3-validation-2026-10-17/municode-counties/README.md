# Wave 3 Municode counties and additional cities validation

This package owns sequences76,77,83,84,88,89,90,91,93,95,96,97. It validates bounded, live acquisition and parsing methods. `results.json` contains one row per assigned jurisdiction and separates primary legal-provision records from supplemental government PDF-page records. Every `complete_corpus` value is false.

## Setup and offline verification

Use Python3.11+ and install `requirements.txt` into a local virtual environment. The tested host is macOS26.6.2 arm64 with Python3.12.14, lxml6.1.1, pypdf6.10.0 and pdfplumber0.11.9. The retained `.venv/bin/python` uses the tested bundled Python base and system site packages; `.venv` is local verification infrastructure, not portable evidence. Install requirements afresh after relocation.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -B scripts/verify.py
```

The verifier makes no network requests, checks retained source hashes and executed script hashes, reparses into temporary directories, and compares JSONL/CSV bytes. It does not overwrite source or normalized evidence. `manifest.json`, when sealed, covers deliverable files and excludes local dependencies, caches and itself. Completed acquisition/verification logs are included.

For live browser acquisition install Node18+ and Playwright (`npm install`), and ordinary installed Google Chrome. Tested Node24.19.0/Playwright1.62.1 and Chrome155 are recorded exactly in each acquisition receipt. The collector does not require Codex APIs. Playwright resolves from the local `package.json` by default; `PLAYWRIGHT_MODULE_ROOT` is an optional development override. Python3 stdlib with POSIX `fcntl` is used for the cross-process gate; Windows operation was not tested.

```sh
MUNICODE_EXPECTED_CLIENT_NAMES='["Richmond"]' MUNICODE_EXPECTED_STATE=VA \
  node scripts/collect_browser.cjs \
  'https://library.municode.com/va/richmond/codes/code_of_ordinances' fresh/richmond 3
python3 scripts/normalize.py fresh/richmond --offline
```

Always use a fresh output path. `scripts/collect_browser_all.py` serially runs the exact assigned source routes from `collect_all.py`. Baton Rouge's explicit publisher identity is `Baton Rouge, East Baton Rouge Parish`. Source state, client and visible publication bindings are asserted. Receipts retain exact collector and gate bytes, selected nodes, full publication inventory, full TOC, raw bodies, timing, runtime and native download result. The browser path operates ordinary public document/API requests; no imported cookies, login, proxy rotation, challenge interaction or legal-content mocking. The currently supported collector can omit redundant static application assets following an ordinary rendered availability check by the coordinating group; publisher security scripts remain enabled. Full ordinary application bootstrap is available with `MUNICODE_FULL_BOOTSTRAP=1`.

## Rate limits and retained failures

All Municode collectors share `/tmp/compliSolv-municode-rate-gate`, with3.5seconds between request reservations across processes. `MUNICODE_GATE_DIR` can point to a deliberately shared replacement. A new challenge or429 writes an atomic persistent browser stop;429 also preserves at least300seconds and any longer Retry-After. Do not remove a stop automatically or use fresh profiles/endpoints to circumvent it. The current historical direct collector refuses to run while `family-stop-context.json` marks direct HTTP stopped, even after relocation. Direct HTTP was stopped after coordinated Cincinnati/Fairfax challenge reports; its scripts remain historical evidence and must not be used while that stop applies. Richmond's eight successful direct API responses, acquired before the stop, are retained in `http/richmond`; its driver was terminated before a publisher binary request. Offline continuation is explicitly recorded and is not a new live acquisition.

`family-stop-context.json` records that sequence. A coordinator authorized the ordinary browser path only after an unassisted public page rendered successfully. Normal browser requests retain the direct stop and have their own persistent challenge/429 stop.

## Scope and applicability

`source-scope-inventory.json` separates tested primary samples from other publications and TOC families. A publication inventory is discovery evidence, not collection of its legal provisions. Richmond and Norfolk are Virginia independent cities. Los Angeles County, Clark County and Westchester County are separate legal layers from incorporated municipalities; territorial applicability must be determined provision by provision. Baton Rouge / East Baton Rouge Parish is one combined target, with city/parish/unincorporated-area qualifiers retained and no city-only population attached.

Government routes provide separate Baton Rouge UDC and Clark Title30 PDFs. `scripts/government_pdfs.py` acquires only observed `.gov` PDF links with slow, serial GETs and refuses publisher redirects. It normalizes source PDF pages without inventing section boundaries. `native/*/normalized` identifies each record explicitly as a PDF page. Full native files are preserved, but only a bounded page sample is normalized. Cambridge's official page identifies separately published zoning; a municipal-code sample does not validate that zoning corpus. Official Clark routing also lists later amendments not yet codified. Baton Rouge warns not all council ordinances/resolutions are included in the published code.

## Quality and currency limits

Source HTML is retained with heading/path, exact requested Docs.Id, body SHA, cross-reference attributes, lists, footnotes and table cells. `verify_tables.cjs` performs independent offline Chrome DOM comparisons of cell text, tag, rowspan and colspan for any HTML table sample; all network is blocked. Its output is supplemental QA, not another live acquisition. Native PDF grid extraction has explicit limits: visual review of Clark Table30.02-1 found dropped abbreviation/reference cells and the final row; the original page/PDF remain authoritative evidence and the extracted grid is not certified. Baton Rouge Table9.A has merged headers and split extraction regions, also uncertified. See `evidence/pdf-visual/qa.json` and renders.

Publisher downloads are genuine native publication PDFs when enabled, separate from browser print. PDF magic/hash/readability and first-cover edition labels are checked by `scripts/validate_downloads.py`; that is an authoring report command, not the read-only verifier. A matching cover supplement proves only the displayed label, not full-body equivalence or current incorporation of every ordinance. Clark's government Title30 landing label, PDF filename and cover dates differ; retained labels are reported separately.

Recorded export exceptions: Baton Rouge / East Baton Rouge Parish PDF Supplement103 differs from API Supplement104 Update1 and is marked partial. Richmond recodification has no comparable supplement token. Clark begins with a Supplement149 insertion guide matching the API label; the state is absent from that first page, while API state/publication binding identifies Nevada. Primary PDF download is disabled for Cambridge, Los Angeles County and Westchester County; Cambridge's separately published Zoning Ordinance was additionally tested with3provisions and its native PDF (Supplement8). Los Angeles County10.04.070 was additionally sampled to preserve the explicit Title10 unincorporated-area/contract-city scope rule.

No database writes, production ingestion, full corpus collection, or Git operations are performed by this package. Prior sealed packages were not modified.

<!-- RECORDED OUTCOMES -->

## Recorded outcomes

|Seq.|Jurisdiction|Status|Legal provisions|PDF-page records|Primary native download|Edition label check|
|---|---|---|---:|---:|---|---|
|76|Richmond|standalone_e2e_pass|4|0|passed|unproven_missing_comparable_labels|
|77|Norfolk|standalone_e2e_pass|3|0|passed|cover_label_matches|
|83|Grand Rapids|standalone_e2e_pass|3|0|passed|cover_label_matches|
|84|Birmingham|standalone_e2e_pass|3|0|passed|cover_label_matches|
|88|Columbia|standalone_e2e_pass|3|0|passed|cover_label_matches|
|89|Stamford|standalone_e2e_pass|3|0|passed|cover_label_matches|
|90|Cambridge|standalone_e2e_pass|6|0|unavailable|not tested|
|91|Hartford|standalone_e2e_pass|3|0|passed|cover_label_matches|
|93|Los Angeles County|standalone_e2e_pass|4|0|unavailable|not tested|
|95|Baton Rouge / East Baton Rouge Parish|standalone_e2e_pass|3|10|partial|cover_label_differs|
|96|Clark County|standalone_e2e_pass|3|9|passed|cover_label_matches|
|97|Westchester County|standalone_e2e_pass|3|0|unavailable|not tested|

Primary live legal samples and supplemental PDF pages are separate units. Full jurisdiction corpus completeness and production ingestion remain untested for every row. Historical interrupted attempts are retained without double-counting them in this matrix. Read-only replay also verifies those historical bytes.
