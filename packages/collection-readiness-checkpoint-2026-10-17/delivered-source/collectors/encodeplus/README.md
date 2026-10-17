# enCodePlus full-publication collector

This adapter traverses a publication's complete dynamic TOC by default. It replaces the earlier fixed-three-section validator. It supports the Lincoln Municipal Code, Overland Park Municipal Code/UDO, Savannah Code of Ordinances, Fairfax County Zoning Ordinance, and explicit configurations for other enCodePlus publications. Publication coverage is separate from jurisdiction coverage. A full zoning ordinance does not include Fairfax's main county code; a full Lincoln charter does not include its municipal code.

## Install, collect, resume and verify

Python3.12.14/macOS26.6.2arm64 was tested. Python3.10+ and POSIX flock are required; other operating systems were not live validated. Run from the repository root:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r collectors/encodeplus/requirements.txt
.venv/bin/python -B -m collectors.encodeplus.collect lincoln --out /data/NEW-lincoln
.venv/bin/python -B -m collectors.encodeplus.collect lincoln --out /data/NEW-lincoln --resume
.venv/bin/python -B -m collectors.encodeplus.verify /data/NEW-lincoln
.venv/bin/python -B -m collectors.encodeplus.tests
```

Named keys are in `targets.json`. No hardcoded provision IDs select the collected corpus. `--max-items N` is an explicit acquisition-block limit, not a provision count: one container response can include hundreds of source nodes. **Any requested limit forces an incomplete result**, even if that block happens to contain every node. `--skip-assets` explicitly prevents attachment completeness. Default runs have neither limit.

Secondary publications use an explicit pinned config with `base`, `identity`, `jurisdiction`, and `scope`; `base` must be the HTTPS publication directory ending in `/`. An exact live TOC identity match is required before legal-body acquisition. The City Charter config was populated from the observed publisher TOC:

```sh
.venv/bin/python -B -m collectors.encodeplus.collect lincoln-charter --config collectors/encodeplus/configs/lincoln-charter.json --out /data/NEW-charter --native-export
```

Do not invent labels for unqualified secondary publications. Inspect the linked publication's public TOC, supply its exact identity explicitly, and retain the discovery evidence. A new config does not imply that publication has already passed live validation.

## Inventory, ownership and hierarchy

The collector obtains the entire publication TOC, pins its exact identity and normalized inventory hash, then requests the first unaccounted source ID. A normal container response can contain descendants; all observed `section[data-secid]` IDs in that body are inventoried. TOC nodes and embedded body nodes are counted separately. Subsequent requests skip already owned IDs. Every requested `#thePage/@secid` must match the requested ID.

Canonical hierarchy comes from the publisher's body section classes (such as `_001 _001-013`), actual nested section ancestry, and response breadcrumbs. It does not trust Lincoln's malformed declared TOC depths. Flat sibling sections with body hierarchy classes are mapped to their observed source IDs. Source TOC label/body-heading differences are retained as explicit dispositions; canonical source body headings take precedence. Legitimate headless sections retain their TOC label or definition label with `heading_source`, or explicitly record absence of a source heading. They are not dropped.

Each normalized record owns only its section's body. Descendant `section` elements are removed from that owned body; navigation mini-TOCs are excluded from substantive text and retained in owned source HTML with a disposition. An empty leaf cannot pass as an operative record: emptiness requires explicit source container ancestry/has_children or a literal reserved/repealed/omitted disposition. Other empty leaves remain `source_empty_unresolved` records so traversal can continue, but the verifier blocks publication text completeness. A bare Article/Chapter/Title heading does not prove that an empty node is structural. Publisher ancestor heading stubs outside the selected canonical subtree supply paths only and never duplicate acquired bodies. Inline text joins preserve the original font/span boundaries without inserting spaces inside words; DOM blocks and BR elements supply text boundaries. Normative definition prose placed inside a heading is retained as body text with an explicit ownership flag. Unowned substantive text or asset references outside the source sections fail closed; only explicitly recorded publisher branding/script/style controls are omitted. Unknown structures remain raw failure evidence.

