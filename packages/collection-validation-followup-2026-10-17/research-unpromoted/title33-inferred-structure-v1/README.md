# Title 33: narrow inferred-structure investigation

This is an **unpromoted isolated candidate**, not a full Title 33 replay or a new
publication-completeness proof. The original official 1,855-page PDF and all prior
outputs remain unchanged. Current official production `pdf_structure.py` remains
SHA-256 `2fcd3238e28461c51489cf8b03ec8decf010a2409b69c107d49db39b52f76802`.

The prior terminal f0d7a63e replay detected 10,394 cells, with 9,702 agreeing under
its independent cell comparison. Of the 692 disagreements, 683 belonged to
`aligned_text_numeric_schedule` candidates and nine to ruled tables. Those are
counts from the original terminal output, not a new full-book execution.

Seven original physical pages were inspected: 4, 10, 14, 35, 155, 634 and 1288.
`current_selected.py` is an exact copy of the current production parser with only
an optional page-selection filter, preserving original physical page numbers,
original PDF hash and original 1,855-page count. It confirms that the current
whole-owned-word serializer already fixes the canonical page-text character loss
seen in the older replay on pages 35 and 155. That repair is not attributed to
this candidate.

`candidate_selected.py` adds a conservative inferred-cell guard. If no actual
candidate cell contains a whole source word, the inferred table is rejected as a
canonical page-text owner. Every source word remains in ordinary canonical text.
The detector's original cell IDs, boxes, spans, strings and independent text
comparisons remain retained as unqualified structure. Rejected candidates do not
vanish from the cell/disagreement denominators. Cells are not widened or cropped
into a pass. Merged cells that really contain a whole word remain eligible.

The selected actual results are:

| Physical page | Unsafe source words | Candidate cells retained | Disagreements retained |
|---|---:|---:|---:|
| 10 | 40 | 345 | 33 |
| 35 | 32 | 260 | 28 |
| 155 | 19 | 123 | 13 |
| 14, ruled control | 0 | 154 | 0 |

These three inferred candidates split ordinary chapter/index words across
artificial columns. All 728 rejected-candidate cells and 74 disagreements remain
available. Canonical word/glyph ownership remains complete. This does not qualify
all legal table structure, inferred index relationships or reading order. In
particular, a page gutter heuristic may still separate right-hand index folios;
this investigation does not claim to resolve that ordering question.

The other sampled conditions stay explicit:

- Page 4 has three whitespace glyphs, no non-whitespace source glyphs, no image
  objects and no vector objects. The current parser correctly treats its text
  comparison as not applicable and does not fabricate an `[IMAGE]` marker.
- Page 634 contains two native images plus available source glyph text and an
  existing `HiddenHorzOCR` font. Reading that existing text is not a new OCR
  operation. The original source contains 39 hyphens and ten bullet glyphs;
  PDFium exposes 37 and nine. No raw U+0002/IsHyphen case was found. The strict
  engine-disagreement flag remains; overlapping source glyphs are not broadly
  deduplicated into a pass.
- Page 1288 has seven source-defined private-use glyphs that agree in both text
  engines. Font object 8937 explicitly maps source CID `0x0078` to U+F0B7, with an
  identity CID/GID map and embedded glyph 120. The subset font has no `cmap` or
  `post` table supplying a semantic glyph name. The exact private-use character
  is retained; no invented replacement with U+2022 is applied. The current
  review flag remains.

The ruled-table U+0002 line-end-hyphen cases are a separate core-agent study. This
candidate does not integrate or re-test that helper and claims no fix for those
nine Title 33 cells.

From this directory, with the shared Python 3.12 runtime and installed official
collector requirements, narrow replay commands are:

```sh
python run_selected.py WORKSPACE_ROOT current_selected.py fresh-current.jsonl
python run_selected.py WORKSPACE_ROOT candidate_selected.py fresh-candidate.jsonl
python test_guard.py
```

The first two commands require fresh output filenames. `test_guard.py` verifies
the retained paired receipts, exact original cell diagnostics, real boundary
fixtures, whole-word ownership and positive/negative synthetic geometry cases.
Its 20 checks are not a full-publication test suite. `guard-only.patch` contains
only the proposed guard delta, excluding the diagnostic page-selection filter.

No image pixels are decoded, extracted, rendered or transcribed. Native source
image metadata and literal `[IMAGE]` placeholders remain under the existing
policy. Socket connections, image stream decoding and raster rendering are
blocked during both selected-page executions. There is no new publisher traffic.
