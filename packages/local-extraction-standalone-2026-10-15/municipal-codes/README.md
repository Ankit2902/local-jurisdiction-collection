# Municipal.codes standalone acquisition handoff — October15,2026

This new package tests ordinary isolated standalone Chrome and publisher exports. `STANDALONE-VALIDATION.json` is the current report. The copied E2E material below is prior evidence, not a claim that its CUA captures became standalone acquisitions.

| City | Best actual standalone source | Qualified output | Source stability and limitations |
|---|---|---:|---|
| Berkeley | Headed Chrome legal page; also publisher Save→HTML download |10records |Three retained page snapshots match legal bodies/currency; selected HTML export matches1.01.010 body |
| Petaluma | Headed Chrome legal page |10records |Three retained page snapshots match legal bodies/currency; includes separate chapter note |
| Sonoma | Headed Chrome legal page |10records |Three retained page snapshots match legal bodies/currency |
| Bellingham | Initial headed legalstage200+expectednode+savedDOM |13records |Successful single bounded source→parse; export429 and laterlegal429 prevent complete job/endcheck. No further host requests |
| Everett | Headed Chrome publisher Share→Save→WebPageHTML |1record |Actual selected1.01.010 HTML file; export current-through notice matches prior independently retained CUA site-footer. No fresh repeated endcheck |

The standalone programs launched installed Google Chrome155.0.8059.41 through Playwright1.62.1, headed, with new browser processes and fresh contexts. They used no operator actions, CUA profile/cookies, storageState, stealth, CAPTCHA interaction or TLS changes. Earlier headless/HTTP403 results are retained separately. These bounded headed successes do not establish reliable headless/scheduled full-corpus collection.

Direct navigation to the advertised HTML export URL did not produce a qualified download: it returned browser ERR_INVALID_RESPONSE, a challenge or429. The publisher's normal Save UI succeeds for Berkeley and Everett: it generates a blob download after ordinary Share→Save→WebPageHTML clicks. The actual files and browser/version/script/download receipts are under `headed-ui-export/<city>/`. No PDF conversion is involved. PDF/RTF/TXT/printPDF are advertised but untested in this phase; they are not marked rejected formats.

The browser title may name Chapter1.01 even when the saved file contains only selected section1.01.010. The parser verifies actual legal node/body scope, not title. Berkeley's selected download body and displayed edition equal the corresponding fresh chapter source. Whole-code inventories remain independently retained earlier CUA evidence. The prior contemporaneous chapter notice matches the new body notice; the Contents HTML itself has no displayed edition notice.  These new pilots do not qualify a new standalone full inventory. Every export remains incomplete with unresolved inventory dispositions and `whole_corpus_validated:false`.

**Everett currency correction:** the earlier E2E helper's generic footer selector selected an article statutory footnote. `CURRENCY-CORRECTION.json` records the exact old field and raw hashes, the corrected before/after `#site-footer` notices, their equality, and comparison to the new standalone HTML notice (Ordinance4203-26, September16,2026). The sealed E2E package is unchanged. The new helper prefers explicit site footer and requires current-through text; missing notice fails qualification.

## Portable setup and commands