Records retain source IDs, headings/provenance, paths/parent IDs, legal/descriptive text, owned HTML, body hash, tables with cell markup/text/th/td/rowspan/colspan, links and all attributes, notes, lists, null/sentinel metadata dispositions and raw source locators/hashes. A record can be a structural container, descriptive/legal body, or explicit reserved/repealed disposition. Counts must be read with those units. Graphic-only nodes retain source identifiers/headings and reference metadata with literal `[IMAGE]` text. Images are intentionally skipped under the user policy; no image OCR or separate image-byte acquisition is performed.

## Assets, edition consistency and stopping

**Current user image policy:** img/picture, inline SVG, image source/srcset, image data URIs, CSS image URLs, video posters and linked image files normalize to the literal `[IMAGE]`. Graphic URL/alt/source metadata remains in `image_refs`; image data-URI payloads are represented by hashes rather than copied into normalized output. Active graphic elements, poster attributes and image CSS URLs are removed. No separate images are requested, downloaded or extracted. If an extensionless nonimage-document request returns image Content-Type, the transport reads headers but leaves its body unread and records an intentional image skip; re-normalization applies the placeholder. Intentional skips are not missing required assets. Original native PDFs may contain publisher images and remain original publisher files.

Required **nonimage** references include linked PDF/Office/ZIP/download-library documents and source-explicit adopted/incorporated maps/documents at extensionless URLs. Ordinary internal code cross-references do not trigger arbitrary document crawling. Unresolved HTML document landing pages, missing nonimage assets and required failures prevent attachment completeness. Tests cover source-explicit extensionless incorporation rather than assuming file extensions identify every legal attachment.

Historical pre-policy JPEG evidence is retained unchanged in earlier evidence runs and explicitly superseded; it is not evidence of current collector behavior. Current image-policy runs contain no separate image bytes.

All requests use the shared serial gate configured for3.5seconds `/tmp/compliSolv-encodeplus-rate-gate` (override `ENCODEPLUS_GATE_DIR` identically across workers). Redirect requests are separately gated. HTTP429 persists Retry-After with a minimum300seconds. Challenges/401/403 persist a stop, with no automatic retry, reset, proxy or identity rotation. Publisher host identity is the exact set `online.encodeplus.com`, `codes.opkansas.org`; other asset hosts have separate persistent stop/cooldown scopes while using the same request-spacing lock. An external refusal must not be misclassified as a publisher refusal. No stop is automatically cleared.

The publisher exposes no reliably qualified global edition ID in these inspected publications. This collector pins an **observed snapshot**, not an official legal current-through edition. Closing checks fetch the TOC and every acquired body block again and compare the reconstructed legal content. TOC or body drift prevents text completeness. `edition_complete` and `jurisdiction_complete` remain false; they are not inferred from stable transport. Graphic/legal attachment semantic coverage remains separately qualified.

## Checkpoints and output contract

Use new/unpopulated output directories. Files/checkpoints use atomic replacement. The checkpoint binds target config, exact acquisition/normalizer/verifier source versions, TOC identity/hash, every acquired block hash/ID list, asset URL/hash, options and phase. Exact executed script bytes are copied into `script-versions/` before network access. Existing cache files require complete receipts, exact URL/status/hash and current pinned config. Corrupt/mismatched caches fail closed. A later explicit resume may create one new immutable `.attempt-N` file for a network timeout or HTTP429; original failed bytes/receipts remain unchanged. Persistent stops, challenges, nontransient HTTP failures and redirect loops never become retryable. Shared cooldown/host stops are still checked before opening any new request. A collector version mismatch fails by default. An explicit `--resume --upgrade-code` validates retained request hashes and captured scripts, preserves the prior checkpoint by SHA in `checkpoint-history/`, snapshots the current implementation, reparses every retained body, and obtains fresh closing checks. It never silently accepts earlier success flags or normalization. The current config/options must still exactly match. A newer read-only verifier may recompute historical raw evidence, but changed normalized semantics must match delivered bytes or fail.

