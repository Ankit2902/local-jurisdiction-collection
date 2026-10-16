# Code Publishing bounded live acquisition and export handoff

This is the October15 E2E follow-on package. It includes delivered, exercised transports for supported CUA and standalone Python/Playwright, exact live DOM and acquisition receipts, source-observed navigation plans, the bounded parser/export CLI, offline fixtures, tests, and verified current sample exports. No production adapter/database changes or full-corpus extraction/import occurred.

The supported CUA path acquired and parsed **five current Code Publishing municipalities**: Flagstaff, Fremont, San Carlos, Burien and Renton. **SeaTac and Foster City announce migration to eCode360** on the legacy publication landing pages. SeaTac's still-accessible legacy chapter is retained and parsed only as a migrated-vendor sample. Foster municipal extraction is assigned to eCode360; this package inventories its separate Estero Municipal Improvement District scope without extracting that district. Current eCode handoff: sibling `../ecode360/` (use its report for current municipal editions).

`E2E-VALIDATION.json` and `<slug>/E2E-VALIDATION.json` are the current results. Prior `VALIDATION-REPORT.json`, `README-V1.md`, `historical/` and `replay/` are retained earlier-stage/historical evidence and do not override these results. `current-pipeline/<slug>/export/` contains the current generated contract artifacts. `current-cua/` holds complete exact DOM, AX text, receipt hashes, URL/readiness/integrity checks and archived acquisition/checksum module revisions. Earlier `live/*.html` files remain explicitly selected excerpts, not full DOM.

## Results and limits

The current supported-CUA samples contain six numbered chapter documents plus one additional Fremont business-tax chapter and one supplementary cross-reference document. The five current municipalities yield77 records (Flagstaff5, Fremont55, SanCarlos10, Burien6, Renton1); migrated legacySeaTac adds12. Fremont's55 include52 numbered sections, two substantive chapter-history bodies and one unnumbered reference-table body. The current business chapter retains147 complete P0–P3 paragraphs. The reference document has one visible legal table with2212rows/4422cells; three hidden sticky-header clones are excluded. Raw DOM contains four tables, and the audit records both denominators. Live row/column-span, image, superscript and nested-list examples were not found in these bounded documents; synthetic fixtures separately test those structures.

All six standalone Playwright chapter requests returned HTTP403 challenge pages in a fresh isolated Chrome context. Those pages are retained and **not accepted or parsed**. A final guarded-script trial also records its actual result separately. Ordinary Python HTTP trials for Flagstaff and Fremont chapters returned403; earlier root probes for all seven also returned403. No challenges, security interstitials, cookies, user profiles or TLS controls were bypassed. Supported CUA uses the connected browser's normal session and was actually executed through the delivered module; it is not evidence of standalone CLI network success.

Live currency markers match before/after each bounded legal capture, including explicit Flagstaff disclaimer bracketing. This establishes observed label stability for the samples; the publisher offers no immutable edition token here. Publication inventory is **incomplete**: each root inventory retains observed title/family/reference/PDF links, but other chapters, unlinked repealed/reserved entries, supplements, incorporated documents, PDF contents and images need fuller scoped qualification. No whole-corpus or production-ready claim is made.

## Dependencies and offline commands

Use Python3.9+ (3.10+ with OpenSSL recommended for HTTPS), Node20+ for module tests, and optionally Playwright1.60.0 plus an installed Chrome channel for standalone acquisition. Node built-ins suffice for the CUA module. There are no hidden absolute runtime dependencies; paths below are relative to this copied package. The test environment's Python3.9/LibreSSL warning is retained in logs; certificate verification stayed enabled.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m unittest discover -s . -p 'test_*.py' -v
node test_acquire_cua.mjs
.venv/bin/python validate_e2e.py --captures current-cua --out work/reproduced-current
.venv/bin/python verify_package.py
```

Windows uses `.venv\Scripts\python.exe`. The verification runner checks accepted receipts, exact raw hashes against browser-before/after SHA256 and archived script sources; then invokes `cp_collect.py acquire`, interrupted/resumed `replay`, and clean `replay`. It compares source CiteTOC IDs/order and all complete publisher P-level paragraphs, visible table/list/cell/span signatures, human publication names/hierarchy, CSV/JSON equality, and resumed/clean bytes. The Fremont three-document sample exercises restart between real current documents. `current-pipeline/<slug>/commands.json` records actual executable paths/argv/returncodes/stdout/stderr; these are execution evidence, not hardcoded dependencies.

`cp_collect.py` provides16-column BOM CSV and JSON fulltext/TOC, aggregate and publication exports, raw inputs, node/disposition/provenance sidecars, exceptions, a manifest, and snapshot/parser-bound checkpoints. `full_text` retains semantic HTML, source order and complete bodies. Supplementary tables have observed heading IDs and unnumbered identity; hierarchy is left blank when absent. Publisher currency and local snapshot ID remain separate. CSV readers need a field limit above128KiB for the large reference body; this CLI uses16MiB. Historical replay commands remain in `README-V1.md` and run without the original project cache.

## Supported CUA live acquisition

Run in the supported `cua_repl` host, after reading its current documented APIs. Choose an available browser ID from `cua.getState()` and create **only a new owned tab**. Module filesystem writes occur in Node outside read-only browser evaluation; the browser only reads DOM. Example (replace the absolute module/output paths and observed browser ID with your copied package/host):

```javascript
var cpMod = await import('file:///ABSOLUTE/PACKAGE/acquire_cua.mjs');
var cpAcq = await cpMod.createAcquirer(cua, '/ABSOLUTE/PACKAGE/work/fresh-cua',
  'https://www.codepublishing.com/CA/Fremont/',
  {browserId:'OBSERVED_BROWSER_ID',sessionName:'📚 Code Publishing'});
