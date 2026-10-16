# Gridics CodeHUB Cupertino bounded validation handoff

This folder provides a runnable offline parser/package CLI and a bounded Playwright acquisition CLI. The offline qualification includes synthetic regressions, two actual retained August 2026 rendered DOM snapshots, and four fresh October 15, 2026 IAB rendered DOM snapshots. The fresh pilot resolved the Title 1 root plus sections 1.01.010, 1.09.030 and 1.10.140 through their full UUID hash routes. Each route renders the whole Title 1 hierarchy.

All eight Title 1 chapter controls were expanded through ordinary browser UI. The independently captured navigation contains 65 Title 1 UUID nodes, exactly matching the 65 rendered legal containers: eight chapters, the title, and 56 numbered sections. The parser emits 58 records, including two chapter notes kept as separate parent records. Seventeen branches outside Title 1 remain closed. This is a bounded validation sample; publication inventory completeness, legal currency, and full collection are **not qualified**. No corpus collection, import, database or production change was performed.

## Portable offline reproduction

Use Python 3.9 or newer. Run these commands from this folder; no project runtime, credential, network service or absolute local dependency is used by replay/tests.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install beautifulsoup4==4.15.0
.venv/bin/python validate.py
```

`validate.py` runs the regression suite, rebuilds `retained-replay/` and `live-replay/`, compares clean and interrupted/resumed exports, and writes `VALIDATION-REPORT.json` with evidence hashes. It removes only the two generated pilot checkpoint files before rebuilding. Production callers should use new output directories or preserve and resume their bound checkpoint. Test duration is around one minute on this workstation; no live requests occur.

Useful individual commands:

```sh
.venv/bin/python -m unittest discover -s . -p test_gridics.py -v
.venv/bin/python gridics.py replay --manifest retained-manifest.json --out /tmp/gridics-retained-review
.venv/bin/python gridics.py replay --manifest live-manifest.json --out /tmp/gridics-live-review
.venv/bin/python gridics.py inventory --html evidence/live-title1-navigation.html --out /tmp/gridics-observed-navigation.json
```

To exercise interrupted replay, use a fresh directory and run `replay --manifest retained-manifest.json --out /tmp/gridics-resume-review --stop-after 1`, then the same command without `--stop-after`. Snapshot ID, explicit source-version label, manifest SHA-256, parser SHA-256, configuration and immutable raw hashes bind progress. A mismatch fails; selecting a new directory is required. Duplicate captures of one UUID merge only when own semantic content agrees. Repeated printed citations with different UUIDs remain distinct records.

## Delivered acquisition CLI

Install optional acquisition dependencies in the same environment:

```sh
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m playwright install chromium
.venv/bin/python acquire.py \
  --url 'https://codehub.gridics.com/us/ca/cupertino#/90d493fe-25f4-4aef-a519-710b1e0055c6' \
  --url 'https://codehub.gridics.com/us/ca/cupertino#/90d493fe-25f4-4aef-a519-710b1e0055c6/88af81d8-f905-4db5-98ae-6c3735fab006/e039b8ec-52e6-4c19-a5e3-a73daccfdeba' \
  --snapshot-id cupertino-operator-pilot-2026-10-15 \
  --source-version 'legal-version-unknown:cupertino-operator-pilot-2026-10-15' \
  --out /tmp/gridics-operator-pilot --headed --operator-window 20
.venv/bin/python gridics.py replay \
  --manifest /tmp/gridics-operator-pilot/snapshot-manifest.json \
  --out /tmp/gridics-operator-replay
