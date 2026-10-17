# enCodePlus wave 3: Lincoln and Overland Park

Both assigned jurisdictions passed a **bounded standalone HTTP acquisition → parse → JSONL/CSV** validation on October 17, 2026. This package contains exactly two result rows (sequences 67 and 82), six operative provision records, two substantive legal tables and genuine publisher-native section PDFs. It does **not** establish a complete jurisdiction corpus, complete code ingestion, or legal currency for the whole code.

| Jurisdiction | Tested provision IDs | Inventory | Table evidence | Native export |
|---|---|---:|---|---|
| Lincoln, NE | 6288, 6289, 12858 | 4,784 unique flat TOC IDs | 20.12.140 climatic/geographic design criteria: 4 rows, 20 cells | 1 page, selected provision |
| Overland Park, KS | 3, 4, 6155 | 4,381 unique flat TOC IDs | 18.430.150 required parking: 13 rows, 29 cells | 2 pages, selected provision |

A record is one requested leaf operative provision. Container text and descendant records are not counted as additional records. The first two records in each city are general code provisions; the third is an actual legal table. See `results.json`, `verification.json` and the per-run receipts for measured checks. The `-v2` folders contain the successful primary samples. Earlier development/failure evidence remains separate.

## Setup and independent offline verification

Tested runtime: Python 3.12.14, macOS 26.6.2, arm64. No Codex, browser, existing user profile, imported cookies or credentials are required. The HTTP gate uses POSIX `fcntl.flock`; Linux compatibility is expected but was **not live tested**. Native PDF checks use pypdf; optional page rendering uses pypdfium2 and Pillow.

Run from the relocated package root:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python scripts/verify.py
```

`requirements-lock.txt` retains the entire tested environment, including incidental PDF inspection packages. `requirements.txt` pins the dependencies actually used by the supplied workflows. The original dedicated `.venv` is retained locally for root independent verification and excluded from the portable manifest/Git handoff. Its tested interpreter is `outputs/wave3-validation-2026-10-17/encodeplus/.venv/bin/python` under the authoritative project root.

`verify.py` uses **no network** and writes only to a system temporary directory. It checks every retained HTTP response against its receipt, every hash-named script snapshot, TOC identity/inventory reconstruction, requested section identity and heading, two independent table text/row/span representations, complete normalized JSONL/CSV byte equality, native PDF identity and table anchors, result evidence paths, and the package manifest when present. It prints deterministic JSON to stdout. It does not rewrite the sealed raw files, normalized outputs, receipts, QA reports or manifest. The stored `verification.json` is a pre-seal run of that command. `acquire.py --offline` is a development facility that writes derived files; use `verify.py` for routine sealed-package replay.

## Fresh live acquisition and publisher downloads

The following commands were exercised in this package; replace the sample output paths with **new, unpopulated** paths. All source requests are serial and pass through a cross-process 3.5-second gate. Concurrent enCodePlus collectors must retain the same `ENCODEPLUS_GATE_DIR` (default `/tmp/compliSolv-encodeplus-rate-gate`). The transport persists HTTP429 cooldown, honors Retry-After with a minimum300 seconds, keeps failure bytes and receipts, and does not retry automatically or rotate identities. Stop on a challenge or rate-limit response and coordinate with other collectors.

```sh
.venv/bin/python scripts/acquire.py lincoln --out /tmp/encodeplus-new-lincoln
.venv/bin/python scripts/native_export.py /tmp/encodeplus-new-lincoln/publisher-table-export.pdf --out /tmp/encodeplus-new-lincoln-native
.venv/bin/python scripts/pdf_qa.py lincoln /tmp/encodeplus-new-lincoln-native

