# eCode360 portable acquisition and parser handoff

This package provides a runnable public-request acquisition CLI, a version-bound rendered-DOM importer, a deterministic parser/replay CLI, and retained validation evidence. It covers the 12 eCode360 routes in the 2026-08-28 source map. A separate observation confirms Foster City's newly identified eCode360 route. This is method validation: **no jurisdiction has a verified complete publication inventory or a verified full collection**. The package cannot publish production-ready output; `replay --release` always refuses.

## Run independently

Requires Python 3.9+ and packages in `requirements.txt`; no project modules, database, credentials, original cache or absolute project paths are required. Copy this entire directory, including fixtures, to any location. The originating Python 3.9 environment printed an urllib3/LibreSSL compatibility warning; offline checks passed and HTTPS requests still returned retained publisher responses. Use a supported Python/OpenSSL build for deployment.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m unittest -v test_ecode360.py
.venv/bin/python validate_local.py --verify-bundle
.venv/bin/python validate_local.py --out replay-check
```

The last command performs no network requests. It runs 22 regressions, then replays all 12 historical chapter DOMs and the one current Santa Monica section excerpt into the specified directory: 116 records total, 0 unresolved nodes and 0 errors within those bounded fixtures. Use a fresh output directory after changing the parser or inputs. `examples/` contains the already executed replay, including its test log and report.

## Commands and bounded acquisition

```sh
# One ordinary public request; keeps raw response and receipt even when blocked.
.venv/bin/python ecode360.py fetch https://ecode360.com/HA4470 --out run-http

# Bounded one-request-per-mapped-route checks; never crawls a corpus.
.venv/bin/python ecode360.py probe --routes routes.json --out run-probe --delay 1.5

# Inspect an already retained DOM's on-page TOC. This emits a candidate only.
.venv/bin/python ecode360.py inspect fixtures/historical/santa-monica-ca/chapter.html \
  --url https://ecode360.com/42718485 --out candidate.json

# Reproduce a historical chapter extraction and its disposition/provenance sidecars.
.venv/bin/python ecode360.py replay \
  --inventory fixtures/historical/santa-monica-ca/inventory.json \
  --artifacts fixtures/historical/santa-monica-ca/artifacts.json --out run-replay
```

`collect --inventory reviewed-inventory.json --out run-acquire --max-pages 1 --delay 1.5` acquires only explicit `acquisition_units` in a reviewed inventory; each unit must contain its observed `url` and `evidence`. Repeating it resumes the same frozen queue. Unknown routes, other hosts, login/query endpoints and unsafe redirects are rejected. Acquisition stops when a response is blocked or its customer/code/date identity differs. A blocked run remains immutable evidence; review the route/access method and use a new directory for a subsequent attempt. A bounded queue finishing is never a full-publication claim.

All 12 ordinary HTTP root requests returned 403 in this environment. They are retained under `evidence/live-http/` with hashes, status, redirect/header observations and time. The CLI uses an identifying CompliSolv User-Agent, validates TLS normally and honors bounded 429/503 retry intervals. It does not solve challenges or disguise automation. Supported public browser navigation did render all 12 mapped route identities, with some legal child URLs still showing challenges. This package does not install a second automated browser or depend on an undocumented browser export interface.

When a normal supported browser can read the publication, save a rendered DOM using that browser's supported capture capability and register it with `import-snapshot`. Do not submit a challenge page as legal text. This command checks exact version identity, the snapshot URL against the frozen inventory/observed units, and hashes retained bytes:

```sh
.venv/bin/python ecode360.py import-snapshot \
  --inventory reviewed-inventory.json --html saved-rendered.html \
  --url https://ecode360.com/42718485 --retrieved-at 2026-10-15T16:42:54Z \
  --out run-browser
.venv/bin/python ecode360.py replay --inventory reviewed-inventory.json \
  --artifacts run-browser/artifacts.json --out run-browser-replay