An interruption after a durable block checkpoint resumes without duplicating records. A not-finished resumed run gets fresh closing-check paths/generation; previous end checks do not satisfy its new interval. A finished resume is a read-only verification. All prior failures remain in the checkpoint history. `--interrupt-after N` is an explicit test hook that stops after N durable blocks.

Files include `checkpoint.json`, `inventory.json`, start/end raw HTML and receipts, raw container responses, asset bytes/receipts, `records.jsonl`, `records.csv`, and `coverage.json`. The verifier validates the exact captured acquisition snapshots, then ignores stored success flags and rebuilds inventory, ownership, record contents, duplicates/missing IDs, assets and start/end equality directly from retained evidence. Its default mode writes nothing and uses no network. Exit0 requires publication text/source traversal and required attachment byte coverage; exit2 means incomplete. A record's raw source locator refers to a retained response rather than duplicating an entire descendant corpus into each parent record.

Coverage fields separately report `publication_text_complete`, `attachments_complete`, `edition_complete`, `jurisdiction_complete`, explicit limits, missing IDs/assets, embedded IDs, duplicate-source dispositions, structural/body counts and source-heading differences. “Publication text complete” means the entire observed publication source-node set is accounted and stable; it does not mean graphic text has been transcribed or codewide legal currency established. `[IMAGE]` intentionally marks graphic content without transcribing it.

## Native full export

`--native-export` uses only an observed Export PDF control and its observed current application mapping, then the normal status/poll/file-token workflow (or direct PDF response). Large native exports have a bounded600-second/30-poll wait. Each explicit resumed export attempt retains separate poll paths; failed or timed-out receipts are never overwritten. This option can be slow and its failure is reported separately from source-node coverage. A native full-scope request is qualified only when its observed root body key spans the complete acquired canonical graph and every TOC ID. The root API may emit just its own heading while descendant API responses supply its full source subtree; that does not turn a partial unrelated root into a whole-publication export. The TOCroot `000` export is explicitly rejected as a full-publication export: it can produce only a TOC PDF. If no single observed body control covers the publication, the option reports unavailable rather than guessing an endpoint or concatenating partial exports.

Native files remain separate from record traversal. Independent offline checks validate source control, container ID coverage, PDF bytes/publication metadata, body headings, per-record text anchors and table-cell text presence. Anchor agreement does not prove pixelwise layout, graphic semantic equivalence, or all official edition relationships. The final coverage reports those limits even when a genuine full-scope PDF downloaded successfully.

## Validation and remaining scope

See `validation-summary.json` for exact final executed commands, runtime, measured live scopes, evidence hashes and full-versus-bounded distinctions. Large live evidence stays outside this collector directory. Earlier wave3/full-publication-validation packages remain sealed; active readiness evidence is separately labeled in the current summary. Compact fixtures are actual observed Lincoln Access Management Policy TOC/body captures; tests mock transport and asset bytes, so they are explicitly **retained-source/synthetic-transport tests**, not additional live collection passes.

The network-free suite tests full dynamic14-node reconciliation with six real source tables and canonical map ancestry, missing/duplicate/corrupt/wrong-publication/end-drift/interrupted/missing-asset failure cases, corrupt resume rejection, explicit limits, unowned text/empty leaf guards, SVG/srcset assets persistent independent host stops, incorporated extensionless nonimage references, image placeholders, and unread image response bodies. Resumed versus uninterrupted JSONL/CSV must be byte-identical. The current-code whole Charter integration is qualified separately below. Full primary-publication runs remain active, and other separate publication families are not all live validated; full coverage cannot be inferred from a bounded smoke or this reusable implementation.

### Current image-policy qualification

Earlier final-policy live publication checks use the historical `no-images-*` evidence runs; the current-code Charter v4 and native-document runs are qualified separately below. Lincoln City Charter covers all188 source nodes across17 acquired and17 closing container responses, with no discovered required nonimage assets; its coverage is publication-only and does not establish codewide legal currency. Lincoln Access Management Policy covers14 source nodes, replaces its map with `[IMAGE]`, downloads zero separate images, and retains the required external Syracuse PDF failure as a nonimage attachment gap. A genuine17-page publisher PDF remains an original native file, permitted to contain publisher graphics.

