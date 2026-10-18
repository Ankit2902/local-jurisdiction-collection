# Independent enCodePlus native-parser promotion review

This review recommends the frozen v3 parser improvements plus the bounded inline-image metadata correction and diagnostic aggregate guard, subject to root promotion. Production and prior evidence remain untouched. It does not qualify required-PDF legal semantics or repair the795 cell disagreements.

The source lineage is production EP parser5d0141e7… → frozen Overland v3c8e0c02a… → isolated final2bdd4253…. Production→v3 changes only `pages()`: table blocks serialize each uniquely owned whole source word once, source glyph/word conservation and CID-literal diagnostics become explicit, and every detected cell retains the exact extraction rectangle as `extraction_bbox`. Rounded display bounds, original detector cell text, span geometry and independent disagreements remain retained. Table detection and all image-redaction helpers are unchanged.

The final parser adds the exact official6ed60608… `image_source_name()` helper and one call. PDFMiner's process-allocated inline name is not a source ID; stream.objidNone yields source_namenull while existing page-local image ID, original-source hash and geometry remain preserved. Named indirect resources retain their name even when the name happens to be numeric. No image stream is read or decoded to derive identity.

An integration guard in `native_document.page_records()` now requires source-glyph conservation explicitlytrue and CID diagnostics explicitlyempty before reporting extractable-text reconciliation. Per-record failures cannot hide behind the older aggregate fields. This guard changes no normalized body record and does not enable legal/table-semantic acceptance.

Independent evidence:

- Both frozen v2/v3 manifests verified. All636 retained page records are identical after removing only extraction_bbox. Unique ownership covers142,533 source words; 6,248 cells retain795disagreements. All201 image placeholders retain IDs, geometry and ownership. All102 legacy CID/engine-failure pages remain explicit.
- Five direct PDFium queries on just two actual UPOC physical169pages reproduce exact original strings at fullprecision bounds, including four prior character-truncation cases. No full 636 native reparse was repeated.
- Four independent bounded processes parse only actual Arlington Charter physical52/57/63 under explicit logical→physical mapping. Baseline differs at seven source_name fields; final records are byte-identical across processes. Only seven names become null; all other fields and ten literal [IMAGE] markers remain identical. All forbidden image stream/API/render/object/PIL/network/child-process calls stayzero. The included native original is immutable source, not a separate image asset.
- States' source-bound201 image exposure report independently confirms objidNone0 in the five Overland documents. This review additionally binds all201occurrences to actual named indirect resource references using metadata-only PDF xref inspection. Therefore the helper has zero affected image names in those five sources.
- All five existing v3 document aggregate outcomes are identical before/after the stronger diagnostic guard: current four reconcile extractable text; legacy2024 UPOC remainsfalse. This does not bridge the legacy 40th/current 42nd source-edition conflict.

Exact test phases and final 56-suite status are recorded in `validation-summary.json` and test logs. The53-test whole family sweep predates the aggregate guard; the final targeted7-test sweep and final full56-test sweep exercise the final four runtime/test files. Unit tests use mocked transport and retained small native fixtures; they are not live publisher acquisitions or a repeated636-page parse. The exact supported fresh shared runtime is Python3.12.14 with the independently qualified package profile.

The image rule remains literal `[IMAGE]`, no separate image acquisition/extraction/decoding/rendering/OCR. Image omission itself is intentional and does not explain away text, cell, source or edition gaps. Remaining795 cell mismatches,102 legacy CID/engine pages, arbitrary table detection, reading order, section semantics and official edition alignment remain unqualified.

Two harness issues are retained candidly under attempts/: an import-context error before parser execution, and a wrong-working-directory test-preparation error. The latter rawlog was inadvertently replaced; only the exact tool-observed error receipt is retained and labeled. Neither is a runtime-parser defect or a passing test. Corrected final invocations and outputs are separate.

The promotion whitelist is only the four files in FINAL-PROMOTION-PLAN.json. Do not copy the whole candidate directory or its historical metadata over production. Root must assert each existing production baseline SHA; new tests must not overwrite unrelated files. No deletions are proposed. Root owns Git and production integration.

Portable artifact integrity check:

```sh
python3 -B /path/to/ep-native-parser-review-v1/verify_review.py
```

Final family regression command from the candidate/ or promoted repository root:

```sh
python -B -m unittest collectors.encodeplus.tests collectors.encodeplus.test_image_context_scheme collectors.encodeplus.test_bounded_decoder collectors.encodeplus.test_savannah_reference collectors.encodeplus.test_savannah_empty collectors.encodeplus.test_inline_image_identity collectors.encodeplus.test_native_diagnostic_aggregate -v
```

Scripts for differential/native probes preserve development paths to immutable source evidence. Do not repeat the full source parses merely to relocate compact proof. Copied source fixtures/reports and their hashes are included; original v2/v3 large evidence paths and hashes are recorded explicitly rather than relabelled as newly generated output.

Final exact-source result: all **56 tests passed in 96.340 seconds**, exit0, using the unchanged final four files. FINAL-PROMOTION-PLAN.json and validation-summary.json bind the exact test log and runtime receipt.