Use Python3.9+, Node20+ and modern npm. The host's npm6 is incompatible with Node24; testing used bundled Playwright1.62.1 via a temporary local symlink that was removed before delivery. A clean installation uses the pinned dependency normally.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
npm install
.venv/bin/python -m unittest -v test_municipal_codes validate_retained validate_live_snapshots test_e2e test_standalone
node test_checksum.mjs
node test_transport_guards.mjs
.venv/bin/python prepare_standalone.py --out review-standalone-exports
.venv/bin/python verify_package.py
```

These are offline tests/replays against the actual retained fresh standalone sources. New output directories are required. The manifests and raw dependencies stay inside this copied package; no original project directory is needed.

For a future authorized live job, review the report's host stop conditions first. The following are exact delivered interfaces, not instructions to immediately retry rate-limited hosts:

```sh
node standalone_acquire.mjs legal-only-plan.json NEW_HEADED_OUTPUT
node standalone_ui_export.mjs ui-export-plan.json NEW_UI_OUTPUT
```

`standalone_acquire.mjs` defaults to page+one advertised HTML endpoint per job; a job's `stages:["page"]` restricts it to legal-page capture. `legal-only-plan.json` records the actual four-city revalidation plan, including the Bellingham attempt that returned429; the retained run is `headed-legal-stable/`. `ui-export-plan.json` records the successful Berkeley/Everett UI download plan. Inputs are actual observed publisher links from fresh `export-discovery/` snapshots. Stop the host on429/challenge; no identity, currency or completion flag may be promoted from that failed response.

`headed-pilot/` retains the initial successful Bellingham page separately from its failed exportstage. `capture-versions/standalone-pilot.mjs` and `standalone-recovery.mjs` retain the exact executed earlier code bytes, with matching receipt hashes. The exact live-executed stable module is retained as `capture-versions/standalone-stable-executed.mjs`; it produced `headed-legal-stable/` and the challenged `headed-difficult/` attempt. The exact successful UI revision is `standalone-ui-executed.mjs` in that same directory. Final transport modules add offline-tested HTTP/blob-origin guards and host-stop/Retry-After recording after these captures; no additional network was performed after hardening. The latter emits no legal records. Publisher download evidence includes actual blob URL, suggested filename, bytes, SHA256, timestamps, browser version and script SHA256.

A human can reproduce the publisher file workflow in an ordinary browser without Codex: open the section's public Share route, select Save, select WebPageHTML and retain the downloaded file. This manual workflow was separately exercised for Berkeley under `operator-downloads/`; its provenance is labelled CUA/operator-assisted and is not counted as the standalone automation success. The successful standalone downloads use the separate Playwright script and receipts.

The older report and README content follows for source/parser background only. Current standalone statuses and the Everett correction above supersede prior runtime/currency claims.

---

# Municipal.codes current acquisition E2E handoff — October 15, 2026

This second package closes the fresh acquisition-to-export gap for all five primary publications using the delivered `acquire_cua.mjs` module and supported Codex browser API. These are fresh URL navigations, retained raw DOM, independent Contents inventories, parser replay and validated contract exports. No old fixture is substituted for live acquisition. `E2E-VALIDATION.json` is the current report; the original report is preserved as `BASELINE-VALIDATION-REPORT.json`.

| City | Fresh primary inventory nodes | Fresh bounded export records | Primary inventory / currency / sampled chapter bodies before-after | Standalone Playwright | Direct HTTP |
|---|---:|---:|---|---|---|
| Berkeley | 5,238 | 25 | Match | HTTP 403 | See fresh receipt |
| Petaluma | 2,860 | 10 | Match | HTTP 403 | See fresh receipt |
| Sonoma | 2,177 | 39 | Match | HTTP 403 | See fresh receipt |
| Bellingham | 2,846 | 18 | Match, distinct postcheck after stale navigation rejection | HTTP 403 | See fresh receipt |
| Everett | 3,742 | 33 | Match | HTTP 403 | See fresh receipt |

The export count includes independent substantive parent bodies where present; it is not the full jurisdiction count. The new real Sonoma appendix type is preserved. Petaluma's BackAppendices page is structural and emits no fake provision. Berkeley and Everett tables retain visible cells, spans and header relationships; duplicate floating table headers explicitly marked aria-hidden are excluded. Bellingham maps retain exact `[IMAGE]` markers, alt text, and source-image URLs in the HTML sidecar. Diagram/map text has not been independently transcribed or OCR-validated; image-bearing provisions require review before corpus completion.

Extra family inventories were captured for Berkeley Charter, Petaluma ZoningOrds/SmartCode/Charter and Everett Charter. Bellingham Charter encountered a challenge and remains blocked; its raw and failed receipt are retained. All extra families still need substantive collection and scope decisions. Whole-corpus inventory classification, attachment handling, official-route gaps and complete body/disposition reconciliation remain release gates. Every generated export says `incomplete_source_validation` and `whole_corpus_validated:false`.

Fresh acquisition is reproducible through two explicitly separate runtimes. CUA-script E2E passed for all five primary codes in the current Codex Chrome session; it requires supported `cua` access and an available browser. The standalone Playwright command actually ran in an isolated installed Chrome context for all five and returned HTTP 403; it is delivered and tested fail-closed, but unattended acquisition has not passed. No CAPTCHA solving, cookie transfer, stealth, TLS override or access-control bypass was used.

## Exact current commands

Use Python 3.9+ and modern Node 20+ with current npm. Install `requirements.txt` in a venv; `npm install` installs the pinned Playwright 1.62.1 dependency. For Playwright's bundled Chromium, run `npx playwright install chromium`; the tested host command instead selected installed Google Chrome using `BROWSER_CHANNEL=chrome`. The host's old npm 6 failed against Node 24; the actual test used its existing bundled Playwright 1.62.1, recorded in the report. That local dependency shortcut is not needed by these portable commands.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
npm install
.venv/bin/python -m unittest -v test_municipal_codes validate_retained validate_live_snapshots test_e2e
node test_checksum.mjs
.venv/bin/python prepare_e2e.py --source live-final --out review-exports
.venv/bin/python verify_package.py
```

