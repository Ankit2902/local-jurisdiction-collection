# eCode360 and municipal.codes full-publication collector

Run from the repository root with Python 3.12+, Beautiful Soup and Playwright. Collection uses an installed ordinary, headed Google Chrome (`channel="chrome"`) and a new owned context; it has no Codex, database, remote-browser or old-output-package dependency. It closes only its own browser/context. Verification and synthetic tests need no browser or network.

```sh
python -m venv .venv
.venv/bin/python -m pip install -r collectors/ecode/requirements.txt
.venv/bin/python -m collectors.ecode.cli collect --url https://ecode360.com/AL0934 --jurisdiction Albany --state NY --out ./fresh/albany
.venv/bin/python -m collectors.ecode.cli collect --url https://phoenix.municipal.codes/Charter --publication Charter --jurisdiction Phoenix --state AZ --out ./fresh/phoenix-charter
.venv/bin/python -m collectors.ecode.cli verify --out ./fresh/albany
.venv/bin/python -m unittest collectors.ecode.tests.test_faults -v
```

Use a fresh output directory. Exit 0 means the selected publication passes text, attachment and edition checks; exit 2 means an independently qualified incomplete result; exit 1 means invalid input or failed verification/cache qualification. A limit is never a full-publication success, even if the selected page happens to contain every currently observed node.

```sh
python -m collectors.ecode.cli collect --url https://ecode360.com/AL0934 --jurisdiction Albany --state NY --out ./fresh/albany --max-items 5
python -m collectors.ecode.cli collect --url https://ecode360.com/AL0934 --jurisdiction Albany --state NY --out ./fresh/albany --resume
```

The second command must use the exact same source revision and identity/configuration. It validates every cached artifact and the dynamically reconstructed inventory before opening Chrome. It makes a fresh ordinary document bootstrap, refuses a changed edition, and continues only missing nodes/assets. Checkpoints and raw artifacts use atomic writes with file/directory fsync. An interrupted process cannot gain a complete claim from an unfinished checkpoint.

For an explicitly reviewed parser or policy change, `--adopt-from OLD_OUT --out NEW_OUT` is a distinct, opt-in migration. It requires a fresh output, verifies original raw hashes and executed source snapshots, preserves those original snapshots and the original checkpoint, requalifies all raw with the new parser, and performs fresh resume/closing validation. Ordinary `--resume` cannot silently upgrade a cache. Migration refuses access-stopped evidence and separate historical image assets. A migrated result is retained-source acquisition plus new normalization and fresh closing checks; it is not entirely fresh acquisition by the new source revision.

A stopped or older retained run can be normalized under the current parser without any network:

```sh
python -m collectors.ecode.cli replay --source ./stopped-source --out ./fresh/offline-replay
python -m collectors.ecode.cli verify --out ./fresh/offline-replay
```

`replay` preserves source access stops and original execution/acquisition provenance. It marks the derivative `network_prohibited`; collection cannot resume from that derivative. An incomplete verified replay returns exit 2. Publisher access stops are not cleared automatically; production resume requires an authorized operator to review actual source access and shared stop state after service returns.

## Publication scope

For eCode360, use the observed customer alias (for example `AL0934`, `BU1237`, `TA6977`, `RO0104`, `AL1955`, `NE4043`, `AN6998`). The alias denotes the entire current customer Code, including the Code/Charter divisions present in that publisher inventory. A numeric chapter URL is promoted to its observed customer alias by default. `--subtree` deliberately disables that promotion and prevents a whole-publication completion claim. The collector dynamically expands all retained TOCs, fetches all unresolved nodes, and skips individual nodes whose own legal bodies were already supplied by a parent page. It retains chapter/article-owned history instead of assigning descendants' text to a parent.

For municipal.codes, select an observed publication root or use `--publication SLUG_OR_ROOT_URL`. Examples include Phoenix `CC`, `ZO`, `Charter`; Bakersfield/Aurora `Code`; and Eugene `EC`. The host may have multiple independently published tabs. The selected tab's complete static `/contents` is the independent inventory. A title page's preface is separately owned. The collector uses a root native HTML export if the observed Share control is enabled; otherwise it traverses the full inventory using public chapter pages, which often supply all their descendants. The current Phoenix Charter title-page “This Page” native control is disabled; ordinary chapter bulk HTML is used. A native chapter download is a bounded export, never a whole city proxy.

