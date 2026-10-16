# Live end-to-end pilots: San Mateo, King County and Daly City

This package adds actual live acquisition → delivered parser CLI → portable JSON/CSV output tests to the earlier retained-source pilot. Only this copied E2E directory was edited. No production adapter, registry, database import or complete jurisdiction extraction occurred. The source documents and samples are bounded deliberately.

`live/final-san-mateo/E2E-VALIDATION.json`, `live/final-king-county/E2E-VALIDATION.json`, and `live/final-daly-city/E2E-VALIDATION.json` are the authoritative new run reports. They include actual commands, interpreter/environment, UTC start/end times, source response receipts, input/output hashes, counts, limitations and exact blockers. Earlier `VALIDATION-REPORT.json` files and `ORIGINAL-PILOT-README.md` describe the original retained-source pilot; their transport limitations have been superseded only where the new E2E evidence says so. `live/develop-*` records are development runs, not final qualification.

## Portable setup

Use Python 3.9+ (3.11+ recommended). No project-checkout imports, absolute user path or pre-existing temporary environment is required. From this directory:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m unittest test_methods test_e2e -v
```

For the optional standalone browser, install declared Playwright and ordinary Google Chrome:

```sh
.venv/bin/python -m pip install -r requirements-browser.txt
```

`browser_capture.py --channel chrome` uses a new isolated headless browser with installed Chrome; it does not use a persisted profile. Alternatively `--channel ''` selects Playwright Chromium after an ordinary `playwright install chromium` installation. All network scripts use normal TLS verification; there is no denial/challenge bypass. This validation environment used Python 3.9/LibreSSL, which emits an urllib3 compatibility warning; successful response receipts are retained, and no certificate verification was disabled. A modern OpenSSL Python is recommended for handoff.

## Live orchestration

Every `e2e.py --out` directory must be new. Existing directories are rejected so a cache replay cannot be called a live run. Commands below create independent outputs outside the bundle if desired.

```sh
.venv/bin/python e2e.py san-mateo --out /tmp/san-mateo-live-new
.venv/bin/python e2e.py king-county --out /tmp/king-live-new --landing-capture live/browser/final-king-landing.html
.venv/bin/python e2e.py daly-city --out /tmp/daly-live-new --route-capture live/browser/final-daly-route.html --section-capture live/browser/final-daly-section-cua.html --standalone-browser
```

The supplied CUA evidence is a timestamped capture, not a fresh browser fetch when replayed. The final run used captures freshly produced for that run. Reacquire those captures through the supported CUA helper to renew the route/body checks on a later date. Evidence and hash receipts are copied under each run's `source/browser/`; exported packages independently retain their raw inputs.

San Mateo resolves current repository HEAD, pins its full SHA, executes `san_mateo.py acquire --archive`, verifies the complete archive's exact Git-tree membership and every Git blob hash, and resolves a declared include subset from the actual repository `index.xml`. Only Code Title 1 and Charter XML are parsed. The root/code index files are checked for metadata-only own content before traversal; a mixed own-body/include file fails explicitly and needs an explicit own-content profile. This is bounded include resolution, not a general-purpose whole-law expansion engine. Every unselected include receives an explicit exclusion disposition. The XML path and child-index locator remain tied to the original source file. A Git commit is a source version, not a legal current-through date.

King County takes a hash-bound current official landing capture, checks that the exact HTML and Word routes were observed there, acquires original HTTP bytes for Title 1, Title 2A and Charter, and executes `king_county.py` on each. It retains source encodings, complete DOM section ranges and three Word files. The reconciliation report compares TOC/body identifiers and source date markers with the Word paragraph text. It does not silently repair publisher numbering or dates. Charter has no detected independent numbered section TOC, so that comparison is marked unavailable rather than reporting every section as missing. Full Word/HTML paragraph equivalence and Title 21A reconciliation are outside this bounded live run.

Daly City executes `daly_city.py acquire` against the public publisher API: live CA client/publication discovery, full independent TOC, and three exact observed section requests (adoption, roof table, fire-code appendix). It executes the parser CLI per requested node. After browser/API parity, it refetches publication metadata and the full tree to fresh filenames; canonical JSON drift causes failure. That brackets collection and browser verification but does not make an atomic publisher snapshot guarantee. The city homepage's exact official Municode ordinance-bank link is retained separately from the codified-publication route. CUA and standalone Chrome captures both compare the exact adoption body text with its API document. Table/appendix structure is inspected from API output; rendered parity for those two samples is not claimed. Unincorporated ordinances remain separate inventory, not incorporated text.

## Supported CUA runtime

`e2e_cua_bridge.mjs` exports `captureCua(tab, output, readySelector)` for stable whole DOMs, and `captureCuaScope(tab, output, selector)` for a bounded exact DOM element. Use only in the authorized Codex CUA REPL, with an existing observed tab. It is not a direct browser-transport Node client. Example after creating an isolated authorized Chrome tab and reading its UI/DOM:

```js
var bridge = await import('file:///ABSOLUTE/PACKAGE/e2e_cua_bridge.mjs');
await bridge.captureCua(kingTab, '/ABSOLUTE/OUTPUT/king-landing.html', 'h1');
await bridge.captureCuaScope(cityTab, '/ABSOLUTE/OUTPUT/city-route.html', '.fancyButton507');
await bridge.captureCuaScope(codeTab, '/ABSOLUTE/OUTPUT/adoption.html', '[id="c_TIT1GEPR_CH1.01COAD_1.01.010AD"]');
```

Selectors above were observed on October 15, 2026; inspect current DOM before reuse. Scope capture declares the selector and retains only that exact element. Whole-DOM capture reads bounded chunks and fails if the document changes length or truncates. A dynamic city homepage failed the whole-DOM integrity check during development; the final route capture uses its exact observed official link element instead. Failed captures never become parser inputs.

The standalone browser can also be invoked directly:

```sh
.venv/bin/python browser_capture.py --url 'https://library.municode.com/ca/daly_city/codes/code_of_ordinances?nodeId=TIT1GEPR_CH1.01COAD_1.01.010AD' --out /tmp/daly-rendered-new.html --ready-selector '[id="c_TIT1GEPR_CH1.01COAD_1.01.010AD"] .chunk-content' --channel chrome
```

## Output and verification

Each `output/<sample>/` is a portable bounded package with 16-column fulltext JSON/CSV, blank-body compatibility TOC, source nodes, dispositions, semantic provenance, original raw bytes and run manifest. The actual document CLIs may also be used separately; see each script's `--help`. `common.package` checks CSV/JSON equality while exporting. Tables retain semantic HTML rows/cells/spans in `full_text`; list labels, notes and inline superscript/subscript survive. Original XML/API/HTML remains authoritative.

`test_methods.py` retains 21 prior parser/portable replay regressions. `test_e2e.py` adds bounded include closure, mixed own-body/include rejection, cycle/traversal/missing include rejection, Git blob mismatch, latest-version drift, tampered capture rejection and Word split-run reconstruction. These are offline tests. Live qualification is separately recorded by `e2e.py`; offline tests do not count as live acquisition.

```sh
.venv/bin/python verify_hashes.py
```

`ARTIFACT-HASHES.json` covers delivered files other than Python bytecode and the manifest itself. Regeneration is deliberate via `verify_hashes.py --write`. Full-jurisdiction readiness still requires complete source-node disposition reconciliation, broader structural/document equivalence sampling and resolution of flagged publisher discrepancies; these pilots do not assert human legal acceptance.