Use a NEW output directory for replay/build and live attempts. A repeated live CUA receipt path is refused before navigation; preserve failed attempts with a new run directory or distinct job id. The optional commands below perform only five bounded chapter probes:

```sh
NODE_BINARY=node .venv/bin/python run_standalone_validation.py review-standalone
.venv/bin/python run_http_validation.py review-http
HEADLESS=1 BROWSER_CHANNEL=chrome node browser_capture.mjs \
  https://berkeley.municipal.codes/BMC/1.01.010 review-single section 1.01.010
```

For supported CUA acquisition, run the following in Codex `cua_repl`, after its documented entry-point setup and browser selection. `packageRoot` is the absolute path of THIS copied package; choose a browser ID from a fresh `cua.getState()` inventory, not a hardcoded browser from this run. This script opens and closes only its own tab. CUA does not provide response HTTP status, so receipts leave `http_status:null`.

```js
let mcFs = await import('node:fs/promises');
let mcUrl = await import('node:url');
let packageRoot = '/absolute/path/to/municipal-codes';
let mcModule = await import(mcUrl.pathToFileURL(packageRoot+'/acquire_cua.mjs').href);
let mcPlan = JSON.parse(await mcFs.readFile(packageRoot+'/e2e-plan.json','utf8'));
let mcCapture = await mcModule.createAcquirer(cua, packageRoot+'/new-live-run',
  mcPlan.jobs[0].url, {browserId:'ID_FROM_FRESH_INVENTORY', sessionName:'🏛 Municipal codes'});
// Execute in batches of 1-2 jobs in tool calls of at most 60 seconds.
await mcModule.captureJob(mcCapture, mcPlan.jobs[0]);
// Continue observed jobs from mcPlan.jobs. Inspect each returned accepted flag.
// After each city's inventory-after, repeat its chapter job with id:'version-after'.
// A rejected job remains rejected: new attempts require distinct ids/directories.
await mcModule.closeAcquirer(mcCapture);
```

Each CUA receipt binds its job, module/helper SHA256, raw file SHA256, whole-DOM browser SHA256 before and after capture, timestamp, final URL, content identity, readiness errors and fresh accessibility state. DOM chunks join before UTF8 encoding, preserving surrogate pairs. Changes during capture, source mismatches and stale navigation are rejected. `capture-versions/acquire_cua-v6.mjs` preserves the exact earlier tested module bytes; final module v7 adds only immutable receipt refusal. Receipts identify which module acquired each raw source. `live-run` is earlier exploratory acquisition and is excluded from E2E pass claims.

`prepare_e2e.py` verifies accepted raw checksums and browser before/after checksums, compares independent before/after ordered inventories, displayed currency and sampled chapter body hashes, builds a version-bound manifest and invokes the delivered replay function. Self-contained `e2e-exports/<city>/inputs/manifest.json` files can be replayed after copying the package; no original workspace path is required. Output sources and records are hashed; all unmatched inventory nodes remain unresolved. A successful bounded replay does not promote inventory completeness or whole-corpus status.

The section below preserves baseline context and commands; its one-chapter counts describe the earlier phase only. The table and E2E report above supersede those counts for this package.

---

# Municipal.codes source-validation handoff — October 15, 2026

This self-contained package delivers a runnable bounded acquisition/parser/replay path for Berkeley, Petaluma, Sonoma, Bellingham and Everett. It fixes the `/contents` boundary defect and unsafe Contents-as-provision fallback, parses stable section-card identities, preserves separate parent text, retains semantic HTML, and refuses stale or mismatched checkpoints. No production adapter, database, import or full-corpus collection was changed or run.

The parser is validated against real August 28 cached HTML **and current October 15 rendered chapter DOM for all five cities**. The current primary-code Contents trees are independently retained with 16,863 nodes total. Those are navigation/source nodes, not a provision count. Only one representative chapter per city was acquired for text validation: 54 section cards and two chapter note bodies. Every unacquired node remains unresolved in the example exports.

