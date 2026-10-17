# Official publication collectors

**Active readiness validation (2026-10-17):** full native Milwaukee6-file/2,300-page and Portland complete Title33/1,855-page proofs have completed. All33PortlandHTMLtitle documents now passed source/owned-body replay (3,168records39tables); Burlington, ArlingtonTX61files, ArlingtonCounty80files and Spokane7,490-section native selections are still completing full-run reconciliation. `validation-summary.json` records current progress and limits; the prior sealed-stage report is `prior-stage-validation-summary.json`. The explicit coordinate-v1 PDF parser is integrated and has five passing independent structure tests; complete County/TX/CivicPlus runs now exercise it. Earlier native/page proofs retain their original stream parser scope.

This standalone adapter inventories and collects the **selected publication** without a default item limit. It covers official full-title HTML, linked title/chapter/section graphs, current linked PDF document sets, a publisher-native single HTML document, and the official Baltimore GitHub HTML archive. It does not assert that an entire jurisdiction's legal corpus is complete. Exact tested scopes and relative retained evidence paths are in `validation-summary.json`.

## Install and run

Qualified runtime: Python 3.12.14, Node 24.19.0, Playwright 1.62.1 and an installed ordinary Google Chrome 155. Python 3.12+ and Node 18+ are the intended portable baseline; other versions have not been independently qualified. The lock uses POSIX `fcntl`, so this release is qualified on macOS/Linux, not native Windows. HTTP-only sources do not need Node or Chrome. Keep the virtual environment and large outputs outside the repository.

From the repository root:

```sh
python3 -m venv /your/runtime/official-venv
/your/runtime/official-venv/bin/python -m pip install -r collectors/official/requirements.txt
npm install --prefix collectors/official
export PYTHON=/your/runtime/official-venv/bin/python
export NODE=/absolute/path/to/node
"$PYTHON" -B collectors/official/collect.py \
  --config collectors/official/configs/baltimore-code.json \
  --out /your/evidence/baltimore-code
```

For a headed-browser source, leave the desktop available. The script launches installed Chrome with its own disposable profile and closes that profile. It uses ordinary public pages and exact observed native links. It imports no cookies, does not disable TLS verification, and never interacts with a challenge. The browser dependency resolves from `collectors/official/node_modules`; an existing external installation can instead be supplied through `NODE_PATH`.

Each output must be new/empty. A complete run returns `0` only at its declared requested coverage level; partial, access-blocked, drifted or unresolved runs return `3`. A native PDF `file_pages` success is deliberately distinct from legal-semantic success.

```sh
# Resume after a durable boundary, using exactly the same config and executed code.
"$PYTHON" -B collectors/official/collect.py \
  --config collectors/official/configs/baltimore-code.json \
  --out /your/evidence/baltimore-code --resume

# Explicit smoke limit: always incomplete, even if the limit happens to equal inventory size.
"$PYTHON" -B collectors/official/collect.py \
  --config collectors/official/configs/arlington-va-current-portal.json \
  --out /your/evidence/county-smoke --max-items 2

# Read-only, network-free evidence replay: returns 0 complete, 3 incomplete/error.
"$PYTHON" -B collectors/official/verify.py /your/evidence/baltimore-code

# Compact retained-source and fault-injection qualification: no live network.
"$PYTHON" -B collectors/official/test_offline.py

# Validate selected final live proofs against the relative-path summary, including
# correctly incomplete runs. This command returns 0 when all declared expectations hold.
"$PYTHON" -B collectors/official/verify_suite.py --evidence /your/evidence/official
```

`--interrupt-after N` deliberately stops after N newly completed, atomically saved items. The offline tests compare an interrupted/resumed run with an uninterrupted run byte for byte at the normalized JSONL level. A previous failed acquisition is retained and is not silently retried. If source identity changes or code/config differs, use a fresh output. `--from-cache /previous/output` may reuse successful hash/source-bound raw item bytes with the same source/inventory/edition config in a NEWoutput (an explicit PDF normalization mode is the only permitted parser-only config difference); it always performs fresh discovery, current-code parsing and every source end check. It never imports a failed response or an old success flag. A source access stop requires an informed operator decision; do not remove gate state to force a retry.

