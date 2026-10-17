# Municode state expansion validation — October 17, 2026

This package covers the 12 jurisdictions listed in `assignment.json`: Huntsville AL, Des Moines IA, Little Rock AR, Providence RI, Charleston SC, Bridgeport CT, Jackson MS, Fargo ND, Billings MT, Wilmington DE, Cheyenne WY, and Charleston WV. `results.json` contains one conservative outcome per target. All 12 passed standalone live acquisition through parsing for a bounded total of 36 substantive section records (three per jurisdiction). Eleven original native publisher PDF exports were acquired; Bridgeport advertises no enabled publication PDF. Every jurisdiction remains `complete_corpus: false`.

The primary workflow is ordinary standalone Python HTTP acquisition from the public endpoints used by the Municode application. The public organization route resolves the exact city/state and client ID; product metadata resolves the primary publication; latest job metadata pins the sampled version; the full tree inventories nodes and families; three observed leaf sections are downloaded and normalized to JSONL and CSV. This avoids a dependency on Codex or any existing project parser. Legal source HTML, headings, paths, lists, cross references, table cells/spans and notes survive in JSONL and retained raw responses. CSV supplies the core text fields. Unsupported or denied routes are retained as failures, without retries or alternate identities.

The legacy `Clients/keyword` route is not required. Some current endpoints may return 403 by jurisdiction or publication; the package records those responses. A successful endpoint for one city does not qualify every city. A publisher shell or routing page does not count as a legal-content sample.

## Setup and offline verification

