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

Each normalized record owns only its section's body. Descendant `section` elements are removed from that owned body; navigation mini-TOCs are excluded from substantive text and retained in owned source HTML with a disposition. An empty leaf cannot pass as an operative record: emptiness requires explicit source container ancestry/has_children or a literal reserved/repealed/omitted disposition. Unowned substantive text or asset references outside the source sections fail closed; only explicitly recorded publisher branding/script/style controls are omitted. Unknown structures remain raw failure evidence.

Records retain source IDs, headings/provenance, paths/parent IDs, legal/descriptive text, owned HTML, body hash, tables with cell markup/text/th/td/rowspan/colspan, links and all attributes, notes, lists, null/sentinel metadata dispositions and raw source locators/hashes. A record can be a structural container, descriptive/legal body, or explicit reserved/repealed disposition. Counts must be read with those units. Graphic-only nodes retain source identifiers/headings and reference metadata with literal `[IMAGE]` text. Images are intentionally skipped under the user policy; no image OCR or separate image-byte acquisition is performed.

## Assets, edition consistency and stopping

**Current user image policy:** img/picture, inline SVG, image source/srcset, image data URIs, CSS image URLs, video posters and linked image files normalize to the literal `[IMAGE]`. Graphic URL/alt/source metadata remains in `image_refs`; image data-URI payloads are represented by hashes rather than copied into normalized output. Active graphic elements, poster attributes and image CSS URLs are removed. No separate images are requested, downloaded or extracted. If an extensionless nonimage-document request returns image Content-Type, the transport reads headers but leaves its body unread and records an intentional image skip; re-normalization applies the placeholder. Intentional skips are not missing required assets. Original native PDFs may contain publisher images and remain original publisher files.

Required **nonimage** references include linked PDF/Office/ZIP/download-library documents and source-explicit adopted/incorporated maps/documents at extensionless URLs. Ordinary internal code cross-references do not trigger arbitrary document crawling. Unresolved HTML document landing pages, missing nonimage assets and required failures prevent attachment completeness. Tests cover source-explicit extensionless incorporation rather than assuming file extensions identify every legal attachment.

Historical pre-policy JPEG evidence is retained unchanged in earlier evidence runs and explicitly superseded; it is not evidence of current collector behavior. Current image-policy runs contain no separate image bytes.

All requests use the shared serial3.5-second gate `/tmp/compliSolv-encodeplus-rate-gate` (override `ENCODEPLUS_GATE_DIR` identically across workers). Redirect requests are separately gated. HTTP429 persists Retry-After with a minimum300seconds. Challenges/401/403 persist a stop, with no automatic retry, reset, proxy or identity rotation. Publisher host identity is the exact set `online.encodeplus.com`, `codes.opkansas.org`; other asset hosts have separate persistent stop/cooldown scopes while using the same request-spacing lock. An external refusal must not be misclassified as a publisher refusal. No stop is automatically cleared.

The publisher exposes no reliably qualified global edition ID in these inspected publications. This collector pins an **observed snapshot**, not an official legal current-through edition. Closing checks fetch the TOC and every acquired body block again and compare the reconstructed legal content. TOC or body drift prevents text completeness. `edition_complete` and `jurisdiction_complete` remain false; they are not inferred from stable transport. Graphic/legal attachment semantic coverage remains separately qualified.

## Checkpoints and output contract

Use new/unpopulated output directories. Files/checkpoints use atomic replacement. The checkpoint binds target config, exact acquisition/normalizer/verifier source versions, TOC identity/hash, every acquired block hash/ID list, asset URL/hash, options and phase. Exact executed script bytes are copied into `script-versions/` before network access. Existing cache files require complete receipts, exact URL/status/hash and current pinned config; corrupt/failed/mismatched cached requests are not accepted. Collector upgrades require a new acquisition output rather than silently reusing checkpoints. A newer read-only verifier may recompute historical raw evidence, but changed normalized semantics must match delivered bytes or fail; this does not permit collector resume across versions.

An interruption after a durable block checkpoint resumes without duplicating records. A not-finished resumed run gets fresh closing-check paths/generation; previous end checks do not satisfy its new interval. A finished resume is a read-only verification. All prior failures remain in the checkpoint history. `--interrupt-after N` is an explicit test hook that stops after N durable blocks.

