# Wave 3 standalone acquisition validation — six jurisdictions

This package validates bounded live legal-text acquisition, normalization and genuine publisher downloads for Cleveland, Cincinnati, Fort Wayne, Toledo, San Diego County and Fairfax County. It does **not** contain or demonstrate complete jurisdiction corpora. See `results.json` for one result per assignment and `publication-inventory.json` for separate publications, embedded families, edition evidence and untested leads.

All collection ran on macOS Darwin25.6/arm64 using ordinary installed headed Chrome155.0.8059.84, Node24.19.0, Playwright1.62.1 and Python3.9.6. Exact Python dependencies are in `requirements-lock.txt`. There is no Codex API, CUA, browser profile, external package import or prior-output runtime dependency. The absolute bundled-runtime paths used in this workstation's logs are evidence, not requirements.

## Install and replay retained evidence

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-lock.txt
npm install
.venv/bin/python scripts/replay.py --offline
```

`--offline` performs no network requests and reads/compares only. It reconstructs normalized JSONL/CSV in memory, checks source/byte hashes and selection identity, and compares with retained outputs. `--write` is the explicit output-writing mode used after acquisition. The convenience `normalize.py --offline` inherited from the Municode engine writes artifacts; use **`replay.py --offline`** for read-only verification. The venv is intentionally retained until root's independent replay, but is excluded from the portable evidence manifest.

## New live acquisitions

Use a directory that does not exist. Ordinary Google Chrome must be installed. The shared cross-process gates use Python fcntl and therefore require a POSIX host (macOS/Linux); Windows transport locking is untested. `NODE_BIN` can select Node; Playwright resolves from normal `node_modules`, or set `PLAYWRIGHT_MODULE` to its installed module path for American Legal and `PLAYWRIGHT_MODULE_ROOT` to a Node package.json for Municode. `PYTHON` selects the gate's Python interpreter if needed.

```sh
.venv/bin/python scripts/collect_alp.py --sequence 59 --out runs/new-cleveland
.venv/bin/python scripts/collect_alp.py --sequence 72 --out runs/new-fort-wayne
.venv/bin/python scripts/collect_alp.py --sequence 75 --out runs/new-toledo
.venv/bin/python scripts/collect_alp.py --sequence 94 --out runs/new-san-diego-county
.venv/bin/python scripts/collect_municode.py --sequence 63 --out runs/new-cincinnati
.venv/bin/python scripts/collect_municode.py --sequence 100 --out runs/new-fairfax-county
.venv/bin/python scripts/fairfax_encode.py --out runs/new-fairfax-zoning
```

The American Legal wrapper creates a portable new mini-package, discovers the current publication and bounded chapter, requests the selected section's native HTML and normalizes source/export. `runs/fresh-cleveland` is an actual live execution of this fresh-output wrapper with8 rendered records and1 matching native record. Main retained source acquisition and export scripts also ran live for all4 targets. The Municode fresh-output wrapper completed an actual2-node Fairfax County smoke in `runs/fairfax-current-smoke` using the exact final collector (SHA256 `2e91629d646a3b6c6f81140fdea19fb404efbd67b6dd5b327de76f71061154c5`). Both normalized records and unavailable-primary-PDF inventory outcome passed. The retained direct engine commands and exact executed versions are in receipts/logs.

American Legal uses ordinary TOC navigation (maximum4 levels), at most4 scroll steps per acquisition/expansion, and parses only fully rendered operative section containers. Its native export scope is **one selected section**, even when the rendered chapter sample includes many provisions. The native HTML bytes came from Download → Save HTML → the newly returned export-job UUID's OPEN link. They are not browser print-to-PDF. Each exported body is compared against the entire normalized rendered body with the same canonical documentID, and every requested heading is bound. Only harmless whitespace/punctuation spacing and case are normalized for comparison.

Municode direct HTTP returned403 with `Cf-Mitigated: challenge`; those initial failures are retained in `runs/cincinnati-live` and `runs/fairfax-county-live`. All direct-HTTP work remains stopped. Root then authorized a normal headed-browser availability check, which succeeded unassisted, followed by the gated normal public browser workflow. No challenge interaction, imported cookies, proxy, fingerprint masking or access-control bypass occurred. The shared gate defaults to `/tmp/compliSolv-municode-rate-gate` across all processes, spaces publisher starts by3.5seconds, persists browser challenge/rate-limit stops, and honors Retry-After. Do not delete or reset a stop to continue. The retained Cincinnati run used full app bootstrap; later Fairfax runs use normal document plus browser API calls while omitting application assets, with publisher security scripts left enabled. A minimal `rendered.html/png` is an **application shell**, not rendered-section text QA; substantive source evidence is the retained identity-bound CodesContent HTML and raw responses.

Municode binds client name/state, visible ClientContent publication, productID, pinned latest-job ID and exact requested documentID. The native publication PDF is separately downloaded only when the current inventory enables it; native bytes, PDF parsing and selected-body/edition outcomes are recorded separately. A whole-book native download is **not** a claim that all pages or sections were normalized. Signed download URLs may expire; rerun the resolver, not a stored signed URL.

Fairfax's **independent** zoning ordinance uses ordinary server-rendered enCodePlus `doc-view.aspx` endpoints, exact requested `#thePage` and section identity, and an observed native OpenPDF action. Three selected operative provisions include §2100's real HTML table (26rows,114cells). HTML source is checked independently for table text/rowspan/colspan; all114 source cell texts also occur in its native2-page PDF. The PDF was rendered and visually inspected. Native PDF footer says July1,2026; official zoning page says updated July2,2026, so exact whole-publication edition equivalence is unproven. The shared enCodePlus gate defaults to `/tmp/compliSolv-encodeplus-rate-gate` at3.5seconds. The Public Facilities Manual and Comprehensive Plan remain separately inventoried and unacquired.