Python 3.10+ is recommended (the live run used Python 3.12.14 on macOS ARM64). Create a local environment for optional official-PDF analysis:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-lock.txt
.venv/bin/python scripts/verify.py
```

Routine verification runs `scripts/verify.py` only: it normalizes into temporary directories and writes a byte-stable verification report, preserving source evidence and final outputs. The build/requalification scripts (`finalize_replay.py`, `quality.py`, `inspect_downloads.py`, `build_results.py`, and `table_sample.py --offline`) are explicit optional rebuild operations, not required for ordinary verification. The primary acquisition, normalization and `verify.py` use the Python standard library only. Brotli is needed to replay the compressed official Jackson routing HTML; pypdf supports the bounded official-PDF page extraction. PDF previews used pypdfium2; pdfplumber is included for optional deeper table analysis, not a claim of reconstructed table accuracy.

`verify.py` checks raw acquisition hashes, exact executed script snapshots, deterministic replay hashes, CSV/JSONL agreement, duplicate record identity rejection through the parser, and result evidence paths. It uses no network. The source snapshots are retained under `script-versions/` and each direct sample's own `script-versions/`. The initial browser failure is preserved under `live/huntsville-al/` and is not a passing acquisition.

## Fresh live examples

From this directory, use a new output directory for a fresh attempt; the default batch refuses to silently reacquire an already attempted target:

```sh
python3 scripts/acquire.py --sequence 44 --out /tmp/des-moines-live-new
python3 scripts/acquire.py --sequence 48 --out /tmp/bridgeport-live-new
python3 scripts/acquire.py
```

`MUNICODE_GATE_DIR` must be the same directory for every concurrent Municode process (default `/tmp/compliSolv-municode-rate-gate`). The copied shared implementation serializes requests with an OS file lock, keeps request starts at least three seconds apart, handles redirects individually, and persists a 429 cooldown of at least Retry-After or five minutes. No request retries, login, challenge interaction, cookie import, proxy or IP rotation occurs. macOS and Linux have `fcntl`; other platforms require an equivalent gate before live use. Only the stated macOS environment was live tested.

For the optional ordinary headed browser fallback, install Node.js, Google Chrome and Playwright:

```sh
npm install
node scripts/collect_browser.cjs 'https://library.municode.com/ct/bridgeport/codes/code_of_ordinances' /tmp/bridgeport-browser-new 3
python3 scripts/normalize.py /tmp/bridgeport-browser-new --offline
```

The executed browser version and node version are in each browser receipt. `PLAYWRIGHT_MODULE_ROOT` can point to an existing Playwright package.json; otherwise normal local `node_modules` resolution applies. `PYTHON` can select the Python interpreter for the shared gate. `BROWSER_CHANNEL` defaults to `chrome`. A headed desktop is required. Browser code snapshots used for acquisition are retained. The current optional fallback uses a lean public-API browser context by default (`MUNICODE_LEAN=0` selects the full application). It stops app/third-party assets before network while leaving publisher security scripts untouched, and it does not interact with access challenges. This fallback is qualified only where a retained live receipt identifies it.

## Exact collection boundary and work needed for full ingestion

`scripts/acquire.py` is a **bounded validator hardcoded to three selected provisions**: `selected=(pref or leaves)[:3]`. It enumerates the full TOC for inventory, filters to numbered leaf headings, favors paths outside charter/constitution, and fetches only those first three selected nodes. It does not walk all legal bodies. `--out` changes the output location, not this scope. The optional browser validator also defaults to a bounded sample; changing a sample count does not establish completeness.

The technical team must replace that selection with a coverage-driven ingestion plan before a full run:

1. Enumerate every TOC node in the pinned product/job, verify unique identifiers and record an explicit disposition for every node. Classify nodes by actual own content; containers can have substantive bodies, and leaf nodes can contain an entire chapter or links to separately published text. A leaf-only filter is insufficient. Des Moines Chapters 134 and 135, for example, appear as single TOC leaves and are outside the three-section sample.
2. Fetch each included node body, matching its exact `Docs.Id`; account for grouped responses and deduplicate by product ID, job ID and node ID. Retain headings, parent hierarchy, source order, HTML tables/spans, cross-reference attributes, notes, lists and attachments. Reconcile expected nodes against emitted records and explicit exclusion dispositions; three successful provisions cannot supply that reconciliation.
3. Resolve each separate publication in ClientContent independently, including charter, zoning and development publications where present. Capture separate job/version metadata, TOC, source bodies and publisher exports. Inventory MuniDocs, pending ordinances, zoning maps, incorporated documents and external chapter attachments with explicit inclusion decisions; a primary-code pass does not qualify them.
4. Add a deliberate resume/checkpoint policy, bounded error handling under the shared rate/cooldown gate, source version/drift checks, and broader structural equivalence sampling. Reconcile native PDF currency with online job metadata before substituting a PDF for online text. Preserve failed or excluded nodes rather than claiming successful corpus closure.

No full run, full-node coverage reconciliation, attachment closure or complete separate-publication ingestion was performed or tested in this package. Every `complete_corpus` field remains false. The retained full TOCs and publication inventories are planning evidence, not proof of fully ingested legal text.

## Publisher downloads and additional publications

Native publisher PDF acquisition is tested separately from the legal-section sample. The script inspects ClientContent's enabled PDF feature, resolves the exposed `PublicationPdfDownload` URL and downloads original PDF bytes. A passed download is not a fully parsed corpus. Browser print-to-PDF is never used. Disabled, missing, or blocked exports have their own status. Captured blob URLs contain expiring publisher query signatures; the fresh acquisition script resolves a new export URL rather than relying on a retained signed URL.

Official city alternatives under `official-pdf/` include original zoning PDFs for Huntsville, Providence, Jackson and Charleston WV when their download succeeds. The exported page records are labeled `pdf_page`, with physical PDF page numbers and source hashes; they are **not** reconstructed legal sections. Huntsville's sample skips its long TOC to include physical pages 20–22 and 24–35. Other PDFs use physical pages 1–15. The complete original PDF may be retained while only those pages are normalized. Cheyenne's original UDC PDF attempt is retained even when denied. The live official routes and extracted links appear under `routes/`.

Charleston SC has a separate Municode Zoning publication. Providence and Huntsville have separate official zoning PDFs. Fargo's official route places Land Development Code in Chapter 20 and links a 2026 LDC project; a project link alone does not establish an adopted replacement. Billings has 2026 zoning/subdivision amendments requiring reconciliation with the codified source. Bridgeport's official legacy-library query clientId=16075 must not be assumed to equal the current API ClientID; the organization endpoint resolves current identity. Charter/zoning scope still requires separate checks. Pending ordinances, MuniDocs, zoning maps, incorporated building standards and other separate documents are not assumed included by a primary code sample. Consult each result's publication inventory and family gaps.

The output validates transport and bounded parsing. It does not establish whole-jurisdiction corpus completeness, adoption status of every amendment, a current legal certification, or broad browser/platform compatibility.

The final parser replay preserves initial normalization outputs in `normalized-initial/` and records a separate offline phase in `final-normalization-phase.json`. Des Moines supplemental table QA uses the publisher history table (587 rows, 1,685 cells), explicitly metadata rather than substantive legal text. Two inspected fee/rate provisions contained no HTML table, and those negative qualification attempts are retained. The initial table-header linebreak discrepancy and its corrected offline replay are both retained.

Native PDF currency is separately inspected from first-three-page text. Des Moines, Providence, Fargo and Billings have first-page supplement mismatches against the current online job; later PDF pages/update sheets are not audited. A download success does not establish PDF/API equivalence.

Initial gate code reserved starts at 3.0/3.1 seconds; an integrated audit found a 2.899-second logged timestamp gap due to timestamp placement/jitter. The shared gate guard was increased to 3.5 seconds and the direct driver restarted after the first four completed state targets. Exact older script versions remain in evidence. No 429 response was observed in these state attempts.

The auxiliary official-route discovery receipts retain URL, acquisition time, response headers and raw hashes. Those discovery-only receipts do not record an exact initial script hash per request; they are supporting routing evidence, and no passing legal-content result depends solely on a route page. Primary API and native-export transport receipts retain runtime and executed script hashes.