## Configured publications

| Config | Selected publication and acquisition | Qualification and scope |
|---|---|---|
| `portland-code.json` | All linked city-code HTML titles, dynamically discovered `/all` documents | All33HTMLtitle documents source/owned-body replay passed; letteredcitations and repeal/prefix/body/suffix notes preserved. Prior Titles1–2 were bounded. Title 33 remains an explicitly required separate component, preventing all-city-code completion. |
| `portland-title33-complete.json` | Observed July1,2026 complete eFiles Title33 nativePDF | Full1,855-page native acquisition/source-consistency proof completed; legal semantics remain manual review. |
| `portland-zoning-pdfs.json` | All official native PDFs linked by Title 33 landing page | Separate runnable file set; current/future-effective versions are not resolved into one legal edition. Printable eFiles volumes and maps outside this exact set remain separate. |
| `baltimore-code.json` | Official hub-exposed repository, current default branch/commit, entire Code subtree | Full archive download and canonical HTML ownership traversal tested. Model-code stubs and unresolved incorporated nonimage references prevent a complete legal-corpus assertion. |
| `baltimore-charter.json` | Same current archive, separately selected Charter subtree | Runnable whole-subtree config; real Article I fixture qualifies canonical-member and aggregate deduplication. This is not a live full Charter proof. |
| `milwaukee-publications.json` | Six current index-labelled native files: Charter, Volumes 1–3, Salary and Positions | Source-backed index-selection regression; full default file-set collector. Historic unlabelled alternatives are not substituted. Whole six-file/all2,300-page native proof completed; structural PDF qualification continues. |
| `milwaukee-volume2.json` | Entire native Building and Zoning Volume 2 PDF | Full live native-file and all-physical-page proof; no reconstructed legal sections or PDF tables. |
| `burlington.json` | CodePublishing root/Charter/appendices and all observed linked legal documents | Ordinary Chrome and exact underlying native HTML response binding; fresh bounded Charter traversal. Full default graph traversal is runnable, but a full Burlington live corpus was not completed. |
| `arlington-tx-code.json` | Current official alphabetical Code, Charter and UDC linked PDF set | Dynamic whole set, observed native-link flow. Pending ordinances remain a separate legal layer; posted chapter dates can vary. Bounded live acquisition only. |
| `spokane-code.json` | Whole Title/Chapter/Section graph, including embedded UDC | Source-observed SelectAll/ViewSelected Title→Chapter→Section forms provide the full7,490-enabled-section inventory; complete ordinary POST batches are being validated. Title/chapter navigation is never emitted as legal records. Charter is separate. |
| `spokane-chapter-01-01.json` | Explicit Chapter 01.01 Adoption of Code subset | Small genuine chapter-level traversal proof; does not stand for the whole Municipal Code. |
| `worcester-part1.json` | Entire posted Part One PDF, amended through September 8, 2026 | Full live native-file and all-page proof, with edition tokens checked independently from transport. |
| `worcester-publications.json` | Native PDFs linked on official ordinances/regulations index | Runnable full linked document set. This is distinct from the proven Part One file; zoning/Charter are separate. |
| `arlington-va-current-portal.json` | Current Arlington **County** portal's complete observed 80-document inventory | Primary County route. Each native URL is decoded from its observed portal link and must also appear on its actual current detail page before download. Fresh two-file proof; no claim to full 80-file acquisition/current legal consolidation. |
| `arlington-va-posted-chapters.json` | Legacy official posted chapter PDF set | Separately runnable secondary publication. It is never substituted for the current primary portal. |
| `new-orleans-czo.json` | Entire publisher-native `print-all` HTML, observed legal wrapper excluding generated print banner/tool controls | Whole native HTML acquisition/parser tested, with preserved HTML tables. Source-heading/ID segmentation retains1,272bodyrecords and89tables in the retained fullsource trial; fresh fullproof/replay is running. Duplicate printed9-3-C IDs remain distinct source occurrences. ExactState-law citations are separate dependencies; zoning maps are deliberate image omissions. |