Earlier `qualified-*` image downloads and reports remain historical superseded evidence. Current-policy primary-target normalization replays are explicitly retained-evidence tests, not additional live acquisitions. Use the exact run/replay scope labels in `validation-summary.json` when citing results.

### Required document byte integrity

Required nonimage attachments must contain nonempty bytes. A PDF identified by URL, MIME or header must have a PDF header/EOF marker and pass strict pypdf parsing with a readable, nonempty page tree and readable content streams; encrypted or truncated/unparseable PDFs remain unqualified and missing from successful asset coverage. Collection records qualification before accepting an asset, and read-only verification repeats the document checks from retained bytes instead of trusting a stored qualification. Rehashed empty/truncated-file faults therefore cannot pass. Other non-PDF binaries receive only a nonempty-byte qualification; this does not assert their semantic completeness or validate every document format. These checks do not read, download or extract image bodies.

## Current-parser retained-evidence derivatives

To assess a new parser without altering an earlier sealed source package, use a new derivative directory:

```sh
.venv/bin/python -B -m collectors.encodeplus.replay /sealed/OLD --out /data/NEW-derivative
.venv/bin/python -B -m collectors.encodeplus.verify /data/NEW-derivative
```

Replay verifies retained raw/receipt hashes, copies the original source evidence and script snapshots, retains the original checkpoint under its SHA, records explicit offline lineage, and regenerates normalization. It makes zero network requests and does not refresh source closing checks. The resulting proof is a retained-source derivative, not a fresh live acquisition. Existing outputs cannot be used as the derivative destination.

The active readiness phase uses `outputs/collection-readiness-2026-10-17/encodeplus` outside the repository. Earlier full-publication and wave3 source seals remain immutable. Fresh primary runs and dependency discovery must be read from the current phase's validation summary; the earlier Charter/Access Management proofs do not establish municipal-code coverage. A separately published manual dependency remains separate from parent zoning text coverage, and a linked cover section does not satisfy the entire manual.

## Readiness checkpoint: current-code evidence and unresolved scope

The final narrow image-policy revision passed24 network-free source/fault tests; the exact log is [proofs/readiness-24-tests.log](proofs/readiness-24-tests.log). The earlier23-test log remains retained. These are not24 live acquisitions. The final delta classifies object/embed/source image MIME values case-insensitively, including extensionless uppercase `IMAGE/PNG` objects; the real-parser regression requires two placeholders, no required document, no copied data-image pixels and no active image element. A separate original-raw Chrome DOM audit of the full Fairfax Zoning derivative compared282tables/12,568cells and found zero text/tag/rowspan/colspan/count mismatches. The retained452- and46-mismatch reports show the corrected inline-font word joins and narrowly validated hidden date sort keys. Only equivalent hidden ISO/visible US dates are omitted from substantive text; original raw and owned HTML plus a cell omission ledger remain available.

The actual standalone shared-launcher Charter v4, captured immediately before the narrow uppercase HTML image MIME fix, passed acquisition and offline verification with188source nodes,174owned bodies,14structural containers,17opening and17closing blocks, no missing IDs, no source/runtime drift and zero separate images. Compact source/coverage/image receipts are in `proofs/charter-v4-*`; full evidence is `outputs/collection-readiness-2026-10-17/ops/live-charter-unified-v4`. This is a whole City Charter publication proof. It does not include Lincoln Municipal Code or establish global legal currency/jurisdiction coverage.

Full Lincoln Municipal Code, Overland Park, Savannah and Fairfax Public Facilities Manual acquisitions are safely paused for this checkpoint after draining active HTTP requests under the shared lock. Their exact code/checkpoint histories remain retained; a later resume must explicitly upgrade and revalidate the narrow image fix. Their interim acquisition sizes are6,714/6,279/5,674/624body IDs respectively; final closing/source/document acceptance remains pending in this checkpoint. Full Fairfax Zoning source743nodes reconciles, but its required facilities-manual dependency and that manual's external standards remain separate. Do not read an active checkpoint or full TOC as a completed legal corpus.

