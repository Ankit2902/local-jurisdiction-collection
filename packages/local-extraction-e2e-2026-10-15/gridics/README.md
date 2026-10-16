# Gridics Cupertino acquisition → parser → output handoff

The authoritative current result is `E2E-VALIDATION.json`. This folder extends the immutable first validation package into a bounded live end-to-end pilot. It delivers both a standalone Python/Playwright job and a supported CUA capture adapter. No jurisdiction-wide legal body collection, database import or production edit is performed.

## Install outside the deliverable

Python 3.9+ is supported; actual live execution used Python 3.9.6, BeautifulSoup 4.15.0, Playwright 1.60.0 and official Chromium 148.0.7778.96. Put the virtual environment and browser cache outside the package:

```sh
python3 -m venv /tmp/gridics-e2e-venv
/tmp/gridics-e2e-venv/bin/python -m pip install -r requirements.txt
PLAYWRIGHT_BROWSERS_PATH=/tmp/gridics-playwright-browsers \
  /tmp/gridics-e2e-venv/bin/python -m playwright install chromium
```

Run commands below from this folder. Local `.venv/` and `.browsers/` directories are disposable execution caches and must be excluded from delivery, hashes and archives. They are not script dependencies.

## Reproduce retained end-to-end qualification without network

```sh
/tmp/gridics-e2e-venv/bin/python verify_e2e.py
```

This runs synthetic and actual-source regressions, replays the freshly acquired standalone and CUA raw manifests into new temporary packages, checks CSV/JSON values, source table rows/cells, navigation dispositions, both runtime semantics, start/end receipts and interrupted/resumed deterministic exports. It writes `E2E-VALIDATION.json`, evidence logs and the two final reviewed packages. It does not open a browser or make network requests. `validate.py` separately reproduces earlier historical/IAB source qualifications; its report is limited to those earlier samples.

## Run the bounded standalone acquisition

The exact live pilot is executable through `e2e_run.py`. The start phase captures one source route, verifies a fresh reload, writes immutable hashes and deliberately stops with status `interrupted_by_requested_progress_limit`. Resume preserves that artifact and captures only the remaining observed URLs. Exit code 0 alone does not mean the capture is complete; inspect manifest `acquisition_status` and requested route count.

```sh
PLAYWRIGHT_BROWSERS_PATH=/tmp/gridics-playwright-browsers \
  /tmp/gridics-e2e-venv/bin/python e2e_run.py start
PLAYWRIGHT_BROWSERS_PATH=/tmp/gridics-playwright-browsers \
  /tmp/gridics-e2e-venv/bin/python e2e_run.py resume
/tmp/gridics-e2e-venv/bin/python gridics.py replay \
  --manifest standalone-combined-manifest.json --out /tmp/gridics-fresh-replay
```

The delivered `standalone-final/` is retained proof. To repeat live acquisition, first preserve/move that folder and its command receipts or run `acquire.py` directly into a fresh output directory with a fresh explicit snapshot ID and source-version label. `e2e_run.py` intentionally refuses to overwrite an existing start checkpoint. Its three URLs are Title 1, section 1.09.030, and the separately observed Comprehensive Ordinance List root. The separate retained `navigation-acquisition/` stage enumerated tree labels/identities only; it did not visit every leaf or collect their legal bodies. `verify_e2e.py` builds `standalone-combined-manifest.json` with the exact independently captured navigation hash plus the later fresh body artifacts. The navigation stage completed before the final body readiness performance correction; its exact successful expansion code and command receipts are retained, and no all-leaf route qualification is inferred.

Generic CLI example for one observed route:

```sh
PLAYWRIGHT_BROWSERS_PATH=/tmp/gridics-playwright-browsers \
  /tmp/gridics-e2e-venv/bin/python acquire.py \
  --url 'https://codehub.gridics.com/us/ca/cupertino#/90d493fe-25f4-4aef-a519-710b1e0055c6' \
  --snapshot-id operator-cupertino-pilot \
  --source-version 'legal-version-unknown:operator-cupertino-pilot' \
  --out /tmp/gridics-operator-pilot --verify-end
```

`--inventory --max-expansions 600 --dismiss-notices` expands the observed navigation once. The optional notice handler only dismisses the observed informational disclaimer and product tour; unfamiliar agreement language, authentication, HTTP 401/403/429/503, expansion errors and snapshot drift stop the run. No credentials, guessed data API, TLS weakening, CAPTCHA handling or publisher access workaround is implemented. `--headed --operator-window 20` alternatively provides bounded operator time for notices. Default route bound is six. The large ordinance table exposed unnecessary repeated parsing under a 20-second pilot budget; final readiness parses once per observation, and the final three-route job uses a 60-second readiness timeout. `--stop-after N` creates a clean interrupted checkpoint; resume with the same bound config and omit that progress limit.