For another qualified exact native PDF use mode `pdf`, a unique id/jurisdiction/state/publication, exact HTTPS `source_url`, `coverage_level: file_pages`, and observed edition tokens where available. `pdf_set` requires exact content/inventory selectors and observed URL/label rules. `html_single` requires an exact content selector and a legal marker plus substantive nonheading body; a heading or TOC alone fails. A new site layout or landing page is not automatically a supported adapter. Test source identity and actual legal bodies before adding a dispatch configuration.

## Evidence, reconciliation and source consistency

`config.json`, `checkpoint.json` and `inventory.json` bind source identity, canonical expected URLs, current inventory hash, exact parser/collector source hashes and invocation/runtime metadata. `executed/` contains the actual code copied before network acquisition. Source files and receipts are stored under deterministic request-name hashes in `raw/`. Parsed per-document JSON is in `items/`; `records.jsonl` retains richer HTML, tables, spans, notes, links, source references and provenance than the CSV convenience export.

The read-only verifier independently reconstructs discovery from retained source, rechecks archive CRCs and member hashes, exact source URL/raw-reference/receipt binding, parser output, inventory closure, ownership, duplicate IDs, page coverage, CSV/JSONL agreement, required nonimage attachments and coverage flags. It does not invoke a network fallback. It also rejects swapping two same-byte PDF sources while recomputing cached parse outputs: source identity is checked independently of byte equality.

At the start and end, the collector compares the selected inventory, PDF bytes, whole native HTML semantic projection, or current GitHub branch commit as appropriate. Full nonarchive runs additionally reacquire every individual selected source and downloaded nonimage attachment, comparing native PDF bytes or owned HTML/body and navigation projections. ZIP sources bind all member contents to the pinned immutable commit. Unrelated navigation outside the configured publication selection does not trigger a false edition change. A source change during the run prevents completion; this is a consistency check, not proof that every posted chapter was legally current on the collection date.

The default gate is `/tmp/compliSolv-official-publication-gate` (`OFFICIAL_GATE_DIR` can select a shared deployment location). All scripts/processes share a per-host POSIX lock, nominal 3.5-second start guard, and retained request log. Each HTTP redirect is gated. Browser documents/XHR/fetch use the same gate. HTTP 403/429 or detected challenges persist an operator-release stop, with case-insensitive Retry-After and at least 300 seconds. No retry, cookie transfer, proxy rotation, masking or TLS bypass is implemented. Do not run multiple copies against the same source to evade the shared gate.

## Images and nonimage attachments

The user's image rule is applied during collection: **no separate image downloads or pixel extraction**. HTML `img`, `picture`, `source/srcset`, inline SVG/image/use, image object/embed/data URI, image links and CSS image references become literal `[IMAGE]` in normalized output. Source IDs, source reference attributes, original raw HTML and compact reference hashes/metadata are retained. A missing image is an intentional policy omission, not a required-asset acquisition failure. References can outnumber markers because several responsive sources may represent one visual object.

The browser blocks image resource requests wherever practical, while leaving security/challenge resources enabled. HTTP image responses are not read as image bodies. Opaque extensionless attachments are not automatically fetched because their type has not been qualified; an explicitly incorporated nonimage attachment remains required/unresolved and prevents the appropriate complete claim. A referenced external URL or a 404 alone is never used as a reason to make an attachment optional. Only a specific configured legal-layer/context rule may mark a citation independent, and explicit incorporation overrides that rule.

Original native PDFs may contain images. They are downloaded as the legal source but no separate raster/vector image file is extracted or rendered. Coordinate-v1 places detected raster `[IMAGE]` markers using object geometry and marks detected blank/vector-map pages without rendering or pixel extraction. It retains ordered blocks, physical word IDs, detected table cells/spans and independent PDFium/pdfminer comparison ledgers. General diagram interpretation, arbitrary borderless tables and legally correct reading order remain review. Legacy stream-v1 proofs append raster markers and are labelled accordingly. A PDF page can contain unextracted visual text. `table_count` counts normalized HTML tables and coordinate-v1 detected PDF tables. A legacy stream-v1 PDF count of zero means **not reconstructed**, never absence of source tables. Detection of some PDF tables does not establish that all borderless layouts were detected.