The first ordinary Lincoln official redirect returned403 at `https://www.lincoln.ne.gov/city/attorn/designs/ds385.pdf`. The exact external host stop and refusal evidence persist; the collector does not switch browser/proxy/aliases to evade it. Many required linked Lincoln documents remain blocked. Overland's interim source capture had5required documents acquired and4failed. AMM's exact ITE Syracuse reference remains unavailable with original DNS/stop history; newer or paid ITE editions are not substituted. `[IMAGE]` graphic omissions are intentional and are not these missing nonimage-document failures.

## Separately published native documents

Six exact current Overland UUID documents have SHA/page-pinned configs `configs/native-82-*.json`. Use the narrow native-document mode rather than pretending these PDFs have an HTML TOC:

```sh
.venv/bin/python -B -m collectors.encodeplus.native_document --config collectors/encodeplus/configs/native-82-4b983dc51ab6.json --out /data/NEW-solid-waste
.venv/bin/python -B -m collectors.encodeplus.native_document --verify /data/NEW-solid-waste
```

`--resume` requires the same config/implementation. Original source and closing bytes must match the qualified file SHA and physical page count. A changed publisher file fails closed pending edition requalification. Native-mode exit0 means `native_document_complete` and `source_page_traversal_complete`; it does **not** mean `publication_text_complete` or legal/table/reading-order completeness. Those semantic dimensions remain false or explicitly require review.

The final-code fresh6-page solid-waste regulations run passed whole-file/each-page capture and independent extractable-text reconciliation. Its relocated read-only verifier exited0; before/after hashes showed both original and temporary relocated evidence unchanged. The compact receipt is `proofs/native-solid-waste-relocated-verification.json`. It contains no detected tables and does not prove table-detection universality. Additional whole native-file/page runs passed the1-page Regulating Plan,1-page Street Sections and62-page Infrastructure Manual. Infrastructure has18detected tables/616cells and4review pages; extractable-text and detected-cell reconciliation are false, so it remains concretely unqualified for those dimensions. The224-pageSTO run was paused after opening-byte capture;172-pageUPOC had not started. All were captured before the narrow HTML image MIME fix using the unchanged pure PDF parser; no normalized legal semantics are inferred. All detected native table cells receive independent bounded PDFium character checks, with source-word ownership and review conditions retained. Raster/vector content is represented by `[IMAGE]` without pixel extraction, rendering or OCR; original native PDFs remain original source files. The pure offline PDF parser is copied and hash-attributed in `PDF-PARSER-PROVENANCE.json`; no official-family transport is imported.

Requirements pin the tested BeautifulSoup/Brotli/PyPDF/fontTools/pdfplumber/PDFium/pdfminer versions. Source/requirements and actual installed package versions are captured in each current run. Code/dependency drift during a live run fails closed; deliberate upgrades preserve the prior checkpoint/scripts, reparse retained bytes and obtain new closing checks. Read-only verifiers use no network and do not modify evidence. See [validation-summary.json](validation-summary.json) for this checkpoint's exact sources, active statuses, tested runtime, commands and limitations.

The current PDF parser conservatively retains concrete text/table review conditions, including possible overlapping table-candidate text and independent-engine glyph differences. Its author is evaluating a later parser separately; that unqualified prototype is not part of this frozen checkpoint. Intentional `[IMAGE]` omissions alone do not cause completeness failure.

The retained timing audit observed259shared-gate request starts after the preceding frozen boundary: configured3.5seconds, minimum actual start interval3.112757seconds, no interval below the original3-second floor and no429. Atomic state persistence before the request timestamp causes the nominal jitter. The transport is intentionally unchanged in this checkpoint; a timing correction is deferred until checkpoint capture. See `proofs/gate-timing-qualification.json`.