```

Never invent a retrieval timestamp. Omit `--retrieved-at` if unknown; the importer marks the timestamp unverified. The saved snapshot must include actual publisher body customer/code/date attributes. If preserving bounded excerpts instead of a full DOM, retain the exact excerpt files, measured scope, source URL, capture metadata and an explicitly synthetic wrapper; the current Santa Monica fixture demonstrates this. Do not claim a complete DOM from truncated tool output.

## Identity, inventory and outputs

The reviewed inventory is a separate input to replay, not a list inferred from whatever bodies happened to parse. Included historical inventories compare the on-page navigation against body nodes for **one retained chapter each**; they explicitly set `inventory_complete:false`. The current excerpt inventory contains only its one observed legal section. Neither demonstrates publication-wide completeness. `inspect` retains untyped family candidates (for example Sunnyvale's Charter, Code of Ordinances, Statutory References and Tables) separately so a reviewer must assign publication boundaries and scope instead of silently dropping them. It never automatically promotes an observed tree to a complete inventory. A zero collapsed-control count is not completeness evidence.

A source identity is `jurisdiction_slug:publication_id:node_id`. Printed citation text is metadata and is never a deduplication key. Distinct nodes with the same printed number remain distinct; a repeated copy of the same node across chapter/section snapshots emits once and retains all artifact origins. Conflicting content under the same identity fails validation. Publication scope comes from explicit inventories and exact customer/code/date identities; sharing a vendor hostname grants no additional scope.

Only an actual legal header paired to its exact `<GUID>_content` body emits text. Navigation, inline references and neighboring bodies cannot become a substitute body. A parent's own operative text and an unnumbered appendix can each emit independently. Substantive child bodies are removed from the parent's own body to prevent double counting. Non-substantive dispositions require evidence. Classifying an observed operative body as structural, editorial or out of scope requires explicit `allow_body_exclusion`; otherwise it remains unresolved.

Every replay writes the 16-column contract CSV (UTF-8 BOM) and JSON full-text/blank-text TOC pairs, at aggregate and per-publication paths. It also writes `publications.json`, `source-nodes.jsonl`, `node-dispositions.jsonl`, `record-provenance.jsonl`, `exceptions.jsonl`, `checkpoint.json`, `run-manifest.json` and `validation-report.json`. CSV/JSON parity is checked. Sidecar provenance supplies stable record IDs, source node keys, raw source hashes/locators/origins, extraction version, semantic HTML and image sidecars. Origin paths are relative to the input artifact manifest, not the replay output directory; retain the fixture/acquisition directory alongside outputs. The included fixture sources are self-contained in this package. Full text retains native lists/tables with table geometry and superscripts/subscripts, and eCode's div-based nested list text/indentation. Images emit ordered `[IMAGE]` markers and source/alt sidecars. This preserves references; it does **not** transcribe image content.

Resume binding includes the complete inventory, artifact manifest, declared parser version and SHA-256 of the parser file. Raw artifact hash mismatches, version mismatch, scope leakage, missing bodies and unresolved classifications remain visible in exceptions/dispositions. Interrupted and resumed fixture output is compared byte-for-byte with clean output for content and deterministic sidecars. Run-manifest execution timestamps naturally differ. Every export is labeled `validation_sample`; `full_collection_verified` and `release_eligible` remain false even if all bounded fixture nodes resolve.

## Evidence and qualification on 2026-10-15

| Jurisdiction | Historical retained legal records replayed | Current browser route identity | Current representative legal text observed | Full inventory / full collection |
|---|---:|---|---|---|
| Burlingame | 1 | Verified | Challenge on bounded child check | Unverified / unverified |
| Emeryville | 7 | Verified | Challenge on bounded child check | Unverified / unverified |
| Half Moon Bay | 10 | Verified | Challenge on bounded child check | Unverified / unverified |
| Malibu | 28 | Verified | Challenge on bounded child check | Unverified / unverified |
| San Leandro | 1 | Verified | Yes, 1 body on observed article | Unverified / unverified |
| Santa Clara | 4 | Verified | Navigation readable; chapter challenge | Unverified / unverified |
| Santa Monica | 9 | Verified | Yes, 9 bodies; 1 exact current section excerpt parser-tested | Unverified / unverified |
| Santa Rosa | 13 | Verified | Yes, 13 bodies on observed chapter | Unverified / unverified |
| South San Francisco | 8 | Verified | Yes, 8 bodies on observed chapter | Unverified / unverified |
| Sunnyvale | 8 | Verified | Navigation readable; chapter challenge | Unverified / unverified |
| West Hollywood | 10 | Verified | Bounded chapter showed no section_content body; unassessed | Unverified / unverified |
| Tukwila | 16 | Verified | Navigation readable; chapter challenge | Unverified / unverified |

Historical count reconciliation is **1+7+10+28+1+4+9+13+8+8+10+16 = 115**, with exact observed TOC/body identities matching for every fixture. An initial test literal of 123 was a summation mistake, corrected to the explicit per-source count mapping; no source bodies were removed to obtain 115. Retained cache raw timestamps are unavailable. Handoff pilot context is August 2026; the replay date is not asserted as the original retrieval date. Current browser version IDs differ for several publications; historical replay never inherits currentness from a current route check.

The official city pages independently linked eCode360 for Burlingame, Malibu and Santa Monica. Half Moon Bay's readable official page linked the legacy Code Publishing route; redirect reconciliation to the mapped eCode root remains outstanding. Seven other attempted official pages returned 403. The attempted `www.ssf.gov` URL did not resolve and is **not a verified official city URL**, so South San Francisco's official route currentness remains unverified. Browser publisher identity and official municipal routing are separate report fields.

Additional Foster City observation: `https://ecode360.com/FO4449` rendered City of Foster City, customer FO4449, code337727, publisher currency 2026-01-26; Municipal Code node51528208 and Title1 node51404425 were visible. It is separate from baseline12, with no parser or complete inventory claim. The parent handoff retains the other agent's official Code Publishing frame redirect evidence.

