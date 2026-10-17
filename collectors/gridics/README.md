# Gridics native-tree collector

The current adapter preserves every root in the publisher's native inventory, its descendants, source IDs, owned bodies and child order. It acquires the complete native subtree before waiting for an independent rendered section, then repeats the traversal in a fresh context to check full opening/closing native JSON equality. It uses installed headed Chrome through Python Playwright and does not require Codex.

**Live collection is currently stopped.** A source-linked Cupertino Water-Efficient Landscape Checklist PDF HEAD returned HTTP 403 at 22:21 UTC on October 17, 2026. No body was saved by that probe. The persistent published workflow advisory is checked before browser startup/output creation; missing or altered advisory packaging cannot release the known stop. This refusal concerns the exact PDF request; availability of other legitimate routes after the stop is untested. Do not clear or retry the stop automatically. Offline replay and verification remain available.

## Offline use

Install the repository's [integrated runtime](../ops/README.md). Normalize retained evidence into a **fresh** derivative directory, then verify that derivative:

```sh
.collection-runtime/venv/bin/python -B -m collectors.gridics.collect replay \
  --config collectors/gridics/configs/miami.json \
  --source /absolute/path/to/retained-miami-source \
  --out /absolute/path/to/fresh-miami-derivative
.collection-runtime/venv/bin/python -B -m collectors.gridics.collect verify \
  --config collectors/gridics/configs/miami.json \
  --out /absolute/path/to/fresh-miami-derivative
```

Use `configs/cupertino.json` for Cupertino and `configs/miami-comprehensive-plan.json` for the separate Miami Comprehensive Neighborhood Plan. The source argument must contain the bound original acquisition, native responses and opening/closing checkpoints. Replay preserves those originals and writes a derivative with exact normalization-source lineage. The historical comparison helper in an evidence package is not the operational entry point.

An incomplete selected publication returns exit `2`, including a correctly verified derivative with known legal/format/attachment gaps. Exit `0` requires every selected-publication criterion to pass. No current Gridics publication is promoted complete. The `collect` action remains in the CLI for legitimate future acquisition, with `--resume` requiring identical source/configuration and validated retained bytes; the current published stop prevents it from starting a browser.

## Current validation

The controlled source-first/list v2 promotion changed only its approved runtime/new-test/fixture whitelist. The previous 57-file production source snapshot is preserved in the promotion evidence. All historical [validation-summary.json](validation-summary.json), proof receipts and earlier derivatives remain unchanged. Current results are recorded separately in [followup-validation.json](followup-validation.json).

The frozen candidate passed **62 tests**. The promoted production suite passed **65 tests in 47.599 seconds**, including three preserved root-owned access-stop tests. The exact test receipt/log are under [proof-receipts/source-first-list-v2](proof-receipts/source-first-list-v2/tests.json). Full retained-source derivatives passed for both previously acquired publications:

| Retained publication | Roots / records | Raw lists / classed lists | Explicit marker gaps / affected owners | Complete |
| --- | ---: | ---: | ---: | --- |
| Miami, document 45 | 32 / 828 | 1,107 / 405 | 408 / 161 | false |
| Cupertino, document 75 | 22 / 2,687 | 1,948 / 1,247 | 1,247 / 973 | false |

For every record, those derivatives preserved canonical legal HTML apart from newly retained list attributes, source IDs, citations, body ownership, source order and hashes. Independent raw BodyM list enumeration verified list inventory/classes/item counts/source hashes. Full opening/closing native trees match exactly. Original source files remained unchanged, and normalized no-image audits passed with zero separate image downloads. These are **offline derivatives of bound live captures**, not a new live execution of the amended acquisition loop.

The source-bound actual Miami table regression also confirms the repaired boundary between `Transit Corridors:` and `NW 7th Avenue` while preserving inline word joins. Older outputs retain their failed text. The new source-first acquisition loop and observed-stylesheet capture path have offline fixture/transport tests; fresh live integration remains blocked by the publisher stop.

