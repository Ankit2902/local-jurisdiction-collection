This package validates bounded standalone collection for ten wave 3 jurisdictions. `results.json` has one row per assignment. Each primary pass means three substantive provisions were acquired live in ordinary headed Chrome, pinned to a named jurisdiction, primary publication and latest job, and converted to normalized JSONL/CSV. Every row has `complete_corpus: false`. The ten targets are Henderson, Orlando, Lexington–Fayette Urban County, Greensboro, Durham, Jersey City, Plano, Madison, Reno and St. Petersburg. A TOC, visible-publication inventory or downloaded PDF is not a normalized whole-jurisdiction corpus.

The current workflow uses the normal public publisher document and live public application APIs in a browser. An ordinary fresh Chrome availability check rendered Henderson's public code unassisted. Direct HTTP attempts by another coordinating group encountered Cloudflare challenges at Cincinnati and Fairfax County. Direct publisher HTTP remains stopped; those attempts are not silently retried through HTTP. Root expressly authorized the ordinary browser workflow after the availability check. No challenge interaction, cookie transfer, user-agent masking, proxy or login is used. The shared stop/authorization record and browser availability proof are retained under `evidence/`. The minimal workflow omits application `/dist/` and unrelated assets while leaving publisher security scripts available; its screenshots show the public document shell. Legal content proof comes from retained, identity-bound live API responses. The initial full application Henderson run and its later minimal transport check are retained separately; duplicate provisions from the transport check are excluded from results record counts.

Use Python 3.9+ for core normalization, tests and verification. Acquisition also needs Node 18+, Playwright and ordinary installed Google Chrome on a graphical desktop. The POSIX `fcntl` shared gate supports macOS/Linux; this package does not claim Windows portability. Install Node/Python dependencies in this directory or your own environment:

```sh
npm install
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

The core offline verifier needs only Python's standard library, so the venv is optional unless inspecting PDFs. It does not launch a browser, access the network or change evidence:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 scripts/verify.py --offline
PYTHONDONTWRITEBYTECODE=1 python3 scripts/test_rate_gate.py
```

To repeat live collection, use a fresh unpopulated output root. The driver sets explicit accepted jurisdiction names and state from `targets.json`; it refuses existing acquisition receipts. Do not run the legacy direct `acquire.py` during the recorded direct-transport stop.

```sh
python3 scripts/run_browser.py --sequence 69 --out-root /absolute/FRESH/output-root
```

All coordinating Municode groups use `/tmp/compliSolv-municode-rate-gate` unless `MUNICODE_GATE_DIR` is explicitly changed together by the operators. The operational browser gate reserves starts at nominal 3.5-second intervals under a cross-process lock. A challenge, API403/access denial or429 creates an atomic shared browser stop. A429 also persists a cooldown honoring Retry-After with a minimum 300 seconds. No automatic restart clears the stop; coordinated operator authorization is required. `scripts/test_rate_gate.py` exercises cooldown refusal without network. The one availability probe's audit includes a logged 2.379-second interval despite nominal 3.5-second reservation logic; actual packet spacing cannot be retrospectively guaranteed. That exception is retained in the gate audit, separated from the subsequent operational browser logs. No429 was observed in these runs.

The collector records exact executed acquisition and gate bytes, runtimes, source URLs, timestamps, response hashes, pinned product/job, visible code publications and download metadata. Final portable code was hardened after the earliest executions: explicit job/product and organization/client binding, client-specific response reuse, shared stops for headerless refusals, and manually gated PDF redirect hops. Earlier executed versions are retained; final offline verification independently rechecks their identities and raw response bindings. Early PDF transport receipts did not record redirect chains. A later fresh primary target exercises the final collector. `MUNICODE_FULL_BOOTSTRAP=1` optionally runs the ordinary complete app; this is slower because every issued publisher request remains gated.

Normalized records preserve exact source legal HTML, node/heading/path, product/job identifiers, body hashes, lists, footnotes/notes, links including `data-nodeid` targets, and table cells with row/column spans and tags. Plain text/CSV separates adjacent cells. Nested table contexts are preserved by the final parser; broad table fidelity is not claimed from a single checked provision. The operative Henderson §4.05.420 business-license schedule is the explicit table test: one table, 176 rows, 528 cells and105 internal cross-reference links. Independent offline Chrome DOM comparison found no text/span/tag mismatches across all 528 cells. All114 anchor texts and source attributes also match independent DOM extraction; all 105 internal targets resolve in the retained same-job TOC. The screenshot was visually inspected. `verify_table.cjs` checks the first record in the supplied folder; the table test folder intentionally contains exactly that one record. An earlier observed investigation-fee provision contained no table; that failed table-selection probe remains an additional substantive sample, clearly separated.