Files include `checkpoint.json`, `inventory.json`, start/end raw HTML and receipts, raw container responses, asset bytes/receipts, `records.jsonl`, `records.csv`, and `coverage.json`. The verifier validates the exact captured acquisition snapshots, then ignores stored success flags and rebuilds inventory, ownership, record contents, duplicates/missing IDs, assets and start/end equality directly from retained evidence. Its default mode writes nothing and uses no network. Exit0 requires publication text/source traversal and required attachment byte coverage; exit2 means incomplete. A record's raw source locator refers to a retained response rather than duplicating an entire descendant corpus into each parent record.

Coverage fields separately report `publication_text_complete`, `attachments_complete`, `edition_complete`, `jurisdiction_complete`, explicit limits, missing IDs/assets, embedded IDs, duplicate-source dispositions, structural/body counts and source-heading differences. “Publication text complete” means the entire observed publication source-node set is accounted and stable; it does not mean graphic text has been transcribed or codewide legal currency established. `[IMAGE]` intentionally marks graphic content without transcribing it.

## Native full export

`--native-export` uses only an observed Export PDF control and its observed current application mapping, then the normal status/poll/file-token workflow (or direct PDF response). A native full-scope request is qualified only when its **body container covers every TOC ID**. The TOCroot `000` export is explicitly rejected as a full-publication export: it can produce only a TOC PDF. If no single observed body control covers the publication, the option reports unavailable rather than guessing an endpoint or concatenating partial exports.

Native files remain separate from record traversal. Independent offline checks validate source control, container ID coverage, PDF bytes/publication metadata, body headings, per-record text anchors and table-cell text presence. Anchor agreement does not prove pixelwise layout, graphic semantic equivalence, or all official edition relationships. The final coverage reports those limits even when a genuine full-scope PDF downloaded successfully.

## Validation and remaining scope

See `validation-summary.json` for exact final executed commands, runtime, measured live scopes, evidence hashes and full-versus-bounded distinctions. Large live evidence stays in the separately sealed full-publication-validation package, outside this collector directory. Compact fixtures are actual observed Lincoln Access Management Policy TOC/body captures; tests mock transport and asset bytes, so they are explicitly **retained-source/synthetic-transport tests**, not additional live collection passes.

The network-free suite tests full dynamic14-node reconciliation with six real source tables and canonical map ancestry, missing/duplicate/corrupt/wrong-publication/end-drift/interrupted/missing-asset failure cases, corrupt resume rejection, explicit limits, unowned text/empty leaf guards, SVG/srcset assets persistent independent host stops, incorporated extensionless nonimage references, image placeholders, and unread image response bodies. Resumed versus uninterrupted JSONL/CSV must be byte-identical. Production runs across every named target and all their separate publication families remain untested; full coverage cannot be inferred from a bounded smoke or this reusable implementation.

### Current image-policy qualification

The final-policy live publication checks use the `no-images-*` evidence runs. Lincoln City Charter covers all188 source nodes across17 acquired and17 closing container responses, with no discovered required nonimage assets; its coverage is publication-only and does not establish codewide legal currency. Lincoln Access Management Policy covers14 source nodes, replaces its map with `[IMAGE]`, downloads zero separate images, and retains the required external Syracuse PDF failure as a nonimage attachment gap. A genuine17-page publisher PDF remains an original native file, permitted to contain publisher graphics.

Earlier `qualified-*` image downloads and reports remain historical superseded evidence. Current-policy primary-target normalization replays are explicitly retained-evidence tests, not additional live acquisitions. Use the exact run/replay scope labels in `validation-summary.json` when citing results.

### Required document byte integrity

Required nonimage attachments must contain nonempty bytes. A PDF identified by URL, MIME or header must have a PDF header/EOF marker and pass strict pypdf parsing with a readable, nonempty page tree and readable content streams; encrypted or truncated/unparseable PDFs remain unqualified and missing from successful asset coverage. Collection records qualification before accepting an asset, and read-only verification repeats the document checks from retained bytes instead of trusting a stored qualification. Rehashed empty/truncated-file faults therefore cannot pass. Other non-PDF binaries receive only a nonempty-byte qualification; this does not assert their semantic completeness or validate every document format. These checks do not read, download or extract image bodies.