| Jurisdiction | Current primary-code inventory nodes | Chapter 1.01 section cards | Additional retained chapter body | Whole corpus |
|---|---:|---:|---|---|
| Berkeley | 5,238 | 10 | None | Unvalidated |
| Petaluma | 2,860 | 9 | Editorial/statutory note; scope review pending | Unvalidated |
| Sonoma | 2,177 | 10 | None | Unvalidated |
| Bellingham | 2,846 | 13 | None | Unvalidated |
| Everett | 3,742 | 12 | Editorial/statutory note; scope review pending | Unvalidated |

`VALIDATION-REPORT.json` separates official route evidence, browser reachability, representative parser checks, primary-code inventory capture and whole-corpus qualification. It includes relative evidence paths and SHA-256 hashes. Its limitations are release gates, not successful production-readiness claims.

## Run from a clean machine

Python 3.9+ is required; a modern Python 3.11+ with an up-to-date TLS trust store is preferable. The Python scripts use only standard-library modules plus `requests` and `beautifulsoup4`.

```sh
cd /path/to/municipal-codes
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m unittest -v test_municipal_codes validate_retained validate_live_snapshots
.venv/bin/python municipal_codes_cli.py --help
```

All paths needed for replay are contained here. Original project cache paths in the retained-fixture manifest are provenance labels; the scripts never read them. The historical cache could overwrite a URL file in place; copied byte hashes are authoritative. The overwritten Everett Contents shell is retained as a negative fixture and never substituted for a current inventory.

Replay one actual current snapshot into a **new** output folder:

```sh
.venv/bin/python municipal_codes_cli.py replay \
  --manifest evidence/berkeley-ca/replay-manifest.json \
  --out /tmp/municipal-berkeley-review
```

An intentional interruption and resume use the same manifest and destination:

```sh
.venv/bin/python municipal_codes_cli.py replay \
  --manifest evidence/berkeley-ca/replay-manifest.json \
  --out /tmp/municipal-berkeley-resume --stop-after 1
.venv/bin/python municipal_codes_cli.py replay \
  --manifest evidence/berkeley-ca/replay-manifest.json \
  --out /tmp/municipal-berkeley-resume
```

The shipped real manifests each acquire only one chapter. The synthetic two-snapshot regression proves interruption/resume and bundle deduplication across multiple acquisitions. Changing the jurisdiction, publication, version, manifest/config, inventory hash, parser bytes or acquired snapshot bindings rejects the old checkpoint. Raw hashes are rechecked on every resume, including already processed artifacts. A changed body for one source identity raises a conflict instead of silently selecting one version.

`build_examples.py` regenerates the five bounded review packages in `examples/` solely from retained evidence. It deliberately honors checkpoint mismatch failures. Use a fresh copy of this package or a new output path after changing the parser; never delete a live-run checkpoint just to conceal a mismatch. `examples/*` contains the contract-shaped CSV/JSON fulltext and derived TOC, independent source-node inventory, one disposition per inventoried node, provenance, exceptions, immutable raw artifacts and run hashes. Their metadata always says `incomplete_source_validation` and `whole_corpus_validated: false`. The derived TOC is not the independent inventory.

## Acquisition and inventory

The direct HTTP acquisition command fetches one approved URL, records redirect/HTTP/header/hash receipts, retains failed responses and retries only bounded 429/503 responses. TLS checks stay enabled. All five direct discovery requests returned HTTP 403 during this run. That did **not** establish a browser block: the supported Codex in-app browser successfully rendered all five chapters and primary-code Contents trees after ordinary readiness checks. No CAPTCHA, access-control bypass or challenge automation was used.

```sh
.venv/bin/python municipal_codes_cli.py routes --out /tmp/municipal-routes.json
.venv/bin/python municipal_codes_cli.py acquire --slug berkeley-ca \
  --discovery --out /tmp/municipal-berkeley-direct
```

`browser_capture.mjs` is an optional standalone visible-browser capture helper. It starts its own Chromium/context and does not attach to or modify an existing user browser. It is syntax-checked, but its Playwright transport was **not live-qualified in this run**; live evidence was acquired with Codex CUA/IAB. Install dependencies through their ordinary package/vendor distribution:

```sh
npm install playwright
npx playwright install chromium
node browser_capture.mjs https://berkeley.municipal.codes/BMC/1.01.010 \
  /tmp/municipal-browser-section section 1.01.010
node browser_capture.mjs https://berkeley.municipal.codes/BMC/contents \
  /tmp/municipal-browser-inventory inventory 'main > ul.contents-toc'
```