## Source and formatting qualification

A source heading owns its immediate body blocks. Descendant provisions remain separate; text is not duplicated into parents. Unknown or absent headings/types are retained with raw source-field hashes and explicit qualification errors, without inventing labels. Native-only roots retain their complete tree and a diagnostic DOM hash. An exact renderer captured in the same phase/epoch is required to classify a root as source-unrenderable; otherwise normal DOM navigation must be attempted and an unavailable witness reported after timeout. Neither disposition can establish full rendered/legal completeness.

The separate Miami Comprehensive Neighborhood Plan has 49 inventory roots. Its original live run stopped at an unlabeled root. A pre-stop ordinary-browser diagnosis retrieved **104 native nodes / 52 body owners** containing operative Education provisions, although the exact retained public client cannot expose that root as section DOM. The complete actual-root fixture is retained and tested. The root must not be discarded or called an empty container; full49-root acquisition and rendered qualification remain unvalidated.

List metadata preserves source classes, style/counter attributes, item order and a source-list SHA. Explicit square/circle/disc/none markers are not converted into decimal numbers. Custom classes such as `paren-value-paren`, `value-paren`, `style-square`, `parenthesis` and `default-style` remain in normalized HTML and metadata. Their punctuation is not guessed from a class name. Missing stylesheet definitions, unsupported counters and malformed per-item formatting produce `source_unqualified` records and `coverage.list_marker_qualification_gaps`.

No embedded style definitions for these classes were present in the audited original BodyM source. Earlier captures did not retain the external stylesheet bodies. A future authorized run retains only **actually observed first-party stylesheet responses**, bound to their URL, owner document, phase, epoch, timestamp, MIME, bytes and SHA. It does not discover/fetch CSS URLs or import CSS image assets. CSS remains original source; retaining it alone does not qualify marker rules (`marker_rules_interpreted=false`). No stylesheet request was made to work around the stop.

The inventory/currentness fields are narrower than legal completeness. `native_inventory_capture_complete` means the observed opening/closing inventories and trees were retained and reconciled. Historical `native_source_complete` indicates stable captured native trees/records. Neither qualifies headings, marker punctuation, independent DOM, required documents or legal semantics. Separate text, source-qualification, rendered-QA and attachment flags remain explicit. Two Miami and five Cupertino empty source entries remain unresolved, alongside external/reference gaps. Required appendices are not waived. Only the source-explicit top-level `COMPREHENSIVE ORDINANCE LIST` with matching bibliographic columns/labels is classified as an ordinance reference inventory; separate uncodified documents are not claimed collected. No whole-jurisdiction completeness is claimed.

## Image policy and offline checks

All image handling follows [IMAGE-POLICY.md](../IMAGE-POLICY.md). Image/font/media requests are blocked where practical. Known image MIME is rejected before response-body reading; a misleading MIME with an image signature is not saved. Normalized images, image-only legal bodies, CSS images and video posters use exact `[IMAGE]`, with source IDs, headings, captions and positions retained. Omission/list metadata hashes embedded data-image payloads instead of copying them. Original legal HTML/JSON/PDF/CSS may contain embedded source image references; no separate image binaries are downloaded, decoded, extracted or OCRed.

Run the current offline family suite from the repository root:

```sh
.collection-runtime/venv/bin/python -B -m unittest discover -s collectors/gridics/tests -v
```

The tests include complete actual publisher-root fixtures, all original inventory IDs for the unrenderable-root case, unknown/malformed source preservation, native/DOM/revision/phase/epoch integrity, raw opening/closing differences, list marker behavior, image-free normalization/body guards, stylesheet response selection, and access-stop tripwires before any browser/network startup. The shared rate gate remains `~/.local/state/local-jurisdiction-collection/gridics`, with at least 3.5 seconds between first-party document/XHR/fetch/stylesheet requests and a persistent stop for HTTP 401/403/429. No cookies are imported, browser identity masking is not used, and publisher challenges are not circumvented.
