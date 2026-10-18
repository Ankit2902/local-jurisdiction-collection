# Manchester whole native publication method

This isolated method selects the two whole source-published documents covered by the catalog's separate zoning/subdivision candidate: the 78-page **Subdivision and Site Plan Review Regulations** and the 258-page **Zoning Ordinance**, for 336 physical pages. `config.json`, `native-pins.json` and the frozen runtime describe that exact scope. Execution and verification outcomes are recorded separately; an active job or opening download is not a terminal full-publication result.

The source chain is the exact official Business Center Ordinances and Regulations page, its observed Planning and Community Development Regulations link, and the eight native PDF links in `#dnn_ctr8908_HtmlModule_lblContent`. The complete source-group ledger is `inventory.json`: seven current linked files and one explicitly superseded 2001 zoning ordinance. The two different bylaw links retain their Planning Board and Zoning Board source groups. Five other current regulation/bylaw files are separately inventoried; this selected method does not acquire or establish their relationship to the primary code.

The selected zoning original is 80,843,774 bytes, SHA-256 `830db70eef13a8339687d01a7e313083f1f526e90c8b0aeba787d892f63041c2`. Its native cover says ordained December 16, 2025 and effective March 1, 2026. The subdivision original is 2,625,517 bytes, SHA-256 `b6d48e782ec50becd5846695e208e5ecd1d8a0bd5623c8e0249efad23701f8ab`; its native cover identifies Manchester, New Hampshire and lists amendments through June 3, 2021. A file modification date or a current index link is not a certification that every later adopted law is incorporated.

## Install and run

Keep this folder together with its sibling `../scripts/` and `../preflight/` directories. No Codex tool, API key, browser, Node runtime or imported cookies are needed. Qualified runtime versions are in `RUNTIME.json`; this method uses the existing pinned official Python requirements. The host gate uses POSIX `fcntl`, so the demonstrated environment is macOS; intended portability is macOS/Linux with Python 3.12+.

```sh
python3 -m venv /your/runtime/manchester
/your/runtime/manchester/bin/python -m pip install -r /bundle/manchester/runtime/requirements.txt

# Download the exact two originals and inspect strict native page counts plus
# bounded identity text. This stage does not perform the full coordinate parse.
/your/runtime/manchester/bin/python -B /bundle/manchester/run.py capture --job /your/fresh-job

# Standard collector: fresh source inventory, source-bound opening cache import,
# every physical page, actual later full PDF and index checks, normal outputs.
/your/runtime/manchester/bin/python -B /bundle/manchester/run.py collect --job /your/fresh-job

# Separate read-only full retained-source verification, with networking denied.
/your/runtime/manchester/bin/python -B /bundle/manchester/run.py verify --job /your/fresh-job
```

The capture stage can be explicitly resumed by invoking it on the same job; only successful URL/hash-bound cached responses are reused. A failed cached response is never retried. A partial normal collection requires `collect --resume`. Source/config/runtime or native edition drift refuses completion; use a separately reviewed new run, not a waiver. The driver requires two distinct selected documents, so a missing link, a crosswired source, a duplicate alias pretending to be the second document or an unrelated host cannot pass. Ordinary direct `runtime/collect.py` is the established underlying engine; the qualified entry point here is `run.py`, which additionally enforces the exact pair and native edition pins.

All HTTPS requests use normal certificate and hostname verification. `TLS-TRUST.json` records the actual verified default trust setup. There is no TLS bypass or fallback transport. The shared host gate remains `/tmp/compliSolv-official-publication-gate` unless an operator explicitly configures the existing `OFFICIAL_GATE_DIR`. Persistent host stops and the retained publisher/official refusals are honored, without resets or automatic retries. Fresh HTTP403/429/challenge responses stop the workflow. Native GETs are serial with the existing nominal 3.5-second gate.

## Images and qualification

No separate image URL, bitmap, decoder, extraction, rendering or OCR operation is permitted. Source-native PDFs may contain images unchanged. The guard denies `Subtype Image` and dimension-only inline image stream decoding before `get_data`, and denies the known image/pixel APIs. Metadata and available native text/font streams remain readable. Actual source-control and synthetic decoder-tripwire tests are in `test_method.py`; the original decoder is stubbed in those tests, so they do not decode real image data.

Normalized output uses literal `[IMAGE]` at detected image locations and retains the available legal labels/captions. Intentional image omission is not a completeness defect. Full native file/page coverage, source-word conservation, independent-engine agreement, detected-cell comparisons and legal-semantic completeness are separate dimensions. Page records preserve source URLs, raw hashes, physical page IDs, word ownership, tables, links, annotations, geometry and explicit review conditions. They are not invented legal section records.

The actual first parse produced 135,664 source words and 226 image placeholders. All 336 pages conserved source words, normalized source-word characters and covered source glyphs. Independent text comparison still disagreed on 239 pages; 13 pages contained private codepoints; 1,225 of 8,573 detected cells disagreed on 18 pages. These are measured remaining text/table gaps, not waived by successful native capture. Final metrics and the later source/strict-verification results belong in the terminal summary, not this preliminary count alone. Legal hierarchy, arbitrary table detection, reading-order interpretation, external incorporated laws, uncodified amendments and jurisdiction completeness remain unqualified.

Run the finite method tests without any PDF parsing or publisher requests:

```sh
/your/runtime/manchester/bin/python -B /bundle/manchester/test_method.py
```

`audit_run.py` is an independent standard-library consumer for a terminal job. It imports no collector or PDF parser and verifies every source receipt, all ordered physical-page identities, all JSONL and CSV fields, the complete source-group inventory, actual closing native hashes, image markers and the retained qualification failures. The original large zoning bytes should be stored once in a release/deduplicated proof package; all cache and later-closing references must resolve through an explicit hash-bound alias map. Original execution outputs remain unchanged.