.venv/bin/python scripts/acquire.py overland --out /tmp/encodeplus-new-overland
.venv/bin/python scripts/native_export.py /tmp/encodeplus-new-overland/publisher-table-export.pdf --out /tmp/encodeplus-new-overland-native
.venv/bin/python scripts/pdf_qa.py overland /tmp/encodeplus-new-overland-native
```

The apparently named `publisher-table-export.pdf` created by the first command is deliberately preserved **HTML status-page evidence, not a PDF**. The original collector stopped its PDF check there and recorded that stage as blocked. The independently executed `native_export.py` continuation resolves the normal frontend flow: read the status page's observed `$.get(...)` polling URL, fetch its public JSON, wait at most three bounded polls if needed, and append its returned File token to the original export URL. Final native evidence lives in `native/*-qualified/publisher.pdf`; the separate `export.json` and `qa.json` establish the successful download. The aggregate results reflect that later success without rewriting the original run report. These PDFs are publisher-generated Aspose.Words exports of **one selected provision each**, not browser print output or whole-code exports.

Each live acquisition snapshots the exact executed source bytes before requesting data, keyed by SHA256 in its own `script-versions/`. `run.json`, `.command.json` and `.receipt.json` retain exact commands, runtime/OS, URLs, acquisition timestamps, response headers, hashes and sizes. Historical command paths may describe the acquisition machine; runnable scripts resolve package resources relative to themselves. `fetch_one.py` provides the same provenance for the discrete discovery/export experiments. Script snapshots are evidence; ordinary use invokes the named copies under `scripts/`.

## Source contracts and meaningful checks

The JS viewer shell (`doc-viewer.aspx`) is not an operative record. The observed public application code in `platform/js-doc-view.js` uses `doc-view.aspx?secid=<observed ID>&ajax=0`; those server-rendered responses contain the legal text. The collector first obtains an independent complete TOC page, checks publication identity, selects IDs already observed in that TOC, and requests only those sections. It asserts `#thePage/@secid`, exactly one matching `section[data-secid]`, absence of nested provision ownership, and exact TOC/body heading equality before normalization.

The parser preserves operative text, heading/citation, canonical body breadcrumbs, full section HTML, body HTML, list counts, anchor attributes and links, section histories, and source hashes. Table cells retain text, th/td, row/col spans and serialized cell HTML, including superscripts. An independent BeautifulSoup traversal compares every cell's text and spans with the stdlib HTMLParser representation: 20 Lincoln cells and29 Overland cells, all matching. Superscript boundaries initially fused text in a development parser; the failed comparison and old script snapshot are retained, and the fixed parser passed fresh source acquisition. Lincoln's two linked legal cross-references are resolved by section ID; Overland's plain-text citations remain text and are not falsely counted as resolved links. No full reference closure is claimed.

The PDF QA checks exact publication metadata, the provision heading and representative table/history anchors against the HTML sample. All three pages were rendered to PNG; Lincoln and Overland first pages were visually reviewed for heading/table layout. Lincoln shows25psf,115mph,36-inch frost depth and the source's70°F value; the collector preserves that source value as published. Overland's table continues across two native PDF pages. The PDFs match sampled identity/content anchors; this does not prove codewide edition parity or pixelwise table equivalence.

Lincoln's publisher TOC contains **547 declared-depth gaps**. The4,784 unique flat IDs are retained. Parent/path assignments from TOC depth are explicitly best effort and `hierarchy_complete=false`; successful record paths instead use the response's canonical breadcrumbs. The original strict-depth failure remains in `live/lincoln/`. Overland's4,381-node TOC has no detected depth gaps. Its first candidate DFD802 Use Table is an image-only PNG, so it failed the HTMLtable check and remains in `live/overland/`; the successful replacement is the actual required-parking HTMLtable.

Publisher `.archiveNotice.nullValue` metadata is excluded from operative body/date claims with explicit per-record dispositions. Overland's “Effective on1/1/1901” is such a sentinel and is **not** represented as legal currency. Empty Lincoln nullValue notices are likewise excluded. Original bytes and section HTML retain evidence of these source fields.

## Publication coverage and edition limits

`publication-inventory.json` retains live navigation links, labels and evidence paths. It is a discovery inventory, not proof of ingestion of each linked family.

Lincoln's primary municipal code is separate from its City Charter, Design Standards and Access Management Policy. The site also links Lancaster County Zoning Regulations and Lancaster County Subdivision Regulations, which belong to a separate county scope, and the joint Lincoln-Lancaster Comprehensive Plan. Those linked families were not acquired/parsed in this bounded validation. The primary code's eReader was inspected; its Download button was hidden and its edition was not established. No guessed hidden PDF path was used. The official Lincoln attorney discovery page returned403 and is retained; the linked publisher route independently served public legal records without a browser or access-challenge interaction.

Overland's primary code TOC includes Title18UDO, charter ordinances, Site Design Standards, Architectural Design Standards, Mixed Use Design Standards and Downtown Form-Based Code. Only two general code provisions and one Title18parking provision were parsed. Governing Body Policies and the Comprehensive Plan are separately published. The live Documents page links STO and UPOC editions labeled **effective10/2/2026**, with distinct prior editions; these separate incorporated documents were inventoried but not downloaded. Infrastructure manuals, referenced model building codes, external plans and images are additional gaps. The official UDO update page describes work extending throughSpring2027 and does not establish an adopted replacement edition.

No global current-through date was established for either code from the inspected About pages/TOCs. The Lincoln sampled table carries Ordinance21820, December15,2025 and an older2020history; Overland's table includes ZRR-3503 and ZRR-3373/2023history. These are section histories, not whole-code currency claims. Discovery HTML, current labels, original failure evidence, and exact native export responses are retained for review.

## Required change for full ingestion

`acquire.py` is **hardcoded to exactly three provision IDs per target** in `CONFIG`; it is a bounded validator. To build a full collector, replace that selected-ID loop with traversal of all unique observed TOC nodes, classify operative leaf/container/repealed nodes, and qualify container-owned text separately from descendants before relaxing the current no-nested-section assertion. Resolve parentage from canonical response breadcrumbs/observed structure, particularly Lincoln's malformed depth hierarchy, instead of treating the best-effort TOC stack as authoritative. Fetch each eligible node once through the shared gate, record exclusions/failures and source changes, and reconcile acquired IDs against the inventory with explicit ownership/closure checks. Do not assume all TOC leaves are operative or all legal text lives on leaves.

Add explicit image/PDF attachment acquisition and parsing (the retained DFD802negative demonstrates why), preserve model-code/incorporated-document boundaries, collect the separate publications listed above, and compare publication identifiers/current-through histories across exports and online text. Whole-publication export requests and their size/runtime/completeness are **untested**. The portable scripts demonstrate viable acquisition and faithful bounded normalization; full-run coverage, update handling, and complete jurisdiction corpus assembly remain work for the ingestion team.