## Scope, editions and remaining work

The4 American Legal samples contain8/19/9/19 normalized operative sections and1 native section each. They are general provisions and do not validate that publisher's complex tables. Source URLs, current overview labels, native export version IDs, timestamps, bytes and hashes are in receipts and validation reports. Currentness metadata describes the publisher's stated edition; it does not independently prove that all recent enactments have been codified.

Cincinnati's official departmental AppendixE PDF is retained as an additional source only: its filename suggests Chapter319, but the compilation starts Chapter317. Three fully delimited sections were parsed from the first2 pages of the67-page PDF. Visible amendment histories are old, and no current-through date was established. This alternative is not substituted for the current Municode publication.

Cincinnati's publisher native PDF is valid and3,616pages long, but its front sheet is **Supplement47/March2026 through Ord0010-2026 effective January14,2026**. The live pinned job is **Supplement48 Update4 through Ord0223-2026 effective June17,2026**. The retained download is therefore marked partial for current-edition qualification; bounded front-matter35pages plus12pages at its observed AdministrativeCode bookmark demonstrate text import, while full-edition reconciliation is untested. These47sampled PDFpages do not contain the3selected APIbody probes; they must not be reported as matched operative export records.

San Diego means **San Diego County**, with Regulatory, Administrative, Zoning, ordinance lists, Board policies and County Charter separate from San Diego city law. The tested main sample is Regulatory Ordinances under `sandiego_regs`; current zoning is `sdzoning`, not the stale assignment `sd_zoning`. Fairfax is **Fairfax County**, not the independent City of Fairfax. Embedded charter/zoning chapters are distinguished from independently hosted publications in the inventory.

For whole ingestion, the tech team must enumerate and deduplicate every relevant publication and pinned edition, traverse every leaf, page/scroll until complete, reconcile TOC node IDs against emitted operative records, handle repealed/reserved/appendix/table/image/map/footnote content, preserve citation links, and audit publication applicability. Add resumable checkpoints and publisher-approved bulk/export arrangements where available. Validate current-through metadata independently and reconcile native-export editions before merging records. None of those full-ingestion/completeness steps is proven by these bounded tests.

Exact executed collectors and gate scripts are retained in `scripts/executed`, individual `runs/*/executed-*` and `runs/fairfax-zoning-live/script-versions`. Scripts can evolve after a capture; each receipt points to the actual executed hash. Original403 failures, later successful transport, native download outcome and parsing outcome are separate. Only owned browser instances were closed. No database, prior sealed output or Git state was changed by this package's collector work.