```

`--operator-window 20` gives the operator 20 seconds per fresh browser context to dismiss the observed informational notice/onboarding through normal UI, if shown. Maximum is 60 seconds and `--headed` is required. Do not continue through authentication or access restrictions. The script uses a fresh context for each URL, requires exact requested URL and publisher UUID container identity, and waits for three stable legal-content observations. It records response status metadata and stops on HTTP 401, 403, 429 or 503. It has no credentials, hidden API, browser-policy workaround or TLS override.

Add `--inventory --max-expansions 300` only for a separately authorized navigation-discovery run. It recursively clicks the observed non-anchor `.doc-tree-iconEle` controls, persists each navigation state, and waits for exposed child groups; an expansion failure or bound leaves acquisition unsuccessful. Zero observed closed branches still does not establish full publisher inventory: virtualization and publication scope need independent reconciliation. Default route bound is six and timeout is 40 seconds. The delivered standalone Playwright CLI was imported/tested offline but **has not been executed live** in this environment. The live pilot used supported CUA IAB with the same observed DOM identities and navigation controls; qualify the CLI transport in the destination environment before relying on unattended acquisition.

## Serialization and output contract

`gridics.py` traverses each node's own body once, excluding nested publisher containers and navigation controls. Nested `li`/`p` text is not duplicated. Lists retain nesting, explicit start/value/type and CSS alpha/Roman numbering; tables retain rows, header/cell identity and spans; superscripts/subscripts remain tagged. Images emit `[IMAGE]` at their reading position and keep original source/alt data in `source-nodes.jsonl` structured HTML. Parent bodies, editorial notes, source crossreference text and footnotes survive. Actual source pilot content covers prose, nested lists and a 13-row/26-cell table in 1.09.030. Synthetic cases additionally cover images, span attributes and sup/sub notation; those constructs have not all been checked in live Cupertino examples.

Each replay directory contains publication and aggregate JSON/UTF-8-BOM CSV with the required 16 fields, derived TOC exports, `publications.json`, `source-nodes.jsonl`, `node-dispositions.jsonl`, `record-provenance.jsonl`, `exceptions.jsonl`, `source-snapshot-manifest.json`, `validation-report.json`, `run-manifest.json`, checkpoint and hash-matched raw source copies. Every observed UUID receives a disposition. Navigation nodes outside acquired Title 1 are `unresolved`; completeness flags stay false. A section route can expose its entire title; UUID deduplication avoids copying that title's records on each route. Chapter-note inclusion is conservative preservation and needs downstream editorial classification before production import.

## Evidence and precise qualification

- `retained-manifest.json`: actual archived publisher DOM from the project's municipal-code-batch browser sample cache, two files originally retained August 28, 2026; legal version unknown. These are actual historical sources, separate from the fresh pilot.
- `live-manifest.json`: four complete fresh IAB DOM captures, exact URL/state evidence and hashes. Captures were read in 70,000-character chunks and checked against DOM character length. No publisher response metadata was available through IAB.
- `evidence/live-navigation.json` and `live-title1-navigation.html`: independent expanded navigation used for Title 1 UUID-set reconciliation. Extraction metadata explicitly notes that its surrounding initial full-page export was truncated; the complete navigation element precedes that cutoff. Legal bodies from truncated files are excluded.
- `evidence/truncated-export.html`, `live-title1-inventory.html`, and `live-navigation-expanded.html`: retained failed 200k-character exports for diagnosis only. The legal parser rejects `[Truncated]`; complete fresh files named in `live-manifest.json` replace them.
- `evidence/live-observations.json`, `*-state.json`, `*.ax.txt`: bounded live navigation observations and exact URL/DOM counts. Screenshots are viewport corroboration only; they do not prove table visual review or route scroll position.
- `evidence/source-comparisons.json`: real retained and fresh DOM counts, chapter-note and difficult-table serializer comparisons.
- `evidence/retained-replay-equivalence.json`: eight deterministic clean/resume export hash comparisons. Regression tests also compare CSV/JSON values, stale async readiness, duplicate conflicts, checkpoint version drift, raw tampering, traversal escape, and the truncated real export.
- `evidence/landing-response.json` and `browser-attempts.json`: an independent direct HTTPS probe returned 403 and initial Chrome connector policy service failed. Supported IAB subsequently rendered public content normally; these earlier failures are retained without representing live access as globally blocked.

Remaining acceptance work is to verify the official city link and current-through/version continuity, execute the standalone acquisition CLI, reconcile all publication families and virtualized branches, and review additional live image/appendix/notation examples. No full-source completeness or current legal version claim is made.