`VALIDATION-REPORT.json` is the machine-readable per-jurisdiction qualification and evidence index. `BUNDLE-MANIFEST.json` hashes the delivered files, excluding itself, Python caches and local virtual environments. `evidence/live-browser/` contains bounded DOM attribute/count observations, not saved full DOMs. `fixtures/current-santa-monica/` retains exact small header/body DOM excerpts and metadata; its assembled document wrapper is expressly identified. `fixtures/historical/` contains retained real publisher chapter DOMs, not synthetic examples. Only `fixtures/semantic.html` and its tests use invented legal content.

## Remaining production work

1. Resolve current official municipal routing where unverified and review all publication families, charters, code supplements, tables, attachments and unpublished amendments in scope.
2. Build an independently reviewed, fully expanded, version-bound inventory with parent/order/classification evidence. Several mapped URLs begin at Title1 rather than the publication root.
3. Obtain normal supported access or an authorized official export for challenged child routes. Extend the bounded acquisition queue only after route/scope review; no access-control bypass is supplied.
4. Perform a full authorized collection separately, reconcile every inventoried node to a disposition and both directions of record provenance, and compare source version/inventory again at the end.
5. Compare ordinary sections, definitions, nested lists, merged tables, images/diagrams, history, unnumbered/parent bodies and repeated labels against source renderings across families. Image meaning/transcription and real multi-publication repeated-number cases remain human review work. Existing synthetic regressions are not that source comparison.
6. Add an independent production release attestation after those checks. This package intentionally leaves release disabled; tests and sample row counts cannot supply that attestation.

`prepare_evidence.py` is an optional maintainer utility requiring explicitly supplied original handoff/cache paths; it is not used by the CLI or offline checks. `check_official_routes.py` documents and reproduces the bounded official-page request method; it can return different results later. Neither is needed to run the self-contained package.
