# eCode360 current-source E2E handoff — 2026-10-15

**All 14 current eCode jurisdictions passed a bounded supported-CUA acquisition → retained exact source → delivered importer → parser → CSV/JSON export run.** These current samples contain **134 records**: 115 across the baseline 12, plus Foster City 7 and newly migrated SeaTac 12. Every sample's on-page TOC matched its parsed records, and every exported body matched retained source text under the documented whitespace comparison. No publication-wide inventory or full corpus collection is claimed.

The runtime distinction is material. Ordinary Python HTTP acquisition returned **403 for all 14 current chapter URLs**. A fresh isolated standalone Python/Playwright Chrome attempt on Foster City also returned **403 / “Just a moment…”**; standalone browser acquisition was not run for the other 13. **The successful live acquisition runtime was supported Codex CUA using Chrome**, through the delivered `acquire_cua.mjs` module. No challenges were solved, automation hidden, TLS weakened, or user browser profile copied.

`E2E-VALIDATION.json` is the authoritative current 14-city result, with explicit direct-HTTP, standalone-browser and supported-CUA statuses per jurisdiction, exact source/receipt/output hashes, parser counts, script revisions and blockers. `VALIDATION-REPORT.json` is an identical convenient alias. `live/final-replay/summary.json` records the executed offline replay of all 14 newly acquired current sources. The replay is reproducible but is not itself a second live acquisition.

## Install and verify

Copy this entire directory. Python 3.9+ is required; Node 20+ is needed for the CUA acquisition regression suite. No project database, credentials, original cache or undocumented project imports are required.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m unittest -v test_ecode360.py test_e2e.py
node test_capture.mjs
.venv/bin/python verify_e2e.py --out replay-check
.venv/bin/python validate_local.py --verify-bundle
```

Executed results: **26 Python tests passed; 11 Node acquisition checks passed; 14 current sources replayed into 134 records with zero unresolved nodes/errors.** `verify_e2e.py` requires a fresh empty output directory and performs no network requests. It verifies the current retained source receipts, builds explicit bounded inventories, imports source documents and writes reviewable exports. The original tested environment was Python 3.9.6 on macOS arm64, requests 2.32.5, beautifulsoup4 4.15.0, Playwright 1.60.0 and Node 24.19.0; exact details are in `live/environment.json` and `live/node-version.txt`. That Python build emitted an urllib3/LibreSSL compatibility warning. Use a supported Python/OpenSSL build for deployment.

## Repeat supported live acquisition

Use the supported CUA runtime for browser work. Import the local module in `cua_repl`, use an isolated task tab/session, and replace the package/output placeholders with your copied directory. The numeric browser ID is obtained from the currently available browser inventory; the session used here was Chrome ID `3`, which is not assumed to be stable elsewhere.

```js
var ecModule = await import('file:///ABSOLUTE-PACKAGE-PATH/acquire_cua.mjs');
var ecAcquirer = await ecModule.createAcquirer(
  cua, '/ABSOLUTE-OUTPUT-PATH', 'https://ecode360.com/51404426',
  {browserId:'CURRENT-BROWSER-ID',sessionName:'📜 eCode qualification'}
);
var ecResult = await ecModule.captureJob(ecAcquirer, {
  slug:'foster-city-ca', id:'unique-attempt-id',
  url:'https://ecode360.com/51404426', kind:'legal',
  expected_node_id:'51404426',
  expected_identity:{customer_id:'FO4449',code_id:'337727',currency_raw:'2026-01-26'}
});
nodeRepl.write(ecResult);
```

Verify the currently reviewed source version before repeating the example; the example identity is the exact version observed on the validation date. Set the expected customer identity and requested source node from observed source navigation. `current-routes.json` lists all 14 bounded chapter URLs and route-discovery basis. End with `await ecModule.closeAcquirer(ecAcquirer)` when the task tab is no longer needed.

The default capture is the exact observed `#codeContent` subtree: it contains the on-page TOC and legal bodies. It is **not a full-document archive**. Optional `capture_selector:'html'` saves full document `outerHTML`; Foster City and Santa Clara have accepted full-DOM sources from the executed earlier revisions. The receipt states scope, raw bytes, UTF-16 length, requested heading/node readiness, customer/code/date identity, start/end SHA-256, source URL, UTC times, fresh AX evidence and exact acquisition/checksum module hashes.

Source subtrees up to 120,000 UTF-16 characters are transferred in one atomic read. Larger captures use bounded chunks joined in memory before one UTF-8 write, preserving surrogate pairs. A self-contained SHA-256 implementation runs inside the read-only DOM evaluator because WebCrypto is unavailable there. The saved bytes must match the browser's SHA-256 before and after capture. Size/truncation, navigation, readiness, source mutation and scope/version failures produce rejected receipts. A changed live DOM is not accepted by merely matching its length.

Early navigation often returned server markup while source widgets were still hydrating. Those captures were rejected and retained. Subsequent captures of the already loaded page were accepted only when exact content and identity were stable. This settling work did not repeat blocked HTTP requests or interact with challenges. When a capture is rejected, inspect the receipt and current state before deciding whether a further bounded capture is justified; do not loop through challenged URLs.

Accepted output pairs are immutable. Repeating the exact job/script/raw binding verifies and reuses the retained capture without browser reads. Changing the job, script or retained bytes refuses overwrite; use a new attempt ID to preserve evidence. Final guard behavior is regression-tested. The final helper also acquired the actual accepted Malibu sample. Other accepted samples were acquired by earlier executed helper revisions; the **exact bytes of those revisions are retained** at `live/acquisition-script-v*.mjs` and indexed per receipt. They are source evidence, not alternate runnable entrypoints. No claim is made that every city was reacquired with the final revision.

