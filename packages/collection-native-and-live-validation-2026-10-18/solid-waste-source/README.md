# Exact native six-page solid-waste logical extraction candidate

This isolated candidate reconstructs the whole retained Overland Park native document into usable logical JSONL and CSV. It changes no production collector, shared launcher, registry, or prior evidence. It makes no new network requests. The qualified source is exactly 38,014 bytes, SHA-256 `1af70bb8170cf2701cfb9e7ede2b274bf848309ca6fcaa3b7a7eeba9cd426c39`, registry publication `native-82-4b983dc51ab6`. The native document is printed **2011**. This packet does not establish current adoption, edition equivalence to other code sources, or jurisdiction completeness.

Use `canonical-final-v2/logical-units.jsonl` or `logical-units.csv` as the canonical legal-text export. Each row owns its own text once, with `parent_id`, a stable `logical_key`, printed label, and original source tag/content-reference/page/glyph/word provenance. Ancestor rows do not duplicate descendant text. The 88 rows include five sections 7.36-1 through 7.36-5, their paragraphs and nested lists, and front matter. Unprinted helper IDs describe ownership; they are not invented printed legal citations.

The final extraction is bound by `final-execution-v2.json`; `final-execution-v2.log` is its terminal stdout. It uses the exact `source/` hashes recorded in the receipt. `fault-tests-final.log` contains the 21-test terminal result. Earlier canonical directories, audit failures, tests, and source snapshots are retained as development history and are not the selected final output. The first independent audit failed due to its own first-section/front-matter dispatch; the first fault-suite failure was a no-op fixture mutation. Neither was a source-text omission. Later source-control metadata and audit source-path checks did not change the legal JSONL/CSV text.

## Original source authority and coverage

The PDF has a forward StructTreeRoot with 191 nodes and 109 unique MCID references. All 15,574 original glyphs, including whitespace, have exactly one owning legal unit or explicit source control. The source has 20 blank tagged paragraphs and six `/Artifact` footers; these are retained separately in `source-controls.jsonl` and CSV. The full original glyph and word ledgers remain in `source-glyphs.jsonl` and `source-words.jsonl`. Text, CID, font, source matrix/bbox, raw line text, source-order paths, and physical pages are preserved.

The extraction binds the original tags to a source-specific printed-label/font/indent hierarchy. It does not hardcode legal bodies. The independent auditor imports neither that profile nor the extractor/tag parser: it walks the original structure tree, reads original text operators through a separate PDFTextDevice, and derives the hierarchy from source labels and indentation. A MuPDF native text device independently confirms every glyph in original source sequence, including whitespace, on all six pages. It uses `FZ_DONT_DECODE_IMAGES` and no pixels. Internal font advance positions differ between readers by up to 0.09212 points; that diagnostic is retained. Every one of the 109 first content-reference anchors agrees within 0.001 points. No broad Unicode tolerance or all-glyph geometry-equality claim is applied.

The source-specific hierarchy preserves the 7.36-1.B.2 a–k sequence across pages 1–2; Residential and Commercial customer items under 7.36-3.B; and 7.36-5.D across pages 5–6 as one owner with two original MCID references. Original physical line breaks remain visible, including `rights-of-\nway.` in 7.36-5.G. The scripts perform no dehyphenation, legal correction, or invented body merging.

## Links, tables, images, and external dependencies

`source-dependency-inventory.json` scans every source page content stream and every indirect object. It proves zero annotations, URI actions, embedded files, XObjects, inline images, Table/Figure roles, and drawing/path operators for this exact six-page file. All content is independently reconciled to printed headings, paragraphs, and lists; table semantics are source-proven **not applicable**, rather than waived after a detector failure.

The preamble expressly incorporates **O.P.M.C. Chapter 7.36**. The body also references **County Solid Waste Regulations**. Their exact owning units/text/MCID/page witnesses are retained. Neither dependency is acquired or resolved in this packet, and no URL or edition match is guessed. The six-page document's text/structure can be qualified separately from those external dependencies. `required_external_legal_dependencies_complete`, `edition_currentness_qualified`, and `jurisdiction_complete` remain false. No common launcher acceptance or publication-complete flag is changed by this candidate.

All code preserves the user's exact `[IMAGE]` policy. It never separately acquires, extracts, decodes, renders, or OCRs images. This particular source contains zero image objects; a different hash is rejected before interpretation. Tests and final execution block sockets, PIL image opening, PyMuPDF image extraction/pixmaps, and pypdf image-stream decoding. No blocked API was called. Original PDF bytes are retained unchanged.

## Portable commands

Use Python 3.12 with `requirements.txt`, or the existing shared interpreter. Tested runtime: Python 3.12.14, macOS 26.6.2 arm64, pypdf 6.21.1, pdfminer.six 20251107, PyMuPDF 1.26.5, Pillow 11.3.0. No browser, external commands, or absolute cross-package imports are required.

From this packet directory, choose a fresh output directory and receipt. Existing outputs are refused:

```sh
python source/run_final.py --pdf source.pdf --out /tmp/overland-solid-waste-FRESH --receipt /tmp/overland-solid-waste-FRESH-receipt.json
python source/independent_audit.py --pdf source.pdf --out /tmp/overland-solid-waste-FRESH
python source/test_logical.py
```

The first command executes extraction plus independent audit with image/network tripwires. For a separately managed interpreter, point `python` to that interpreter without altering an active collection runtime. `test_logical.py` locates this packet's retained `source.pdf` relative to its own file. The tests deliberately corrupt actual exported units, hierarchy, cross-page references, glyph/CID/position evidence, word ownership, footer controls, line breaks, CSV, source hash, and dependency resolution. All negative cases must fail verification.

The profile is intentionally limited to the exact source hash. Another edition or document requires its own source inventory and independent qualification. This packet is an offline retained-source study, not fresh acquisition or proof that all separately published regulations have been collected.