## Coverage meanings and review stops

`publication_file_coverage_complete` means the selected inventory has all native documents with a consistent end state. `pdf_page_extraction_complete` additionally means every physical PDF page has exactly one normalized page record. Neither establishes visible-text accuracy, reading order, legal section segmentation, PDF link annotations, table rows/cells/spans or incorporated standards. `manual_review_required` remains true for PDF pages.

`publication_html_text_coverage_complete` means selected source-owned HTML bodies/navigation closure were reconciled; `legal_semantic_coverage_complete` is stricter and excludes unsegmented documents, heading-only model-code stubs and unresolved required nonimage assets. Baltimore `index.full.html` aggregate alternates are inventoried and explicitly excluded to avoid repeating descendant text. Heading-only publisher source units retain a status/manual-review disposition; the collector never invents text for “As in IBC,” vacant or analogous source stubs. A source's incorporation of another code requires that other legal layer separately.

`requested_coverage_complete` applies only to `requested_level`, with attachments and required separate components also checked. Limits, interruption, missing/extra inventory IDs, unknown ownership/navigation, duplicate records, corruption, page gaps, source drift or required nonimage gaps prevent the corresponding complete outcome. `jurisdiction_complete` is always false. No source index, TOC or homepage counts as a legal record.

## Retained tests and operational limitations

The16-test baseline suite plus5PDF-structure and6readiness-hardening tests uses a real four-page Portland PDF and a real Baltimore Article I ZIP subset plus explicitly synthetic index/transport fixtures. It injects missing items, duplicate output, corrupt raw bytes/ZIP CRC, page gaps, wrong edition/config, lost inventory entries even after rehashing, interrupted runs, forged source-consistency booleans, source-crosswired same-byte PDFs, and interrupted/resumed equivalence. It also tests nested-table ownership, extensionless incorporation, independent citations, image-only legal content, heading-only rejection, no-image-fetch placeholders, six current Milwaukee index selections, exact print-control exclusion versus legal drift, and nonempty/all-page-parse required PDF attachment guards. Compact fixture provenance and hashes are retained.

Full graph collection can be lengthy and source-dependent. Publisher layout changes, blocked browser automation, unavailable documents, unknown attachment formats and TLS trust failures require an explicit incomplete result or operator review. There is no guessed hidden API/export, generic whole-publication operator-import command, or automatic unsupported-site fallback. Existing sealed bounded packages and the database are not changed. Fresh completeSanMateoCode+CharterXML acquisition/replay passed2,652records/50tables, with35image placeholders retained under requested policy; no image transcription is implied. `validation-summary.json` separates current selected proofs from preliminary/failed attempts and gives exact replay expectations.

## Current readiness checkpoint

`READINESS-CHECKPOINT.json` is the compact stable-code/test receipt. `validation-summary.json` is deliberately not frozen while full runs continue. The27network-free tests cover the original integrity/resume faults plus actual16source tablecells, controlled merged cells/two columns/vector-only placeholders, nested image metadata/ownership, exact cached native-download binding, letteredPortland/repeal-note ownership, qualified external statute identity, and complete mixed-parentXMLinclude closure with missing/cyclic/corrupt-tree failures.

Original source configs are `original-{burien-wa,fremont-ca,renton-wa,san-carlos-ca,portland-me,rockland-me,san-mateo-ca}.json`. The four SPA code configs pin the exact observed publication currency at root, each legal page and end checks. The two CivicPlus configs use a browser only for the current official index, then ordinary HTTP for its exact observed native PDF URLs. San Mateo verifies the complete publisher-designated repositoryZIP against every pinned Git blob and traverses all selectedCode/CharterXMLincludes, preserving parent own-content before and after includes. Flagstaffframes and KingCountycurrent title collection are explicit remaining adapter/config gaps at this checkpoint.

Run `test_pdf_structure.py` and `test_readiness.py` alongside `test_offline.py`. `verify.py` additionally returns `pdf_text_table_qa` for coordinate records: extractable-text reconciliation and detected-cell agreement are separate from full file/page coverage and legal semantics. No page/table flag establishes invisible image text or all undetected table layouts.