## Import, parse and verify exports

After an accepted capture, the delivered CLI verifies all receipt/source/start/end SHA bindings before import:

```sh
.venv/bin/python ingest_cua.py \
  --receipt /ABSOLUTE-OUTPUT-PATH/foster-city-ca/unique-attempt-id.receipt.json \
  --jurisdiction 'Foster City' --out run-foster
```

For subtree captures, the raw exact source is retained separately as `retained-source.html`. The importer assembles an explicitly identified document wrapper from observed title, canonical source URL and publisher identity; this is `source-document.html`. It copies the source receipt and imports the wrapped document via `ecode360.py import-snapshot`, then replays the parser against a separate bounded on-page TOC inventory. Full-DOM captures do not require that wrapper. The E2E result includes both raw-source and imported-document hashes, so source bytes and assembled metadata cannot be confused.

Each run writes 16-column contract JSON/CSV full-text and blank-text TOC pairs at aggregate and per-publication paths; CSV uses a UTF-8 BOM and is compared with JSON. It also writes publications, source nodes, dispositions, raw-origin/semantic provenance, exceptions, checkpoint, run manifest and validation report. All outputs remain `validation_sample`, `release_eligible:false`, `full_collection_verified:false`. `replay --release` refuses publication. See the preserved v1 README for the complete contract and general CLI reference; its old coverage statements are historical.

Source identity is jurisdiction + publication ID + publisher node ID; printed citation text never deduplicates distinct nodes. Repeated copies of one node merge origins; conflicting bodies fail. Exact header/body matching prevents navigation or neighboring bodies from becoming legal records. Parent-owned and unnumbered operative bodies are supported. The live Foster source exposed an extra wrapper around list labels: v1's direct-child lookup lost the A.–J. labels. Parser `ecode360-e2e-1.1.0` resolves each label/content pair within its nearest owning list item. Current Foster source regression and all-body source comparisons now pass.

The independent text comparison removes whitespace from source and exported Unicode text, excludes nonlegal UI/script elements, and represents source images by the same ordered marker/alt text. It therefore detects omitted/duplicated legal text and list markers while allowing layout whitespace differences. Separate semantic regressions cover nested lists, superscripts/subscripts, merged tables and image order. Tables retain native row/cell markup, rowspan/colspan and headings; source image meaning is not transcribed. Source-sensitive human visual review remains outstanding.

## Standalone runtimes and concrete blockers

```sh
# Ordinary HTTP: blocked requests are retained and return exit status2.
.venv/bin/python ecode360.py fetch https://ecode360.com/51404426 --out run-http

# Optional standalone browser environment. Uses a fresh isolated profile.
.venv/bin/python -m pip install -r requirements-browser.txt
.venv/bin/python acquire_browser.py https://ecode360.com/51404426 \
  --channel chrome --expected-node 51404426 --out run-standalone-browser
```

The standalone test uses the installed official Chrome channel. For a separately installed Playwright Chromium binary, use `--channel chromium` after its normal installation. This package does not bundle a browser, browser session, cookies or credentials. The actual Foster standalone attempt's response, challenge DOM and receipt are retained under `live/standalone-browser/foster-city-ca/`. Ordinary HTTP receipts for the other 13 chapter requests are under `live/standalone-current/`; Foster's one earlier request is under `live/standalone/foster-city-ca/`. These are all failures, not pipeline passes. The other 13 standalone-browser statuses are explicitly `not_run`.

SeaTac's former Code Publishing root explicitly announced migration to `https://ecode360.com/SE4633`. Fresh exact migration source and receipt copied from the sibling agent are in `live/migration-evidence/seatac-wa/`, with origin hashes. The new target root and its observed Title1→chapter route were acquired independently here. SeaTac's current 12 records belong to eCode360; its legacy Code Publishing chapter is separate historical proof. Foster City's 7 records likewise use the current `FO4449` publication.

## Coverage limits and inherited v1 material

This package collects one current bounded chapter/article sample per jurisdiction, plus the SeaTac route root. The 134 records are **not 14 complete municipal codes**. Complete publication families, charters, tables, supplements, attachments, pending amendments, scope exclusions and every-node inventories remain unverified. The source version is stable during each accepted capture; this does not certify stability throughout a future full collection. Current Foster root navigation also exposes an improvement-district code family, which must be scoped independently before collection.

Official municipal route currentness remains distinct from a correct publisher/customer identity. Retained v1 official city links confirm eCode360 for Burlingame, Malibu and Santa Monica. Other official-route gaps remain, including Half Moon Bay's legacy official link reconciliation. Those pages were not refreshed for this E2E phase. SeaTac has additional fresh vendor-migration evidence; this is not an independently refreshed official-city link.

`examples/`, `fixtures/historical/`, `evidence/` and `HISTORICAL-V1-*` preserve prior method-validation evidence. Their original exports/checkpoint/parser bindings remain unchanged and are **historical**, even where the source row count equals a new current sample. `build_report.py`, `prepare_evidence.py` and `validate_local.py` are inherited utilities; use the current `verify_e2e.py` workflow for live-phase evidence. `validate_local.py --verify-bundle` only verifies the new authoritative manifest. The original package outside this directory was preserved.

The final deliverable is a portable current-source qualification package with a proven supported-browser pipeline and explicit standalone access blockers. Production release requires an independently complete inventory, separately authorized full collection, end-of-collection version reconciliation and human review. None is inferred from sample completion.