Each route uses an isolated browser context, exact URL plus publisher UUID readiness and three stable semantic observations. `--verify-end` reloads the route and requires matching UUID paths, headings and own semantic body hashes before success is checkpointed. Code/config/version and raw hashes bind acquisition; parser/config/manifest/snapshot/version bind replay. Prior successful acquisitions are hash-verified on resume.

## Supported CUA runtime

`cua_capture.mjs` is an adapter invoked **inside `cua_repl`**, using a caller-created isolated tab and documented CUA methods. It never opens a hidden browser connection or reads cookies/storage. The pilot actually ran this adapter through supported Chrome CUA and replayed its output with the same Python parser. An operator can use this pattern after normal CUA browser setup; substitute the actual package location and their own tab handle:

```javascript
const adapter = await import('file:///ABSOLUTE/PACKAGE/PATH/cua_capture.mjs');
await adapter.capture(myIsolatedTab, '/ABSOLUTE/NEW/OUTPUT',
  'https://codehub.gridics.com/us/ca/cupertino#/90d493fe-25f4-4aef-a519-710b1e0055c6',
  {snapshotId: 'operator-cua-pilot', sourceVersion: 'legal-version-unknown:operator-cua-pilot'});
```

Then run `gridics.py replay --manifest /ABSOLUTE/NEW/OUTPUT/snapshot-manifest.json --out /tmp/gridics-cua-replay`. The adapter requires exact URL, UUID/heading identity and three stable DOM observations, reads complete rendered DOM in 70,000-character chunks, verifies lengths and rejects truncated/drifting capture. It is a bounded capture adapter; full navigation expansion and durable acquisition resume are handled by the standalone job. Python replay/resume works with either runtime's immutable output manifest.

## Parser and package behavior

The parser traverses each publisher node's own body once and excludes nested publisher containers and UI controls, avoiding duplicated nested `li`/`p` text. Tables retain rows, header/cell identity and spans; lists retain nesting and start/type/value, including CSS alpha/Roman numbering; superscripts/subscripts remain tagged. Images retain `[IMAGE]` at reading position and source/alt data in original structured HTML. Parent bodies, chapter notes, source crossreference text and footnotes survive. Stable record IDs use publisher UUID, so repeated printed citations do not collide.

Replay packages contain publication/aggregate JSON and UTF-8-BOM CSV with the required 16 fields, TOC exports, publication inventory, source nodes, dispositions, provenance, exceptions, immutable raw copies, snapshot/run manifests and checkpoints. Hash-matched response metadata and end-reload DOM evidence are copied into each package. Large ordinance-list text exceeds Python's default CSV reader field limit (131,072 characters). Consumers using Python `csv` should call `csv.field_size_limit(...)` with a sufficient explicit bound before reading; the final verifier sets it to the observed maximum exported field length and checks exact JSON equivalence. Every observed navigation identity receives a disposition; unacquired bodies remain unresolved, and full collection flags stay false. Chapter-note preservation is conservative and still needs downstream editorial classification.

Navigation identity is distinct from a verified executable route. Ordinary UUID ancestry produces `candidate_source_url`; only a matching actual rendered publisher `data-path` qualifies `source_url`. Some real groups use compound UUID class namespaces that disagree with their current DOM ancestor. Those exact opaque identities and ancestry are preserved; they and their descendants do not become fabricated executable URLs. Full observed expansion does not establish current legal completeness or validate every leaf route.

## Evidence and limits

`e2e-evidence/official-root.json` and its AX snapshot verify the live city website's explicit Cupertino CodeHUB link. `publisher-notice.json` retains the publisher's statement that the source may not reflect the most current legislation. No current-through date or authoritative legal version has been established; explicit unknown-version snapshot labels remain in use.

Standalone receipts retain executable commands, environment, browser version, timestamps, return codes, acquisition status, route counts and raw hashes. Failed notice-selector, compound-identity/ancestry and initial large-table readiness-timeout attempts are retained under clearly named failed directories/logs. The first interrupted policy-pause attempt is not treated as a publisher failure. The earlier direct HTTP 403 and Chrome policy-service failure remain historical evidence; subsequent actual standalone HTTP 200 and supported Chrome CUA successes supersede a blanket live-access blockage claim.

Actual source coverage includes Title 1 prose, nested lists, a visually reviewed 13-row/26-cell table, and the separately acquired ordinance-list family when reported as passed in `E2E-VALIDATION.json`. Synthetic fixtures additionally cover images, rowspan/colspan, superscript/subscript notation, crossreferences and footnotes. No claim is made that every construct or image/appendix family has been checked live.

The prior `evidence/`, `retained-manifest.json`, `live-manifest.json` and their replay folders are retained historical/earlier-IAB validation sources. Truncated 200k browser exports remain diagnosis-only and are rejected by the legal parser. Fresh complete captures named by the current acquisition manifests are authoritative for this end-to-end run.