Other publisher hosts, unsupported inventories/lazy controls, missing legal wrappers or unpinned currency are explicit incomplete/error outcomes. CodePublishing's legacy `.com` URLs must first resolve through an official current route; this adapter does not infer migrations or issue unobserved legacy API calls. New publisher types are not treated as compatible merely because the hostname looks similar.

Jurisdiction/state expectations bind to source labels when supplied. eCode360 exposes customer, code ID, date and state. municipal.codes exposes a publication title and currency statement; source-verified state may be unavailable and is reported separately. Collection of one selected publication always reports `jurisdiction_complete=false`: other tabs, unincorporated ordinances and external adopted laws remain outside that certification.

## Image and attachment policy

The authoritative [image policy](../IMAGE-POLICY.md) applies. Every own source image, picture alternative, inline SVG, image-only body and CSS image reference becomes the exact literal `[IMAGE]` in source order in normalized text/HTML. No separate image bytes, OCR or renderings are acquired. Browser image/font/media loads are blocked without changing challenge controls. Source IDs, headings, paths, surrounding text and image occurrence/reference metadata remain available. Raw publisher HTML/native files may inherently contain images; normalized output contains no active image tags or image data URIs. Intentional image omissions do not create failed required attachments, and no claim is made that image contents were transcribed.

Nonimage document attachments remain separate required assets. HTTP 200 alone never qualifies a file: PDFs require a signature, closing EOF, strict pypdf parse and positive page count; ZIP/Office files require archive CRC validation without member files being saved; supported text/XML/JSON types require nonempty valid UTF-8 content. Empty, encrypted, truncated and unsupported opaque files remain unqualified. The collector sends a serial HEAD qualification before a separate asset GET; an image MIME declaration is intentionally omitted without a GET. Unsupported HEAD, inaccessible assets, ambiguous extensionless links and asset failures remain explicit incomplete attachment outcomes. Hyperlink ledgers distinguish inventoried nodes, observed other-publication/HTML/statutory references, nonimage attachments and unresolved hyperlinks. Reference links do not certify acquisition of external incorporated texts. There is no blanket claim that every external hyperlink is an attachment, or that every unknown hyperlink is safe to omit. A document-only embed/PDF link is an unresolved primary-text node; preserving its original bytes does not certify normalized legal text.

## Reconciliation and files

- `checkpoint.json`: pinned identity/configuration, exact executed source hashes, ordered raw receipts, resume state and errors; migration provenance when applicable.
- `executed-source/`: exact source at run creation. A migrated run also keeps `prior-executed-source/` and `migration-source-checkpoint.json`.
- `raw/*.bin`: actual ordinary browser DOM/document/fetch/native bytes, or empty HEAD bodies; receipt includes URL, time, transport, status/headers, byte count and SHA-256.
- `inventory.json`, `dispositions.json`: source-derived unique node graph and the own-content, explicit structural, reserved/repealed or unresolved classification of each node.
- `records.jsonl`: one own-body record per stable source ID, with heading/path, parent, legal text, normalized HTML, table HTML with nested tables/spans, notes, links, image placeholders and raw witnesses.
- `records.csv`: corresponding IDs/headings/paths/text/source hashes for portable import. JSONL contains the full structured fidelity fields.
- `link-ledger.json`, `image-omissions.json`: explicit hyperlink boundaries and intentional image reference/placeholder coverage.
- `coverage.json`: independently recomputable text/attachment/edition/jurisdiction claims, missing/extra IDs, unknown empty nodes, conflicts, duplicate witnesses, limits, errors and start/end inventory consistency.
- `runtime.json`, `network-events.json`: tested Python/OS/Chrome/dependency versions and live status chronology.

The read-only verifier checks raw hashes and source snapshots, rebuilds the complete graph and own bodies from retained source, checks all output rows and CSV, rejects duplicate IDs/body conflicts, recomputes link/image ledgers and coverage, and requires source identity plus inventory equality at the end. It does not trust a stored success flag. Identical parent/child raw witnesses are deduplicated into one normalized record; conflicting bodies fail closed. Heading-only empty sections, unknown empty types, unowned legal notes or unowned visuals cannot become successful structural exclusions.