await cpMod.captureJob(cpAcq, {
  slug:'fremont-ca',id:'root-confirmed',
  url:'https://www.codepublishing.com/CA/Fremont/',
  root_url:'https://www.codepublishing.com/CA/Fremont/',
  kind:'navigation',wait_selector:'a[href*="01.html"]'
});
```

Derive the next exact URLs from that root's observed links; do not manufacture `/html/` paths from hash routes. `make_capture_jobs.py --stage title --captures work/fresh-cua` selects observed Title1/I, and `--stage chapter` selects the first retained title chapter link. Flagstaff requires the explicitly observed TOC frame first (job `family-toc`); document/frame URLs stay scoped. The included `title-jobs.json` and `chapter-jobs.json` are actual source-derived jobs from this run, not substitutes for rediscovery in a later edition. Execute jobs sequentially using `captureJob`; save roots as `root-post` after acquisition and independently compare currencies. `validate_e2e.py` is intentionally tied to the declared bounded samples and fails if their receipts/markers are missing or inconsistent.

The helper waits for the observed selector, saves fresh AX state, verifies exact final URL and challenge absence, and captures DOM in40k UTF16 chunks. It joins strings before one UTF8 write so a chunk boundary cannot corrupt surrogate pairs. Pure-JS SHA256 of complete DOM before/after must equal NodeSHA256 of retained bytes. Receipts distinguish acquisition/checksum revisions and preserve archived exact source. Existing raw/receipt/AX targets fail before navigation/writes: a new attempt requires a fresh job ID/output. Failed attempts remain separate and cannot be silently replaced. Close only the owned tab with `await cpMod.closeAcquirer(cpAcq)`.

Legal `kind` readiness in the CUA helper checks numbered `h3.Cite` chapters; supplementary table captures use navigation mode plus the parser's specific observed heading ID (e.g. `CR`). `cp_collect.py acquire` requires a retained navigation link, matching raw hashes/route and observed heading ID before snapshot admission. Migration notices, stale bodies, unresolved preambles, missing headings and challenges fail closed.

## Standalone Python/Playwright live acquisition

This transport was actually exercised and remains blocked by vendor HTTP403 in this environment. It is delivered for supported ordinary environments; it never converts a challenge page into a success.

```sh
.venv/bin/python -m pip install -r requirements-browser.txt
.venv/bin/python acquire_playwright.py --jobs chapter-jobs.json --out work/fresh-playwright --channel chrome
```

A fresh `--out` is required. `--headed` is optional for ordinary visible execution. Every job runs in an isolated new browser context, with no persistent user profile, cookie transfer, stealth flags, CDP attachment or certificate weakening. Retained receipts include HTTP status, actual browser/Python version, error/readiness/challenge status, raw and second-read SHA, URL and source-script hash. `current-playwright/` archives the earlier six-job script and receipts; `final-playwright/` exercises the guarded final revision. Supported CUA and standalone results must remain distinct in deployment decisions.

## Final verification and delivery integrity

`test-results-final.txt`, `node-test-results-final.json`, `current-pipeline-results-final.txt`, and `playwright-final-results.txt` retain actual runs. `CODE-FREEZE.json` records source hashes before the final suite. `PACKAGE-SHA256.json` binds package deliverables; the verifier allows additional work environments and checks every listed byte. Current reports record script revisions actually used, including earlier retained acquisition versions. Source changes after freeze require a new freeze and complete relevant verification.
