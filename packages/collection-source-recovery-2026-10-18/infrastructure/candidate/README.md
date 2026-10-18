# Exhaustive Infrastructure printed-flow candidate

This isolated candidate projects all 62 physical pages of the retained Manual of Infrastructure Standards into the existing 172 source-printed units. It changes the canonical `ordered_blocks` and primary HTML, with matching JSONL/CSV. It preserves every source fragment, word ID, exact primary text, existing table/cell object, source heading, native metadata, prior diagnostics and `[IMAGE]` placeholder. Production and the original evidence remain unchanged.

The exact native source is `raw/source.pdf`, SHA-256 `915fe1fdf8ff5da33acfce7d08637808cb57886fbbc7f157b2b81bfcf970827c`. Its observed source is the `doclibrary.aspx` URL pinned in `runtime/collectors/encodeplus/configs/native-82-0c6b3dc40877.json`. The immediately preceding 172-unit output is preserved byte-for-byte, compressed with deterministic gzip, in `evidence/baseline-records.jsonl.gz` (decompressed SHA `8bf0cf6e1d319d900fbdafff16dd8f051e945f39a6102aaad035fe3a4001afe9`). This includes the earlier independently qualified page-26 nested-list witness. The complete cached 62-page IR and native inventory are in the existing `source-ir-and-native-inventory.json.gz` fixture.

The exhaustive denominators are 172 units, 1,776 source fragments, 18,662 unique word IDs, 171 source heading nodes (176 physical heading fragments), 175 contents lines, 142 running controls, 1,271 body fragments, five actual grids with 79 cells, five `[IMAGE]` placeholders, and two cover lines. The new primary structure contains 19 literal-marker list groups / 85 items and 385 printed paragraph groups. Eight apparent parenthesized labels are source-backed wrapped prose (four measurements, a telephone number, two explicit acronyms, and one multiword parenthetical); their exact source text and geometry remain in the disposition ledger. They are not silently turned into list items.

Grouping uses literal marker sequence, indentation and measured line geometry. It does not infer legal hierarchy from source heading IDs or legal meaning. The original PDF has a flat bookmark sequence and no semantic structure tree. Printed paragraph groups describe geometry, not established legal paragraph intent. Thirty-eight cross-page paragraph relationships remain explicitly unresolved. The retained external legal-dependency requirements, source/edition limits, three literal TOC-spacing discrepancies, and printed table note/marker caveat remain unchanged. Whole native reading-order, whole nested-list, paragraph-continuation, required-dependency, edition and whole-publication completeness remain false. `source_literal_block_list_topology_qualified` is restricted to this exact source's observed marker topology, not whole legal semantics.

Nine cached multiline prose fragments needed additional line geometry. Only physical pages 11–14 were parsed for text/word positions: 68 independent PDFium line queries agree with the original cached word and character sequences. No other native pages were reparsed for this candidate. The executed query script and original query receipt are retained under `evidence/`; its historical source paths are provenance, not portable replay dependencies. The result is the hash-bound operational `infrastructure-multiline-native-geometry.json` capsule. The pure collector does not import a PDF/native/image/network library to apply that capsule. Missing, changed or wrong-source capsule data fails closed. These four query pages have no source image placeholders; the five existing image positions on pages 1, 18, 51 and 53 are carried unchanged. There is no image extraction, pixel access, rendering or OCR.

`superseded_printed_flow_diagnostics.original_fields` retains the prior canonical fields. Canonical HTML table cells use the exact previously qualified bounded cell text/spans. Original primary text retains its exact whole-word serialization. The recorded cell/newline/superscript whitespace difference is explicit; a character or ownership difference refuses. No problematic cell is dropped or repaired by guessing.

## Portable commands

From any directory, ordinary Python 3.9+ with its standard library can run:

```sh
python3 -B -S /absolute/path/FROZEN-PACKET/verify_packet.py
python3 -B -S /absolute/path/FROZEN-PACKET/test_source_comparison.py -v
```

The first command checks the complete packet manifest, reconstructs all 172 records through the copied collector's `project_records`, `validate_records` and `outputs`, compares every primary/sidecar byte to `actual/`, and independently consumes all source leaves/cells/HTML/CSV. It writes nothing and does not parse the PDF. Successful verification means the scoped cached-source projection is reproducible; it does not grant whole-publication acceptance.

The eleven portable operational fault tests run from the shipped runtime directory:

```sh
cd /absolute/path/FROZEN-PACKET/runtime
python3 -B -S -m unittest collectors.encodeplus.test_infrastructure_printed_flow -v
```

They exercise all-source counts, deterministic canonical reconstruction, fragment/word/image ownership, invented text, active image markup, false qualification, diagnostic corruption, wrong-source pages, missing/corrupt geometry and changed geometry text/word ownership. The separate nine-test source comparison suite exercises source-byte mismatch, missing/duplicate/reordered fragments, lost grid characters, observed sequence-gap refusal, non-list dispositions and unchanged completeness limits. Existing Infrastructure logical, nested-list and source-route regressions were also run: 37 tests passed (including the eleven new tests), using the pinned shared Python 3.12 runtime and existing source fixtures. The selected packet includes the eleven-test fixtures; the 37-test log is evidence, not a claim that every unrelated fixture was copied here.

## Integration boundary

`WHITELIST.json` contains exactly six proposed files and before/after hashes. `infrastructure_logical.project_records` first validates the previous source profile, applies this entire-source printed flow, then deterministically verifies it. `validate_records` restores the exact old fields and checks the existing source/native/list bindings before rebuilding and comparing the entire new projection. The normal `build_records` and native output route therefore use the new canonical flow. Only the cached current collector route was executed here; a fresh native acquisition/default 62-page parse has not been rerun for this revision.

The `collect.py` change adds the JSON geometry capsule to the existing `code_hashes` inventory, so normal checkpoint/script-version capture and explicit upgrade validation bind this required data too. Old finished packages do not silently adopt the new profile. All other source modules are contextual snapshots, never a promotion whitelist. In particular, the independent sibling MIME correction in `transport.py` is owned separately; this packet does not propose replacing that file.

The broader audit trail under the parent workspace preserves superseded projections and QA preparation failures. Only the exact terminal reports and sources selected by this packet's manifest support this candidate. No older evidence, sealed output, production source, Git state or database was modified.