Node.js 20+ is required for this optional helper. Older `node` binaries cannot parse the ES module. The section command requires an observed card ID; it never infers readiness from page title alone. Inventory selection must be an observed TOC container and does not claim lazy branches are complete. Access challenge/error receipts stop the command with a nonzero exit. If ordinary access requires operator interaction, retain the block and use the supported operator/browser route; this package does not solve challenges.

For an existing captured DOM:

```sh
.venv/bin/python municipal_codes_cli.py inventory \
  --html evidence/berkeley-ca/live-contents-full.html \
  --url https://berkeley.municipal.codes/BMC/contents \
  --base https://berkeley.municipal.codes/BMC \
  --selector 'main > ul.contents-toc' --out /tmp/berkeley-inventory.json
```

A `/contents` URL is discovery only. The independent base is `/BMC`, `/EMC`, `/SMC` or `/Code` as observed. The validator rejects another publication on the same host, near-prefix lookalikes, query routes and path traversal. It does not crawl cross-reference/history/search/share links as provisions.

The live DOM bridge truncated large single-return strings near 200,000 characters. The early `live-contents.html`/`live-contents-ready.html` files are retained as rejected acquisition evidence. **Use `live-contents-full.html` only**: it was captured in 50,000-character chunks, and its UTF-16 length and TOC link count were checked against the browser. Full-document captures missing `</html>` are rejected. All five full snapshots now match their independently observed browser link counts exactly.

## Source identity and fidelity

Cards are individual `article.type-Section` nodes. Observed DOM IDs/data IDs and `data-history` routes determine identity. Chapter identities can use their observed header share URL. Data IDs without a real HTML ID do not invent browser anchors. Printed section numbers are display values; two different source identities with the same citation survive. Duplicate acquisitions of a chapter through section/chapter URLs produce one record per stable identity; every acquisition remains in provenance.

The parser removes actual observed publisher action menus, selection indicators and local TOC markup. It serializes the remaining semantic container once, preserving nested lists, table headers/cells/spans, superscript/subscript, footnotes/history, cross-reference text/links and ordered exact `[IMAGE]` placeholders with alt text following the placeholder. Semantic HTML remains in provenance; tables/lists are represented as HTML in `full_text` so structure survives the 16-field legacy envelope. No image OCR or legal transcription is inferred.

Parent `Title`, `Chapter`, `Article`, `Part`, `Subtitle`, `Subchapter`, `Appendix` and `Division` articles have an explicit own-body path: descendants and navigation are removed before testing their body. The Petaluma and Everett chapter footnotes survive separately. Their operative/editorial scope remains subject to review; the complete source is retained and no note is silently discarded. Unknown article types or unprofiled `main` text become unresolved. A heading alone never authorizes a provision.

## Remaining release work

- Resolve current official-city publisher-link provenance where blocked. Berkeley's city landing explicitly links Municipal.codes. Sonoma's city CivicWeb landing links the legacy Code Publishing URL; its HTTPS destination returned 403, so the live Municipal.codes route is reachable but its present official redirect chain remains unconfirmed. The sampled Petaluma, Bellingham and Everett city landing pages returned 403.
- Review all discovered publication families. Berkeley, Bellingham and Everett expose Charters. Petaluma also exposes Zoning Code, SmartCode and Charter. Sonoma's sampled root exposes Municipal Code. Family identities and unresolved scope decisions are retained in `publications-discovery.json`; the five main-code trees do not prove those additional families complete.
- Freeze/reconcile start and end inventories and publication currency for any full run. A snapshot hash and retrieval date are acquisition identity, not legal current-through dates. Raw publisher currency is retained separately; this bounded run does not establish a coherent whole-publication revision.
- Acquire and account for the unresolved source nodes, review structural/editorial/reserved/scope decisions with evidence, and qualify difficult real tables, appendices, long/nested sections and diagrams beyond Chapter 1.01. Rich semantic cases currently have meaningful synthetic regressions; they are not a claim that all real platform variants were reviewed.
- Independently review representative rendered sections and family scope, then perform full clean/interrupted source replay before downstream use. The scripts intentionally have no production-complete switch.

Verify the frozen delivered files with `python verify_package.py`. `SHA256SUMS` also includes the validation report itself. To refresh the report after an intentional local code/evidence change, complete example regeneration and the test command first, save its output to `evidence/tests.log`, then run `python build_validation_report.py`. This refresh records new hashes and does not upgrade any corpus readiness status.