Publisher PDFs and other nonimage attachments are retained as original files; this HTML collector does not claim their image contents were transcribed or that external attached laws have been merged into the primary publication's normalized text.

## Rate controls and stops

All collection is serial within a run. Documents, public fetch/XHR, HEAD and explicit assets use a shared family gate with a minimum 3.5 seconds between starts; ordinary Chrome static resources retain native browser scheduling. The default gate is `/tmp/complisolv-icc-full-gate/{ecode360,municipal.codes}` (override `ICC_GATE_DIR`/`--gate-dir` only as an explicit operator configuration shared by all same-family collectors). HTTP 403/429, `cf-mitigated: challenge`, visible challenge documents and Retry-After are retained as family access stops. There is no automatic retry/reset, alternate fingerprint, imported cookie session, TLS weakening or challenge bypass. A retained access stop needs operator review; do not choose another gate to evade it.

Final tested commands, scope, evidence paths, hashes and limitations are in [validation-summary.json](validation-summary.json). Network-free compact fixture commands are:

```sh
python -m collectors.ecode.cli verify --out collectors/ecode/fixtures/synthetic-ecode
python -m collectors.ecode.cli verify --out collectors/ecode/fixtures/synthetic-municipal
python -m collectors.ecode.tests.verify_live_fixture --fixture collectors/ecode/fixtures/phoenix-charter-stopped.tar.gz
```

The last wrapper expects an accurately incomplete live proof; its `fixture_check_passed` does not change the nested publication `complete=false`. Compact synthetic fixtures and live representative replay details are provided with the validation report. Synthetic fixture tests establish collector/reconciliation behavior; they are not acquisition evidence for any municipality.

## Final representative live outcomes, October 17, 2026

The current-parser selected proofs are `albany-code-qualified-policy` and `phoenix-charter-qualified-policy` under the external evidence root `outputs/full-publication-validation-2026-10-17/ecode`. Both are explicit new-folder **offline replays** after a publisher access stop, with original acquisition receipts, executed source versions and migration ancestry preserved. Neither is a complete-publication success.

Albany (customer AL0934, Code 336787, currency July 6, 2026) reached all 3,253 inventoried HTML nodes: 3,006 owned records, 53 reserved/repealed empty and 194 structural empty. The first required PDF HEAD returned HTTP 403; all six required attachments remain unqualified and no closing edition/inventory check was sent. This proves full traversal of the dynamically discovered HTML inventory, not a complete publication or closing currency consistency. The earlier fresh image-policy transport proof `albany-final-transport` covers Chapter 1's 17 nodes only. Final runtime source changes were independently replayed offline; a fresh final-revision live closing run was blocked by the retained access stop.

Phoenix Charter reached 81 of 279 inventory nodes (73 owned records and 8 structural empty); HTTP 429 at Charter XI left 198 missing. Its currency is the November 6, 2018 election. This is an incomplete selected Charter acquisition, not the general City Code. No municipal.codes request followed that stop. Both family stops require operator review after source access returns; these evidence runs cannot be resumed automatically.

With `ECODE_EVIDENCE` set to the external evidence directory, read-only full-raw verification is:

```sh
python -m collectors.ecode.cli verify --out "$ECODE_EVIDENCE/albany-code-qualified-policy"
python -m collectors.ecode.cli verify --out "$ECODE_EVIDENCE/phoenix-charter-qualified-policy"
```

Each returns exit 2 with `verified=true` and `complete=false`. For a deliberate offline normalization replay, select a new output directory:

```sh
python -m collectors.ecode.cli replay --source "$ECODE_EVIDENCE/albany-code-qualified-policy" --out ./fresh/albany-replay
```

This also returns exit 2 and does not open a browser. The independent project QA additionally reviewed the frozen runtime and tested image policy and cross-family edge cases. The final local suite contains 21 tests; its last change added a valid zero-page PDF rejection assertion within an existing test. See the exact test source hash and source/runtime distinctions in `validation-summary.json`.