For manual offline normalization into a separate directory:

```sh
python3 scripts/normalize.py live/henderson --offline --out /FRESH/replay-output
```

`prepare_outputs.py` is an explicit mutable build step, not the read-only verifier. It preserves earlier parser-output trials, snapshots final parser bytes and generates final normalized files. `build_results.py` similarly rebuilds results/inventories explicitly. Do not run these build steps against a sealed package. The verifier writes temporary replay files outside the package and compares bytes; `manifest-sha256.json` hashes the final delivery. No Codex runtime is required after installing ordinary dependencies. The validation machine used macOS arm64, Chrome 155.0.8059.84, Node 24.19.0, Playwright 1.62.1, Python 3.9.6 core and Python 3.12.14/pypdf 6.10.0 for PDF inspection. Bundled validation runtimes were used via environment overrides; no package runtime depends on their absolute paths.

Publisher downloads are genuine publication PDFs obtained automatically through the visible primary publication's download feature, not print-to-PDF. `%PDF` and a readable PDF container establish transport/structure only. `publisher-pdf-inspection.json` inspects the first three pages; `edition-check.json` compares the first page's jurisdiction/state and supplement/update tokens (or a republication heading with matching codified-through ordinance) with live API metadata. Download passes are limited to those checks. Historical instruction sheets may follow the first page. The remaining PDF body has not been parsed, normalized or matched section by section. Orlando exposes a concrete mismatch: live Supplement 93, Update 1 versus a download starting with Supplement 91 from December 2025; it is reported as partial. Consult each row for other edition mismatches or disabled exports.

Each `family-inventory.json` lists visible and hidden publications, separately visible products not acquired, charter/zoning/development entries found in the primary TOC, latest-job banners, publisher currentness disclaimers and uncodified-ordinance counts. These inventories identify gaps. They do not prove collection of all charter, zoning, development, administrative or uncodified bodies. The official Lexington page's fixed job485367 is compared with current live latest-job metadata; Lexington–Fayette is one urban-county target. Reno’s official FAQ and live publication inventory identify Administrative Code as its primary municipal code book, with a separate Land Development Code. The initially assumed `code_of_ordinances` lookup returned `Model:null`; that failed attempt remains in `live/reno`, while the successful corrected acquisition is in `recovery/reno`. Madison's assigned `madison.gov/attorney` returned404; current official `cityofmadison.com/attorney` returned200 and links the live Madison Municode code. Other government routing attempts and any403s are retained separately and do not count as substantive code acquisition. Refer to row-specific evidence and limitations before selecting families for full ingestion.

Final bounded outcomes (all primary rows passed live acquisition and normalization):

| Jurisdiction | Legal records | Native PDF pages | First-page edition qualification |
|---|---:|---:|---|
| Henderson | 5 | 2,360 | matched observed API edition |
| Orlando | 3 | 188 | differs from observed API edition; partial |
| Lexington-Fayette Urban County | 3 | 1,599 | matched observed API edition |
| Greensboro | 3 | 926 | differs from observed API edition; partial |
| Durham | 3 | 1,450 | differs from observed API edition; partial |
| Jersey City | 3 | 2,514 | matched observed API edition |
| Plano | 3 | 1,648 | matched observed API edition |
| Madison | 3 | 2,822 | differs from observed API edition; partial |
| Reno | 3 | 1,520 | differs from observed API edition; partial |
| St. Petersburg | 3 | 2,654 | differs from observed API edition; partial |

The record total is **32 provisions: 30 primary sections and 2 explicitly supplemental Henderson sections**. The 10 primary native PDF transports all passed; 4 first-page source/edition checks passed and 6 were partial. See each `edition-check.json` for the concrete metadata comparison. The 6 partials are Orlando, Greensboro, Durham, Madison, Reno and St. Petersburg. These first-sheet discrepancies do not establish the currency of the remaining PDF body.
