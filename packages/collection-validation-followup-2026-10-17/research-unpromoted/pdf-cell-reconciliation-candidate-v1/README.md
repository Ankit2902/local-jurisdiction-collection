# Isolated native-PDF reconciliation candidate

This directory preserves the original 46 mismatches, exact source hashes, full retained-native replays, and a narrowly qualified bounded-decoder repair. It changes no production collector, acquisition stop, original ledger, or source PDF. No network, rendering, image extraction, bitmap, or OCR operation was performed. Original PDFs may contain embedded graphics; normalization uses literal `[IMAGE]` placeholders and native metadata only.

## Concrete table result

`full-native-replay-summary.json` binds all 46 historical cases and the exact implementation. Fire's 46 pages now qualify 799/799 table cells (previously 798); Cleveland's one page qualifies 18/18 (previously 17), retaining all nine image-cell placeholders and adjacent captions. Both repaired cells are source-proven PDFium bounded U+0002 aliases of native hyphens: the same native glyph is explicitly flagged `IsHyphen`, is not generated, has a matching full-range decoder recovery, and matches a unique independent pdfminer hyphen at the same physical position. Original detector text, bounded text, source word ownership, geometry and row/cell identities remain retained.

Infrastructure's full 62-page replay still qualifies 572/616 cells. Its 44 historical disagreements remain explicit. Inferred column edges cut actual words/citation numbers (including GENERAL, RELOCATION, 4.1.3, and March). Matching two clipped fragments cannot prove a source-supported table cell. No table-detection modification or blanket waiver was made. Across these 109 pages, source glyph-to-word, normalized-word and page-level independent character checks pass. This does not establish whole-publication legal semantics or edition parity.

`bounded_decoder.py` is the intended narrow reusable change; `pdf_structure.py` is a historical 9eb baseline copy plus that helper integration, not a replacement for later frozen official/EP safety changes. Future promotion must rebase only the helper/import/cell-loop change onto the current owner version and rerun owner tests. No Title33 full replay was performed here.

## Spokane required attachments

`spokane-native-attachments/native-label-derivative-v3/summary.json` binds all four retained PDFs, five source-owned references, and 101 physical pages. Native stream order, full labels, per-glyph source IDs/geometry, original generic word geometry, source hashes and owner identities are preserved. No geographic map reading order is inferred.

- Appendix-A parcel map: 270 native label runs / 2,090 nonspace glyphs, full parcel IDs such as `35202.2115`, independently qualified text.
- MTFE/city-zoning map: 454 native label runs / 5,529 nonspace glyphs, complete exact native-stream projection including Havana St and Broadway Ave. Independent engine character multiplicity remains unqualified on overprinted text. Native geometry dedup gives 2,560 groups versus 2,682 independent dedup word characters; the original mismatch and failed strict v2 projection are preserved. A separate geometric-support diagnostic matches all 1,725 independent source-word character capacities to native glyphs within their source bounds and supports every native glyph with an independent same-character word at that location. It is explicitly support, not a one-to-one multiplicity/reading-order proof. This is not a source-no-text exemption and not a claimed engine-equivalence pass.
- Community Empowerment Zone appendix: 98 pages, both native engines report zero glyphs on every page. `[IMAGE]` and source-proven native-text N/A apply.
- Community Empowerment Zone boundary map: one page, both engines report zero glyphs. `[IMAGE]` and source-proven native-text N/A apply.

Visual map interpretation is deliberately excluded by the user image policy; it is not an outstanding obligation to transcribe images. A whole-vector-map placeholder additionally requires a source reference/filename explicitly identifying a map plus complex native drawing curves; ordinary table borders do not qualify. No separately downloaded/extracted image bytes are present. Page-level image object placement is metadata only. The native PDF acquisition ledger is unchanged, and this derivative is not a blanket publication-completeness upgrade.

## Offline checks

Tested Python 3.12.14 runtime: project `github/local-jurisdiction-collection/.collection-runtime/venv/bin/python`; dependencies include pypdf 6.21.1, pypdfium2 5.14.0, pdfplumber/pdfminer as captured in `runtime.json`.

From this directory:

```sh
python -B verify_isolated.py
python -B -m unittest -v test_bounded_decoder
```

The second command runs the compact exact Cleveland native fixture plus negative native-flag/index/geometry tests (5 passing tests). The Spokane six-test suite uses the original retained PDF paths, so it requires the original project evidence layout; it is intentionally not advertised as a standalone relocated fixture. Run it from `spokane-native-attachments` with `python -B -m unittest -v test_native_labels`. It opens only PDFium text pages for the two text-bearing maps and has tripwires on pixel/network APIs. Full replay outputs are retained rather than recomputed by the default readonly verifier. The verifier reads all files without modifying them.
