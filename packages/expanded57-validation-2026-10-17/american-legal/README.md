# American Legal — bounded standalone acquisition validation

This package tests public American Legal pages for 11 proposed jurisdictions. It is a bounded transport, parser and normalization validation. It is **not a complete collection of any jurisdiction**, and a successful code sample does not qualify a separate charter, zoning code, resolutions collection, uncodified ordinances, maps, incorporated standards or other publication.

The scripts use normal installed Google Chrome through Playwright, and Python to replay retained HTML. They use no Codex or CUA runtime. Setup after copying this whole directory:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
npm install
node scripts/collect.mjs --out fresh-run-dallas --sequence 4
.venv/bin/python fresh-run-dallas/scripts/parse_verify.py --offline --sequence 4
```

Omit `--sequence` to process the 11 assignment rows serially. `--out` is required and must name a directory that does not exist; the collector creates a portable copy of scripts/configuration there and acquires fresh source and publisher bytes. Previously resolved public sample routes are in `routes.json`; overview/tree discovery evidence is retained in this package. A publisher revision can invalidate a route and requires rediscovery, rather than guessing an identifier. A visible Google Chrome installation is expected (`channel: chrome`). `BROWSER_CHANNEL` can select another installed Playwright-compatible channel. The live run used macOS 26.6.2 arm64, Node v24.19.0, Playwright 1.62.1 and Google Chrome 155.0.8059.84. Python replay used 3.9.6. See `research/runtime.json`.

Offline verification (no browser, network or Codex):

```sh
.venv/bin/python scripts/parse_verify.py --offline
```

The parser checks retained acquisition hashes, produces `parsed/<publisher-slug>/records.jsonl` and CSV for rendered content, and separately produces `publisher-records.jsonl` and CSV for genuine publisher HTML downloads. `verification.json` records actual record and table counts. Raw rendered HTML, native downloaded HTML, native export selection/format evidence and acquisition request metadata are under `raw/`.

`collect.mjs` creates a fresh output directory and runs `request_exports.mjs`. The latter follows public TOC links when necessary, scrolls a bounded sample, retains rendered source HTML, then uses a substantive section's own **Download → Save HTML** control. The website queues an export and supplies an OPEN link. The script waits for that exact newly created export UUID and captures an ordinary browser download event. When the publisher queue is full, it uses the documented Continue control to remove the oldest queued export before proceeding. This matters because a page can retain previous exports in its list. `publisher_export` receipts identify actual file/byte hashes and `publisher-scope.json` identifies actual source headings. Browser print-to-PDF is not used.

The initial live discovery source is preserved by hash under `scripts/executed/`. `scripts/download_exports.mjs` is a tested recovery method for already-created export jobs; `scripts/expand_samples.mjs` is a separate bounded TOC/scroll utility. The final fresh collector uses the combined requester rather than relying on a stale export-list link.

The tested renderer loads a bounded initial set of source sections; it can leave later chapter sections unrendered. The initial native export selection followed the currently active section when a parent checkbox was in a mixed state; the final requester selects a substantive section control explicitly. Actual retained publisher records, rather than the parent division label, define the successful export's scope. No whole-code export is claimed. General-provisions samples may contain no substantive tables. A separate Colorado Springs UDC §7.4.201 sample validates operative table cell text and span metadata; that bounded layout check does not qualify tables throughout every code. Its records are in `table-records.jsonl`, separately from general-provisions records. `table_sample.mjs` reruns that acquisition against an existing Colorado Springs raw directory.

Ordinary urllib requests to the American Legal overview and to a native export link returned 403. Those HTTP outcomes are not portable HTTP successes. Ordinary headed Chrome accessed public content and native downloads without solving a challenge. Earlier development attempts and a closed browser session are retained under `research/early-attempt-raw/` and `research/browser-closed-failure.log`. `scripts/executed/` preserves exact versions used for acquisition hashes when scripts were subsequently refined.

`research/publication-inventory.json` lists independently published and embedded families, with explicit untested scope. `research/official-routes/` retains routing-page responses; some official sites returned 403, and those failures remain evidence. Boston zoning is a separate Municode publication linked from the official Planning Department. Dallas Chapter 51P is separately routed by the city. Louisville's Land Development Code and Sacramento resolutions have separate publisher entries. None is silently included in a successful main-code sample.

The collector spaces explicit navigations/actions by at least 3.5 seconds. Website asset requests, its export polling and its normal lazy section rendering occur under the website's own application behavior. Do not run multiple collectors concurrently against the publisher. Stop on 403, 429 or an access challenge; honor Retry-After and do not solve or bypass challenges, rotate proxies, or assume a native download URL is permanent.

To turn this into whole-publication ingestion, the technical team must replace the bounded sample/scroll loop with an inventory-driven traversal of every document in each independently published code. Maintain stable publisher document IDs and parent paths, follow every observed child/next-document route once, wait for every lazy-rendered section, and reconcile expected TOC leaf IDs against acquired, parsed, duplicate, failed and intentionally excluded IDs. Treat a native whole-publication export as a separate operation whose available scope and size must be tested; these runs exported individual operative sections. Preserve images, tables, footnotes and cross-publication references, validate table spans and representative difficult layouts, and reconcile supplement/version metadata and pending legislation. Publish completeness only after all independently listed families and leaf counts have been reconciled. Full traversal, revision-safe resume, whole-code exports and whole-jurisdiction completeness have not been validated here.

Honolulu's title-only first article is too small to exercise multiple section records. Its full tested rerun recipe adds an observed penalties-and-interest article before offline replay:

```sh
node scripts/collect.mjs --out fresh-run-honolulu --sequence 57
node fresh-run-honolulu/scripts/additional_sample.mjs
.venv/bin/python fresh-run-honolulu/scripts/parse_verify.py --offline --sequence 57
```

Publisher HTML export success remains bound to the specifically requested operative section; the additional article is a separate rendered-source sample. The Colorado Springs table check preserves raw DOM table rows/cells and `rowspan`/`colspan` values. It does not infer or qualify a reconstructed semantic grid or treat repeated DOM table headers as unique legal tables.
