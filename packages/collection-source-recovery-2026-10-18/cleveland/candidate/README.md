# Exact Cleveland printable-attachment corpus candidate

This is an isolated candidate, with no production/Git/publisher/gate changes. It closes the previously unresolved canonical projection of one retained Cleveland required PDF by representing the **complete source-explicit printable attachment** as one linked document unit. It does not derive legal sections from physical PDF pages.

The exact original PDF is `eb1ea94cca6abefd0a8a6645c59cc2cfac5ce704adc4b76240b1ee0f3e858c7a`, 156,425 bytes, linked by publisher document `0-0-0-45110`, **§ 348.02 Frontage Features**, as “Click here to view a printable PDF version”. Source URL ends `/DATAOBJECTS/0-0-0-13294.pdf`. Its printed title is **Required Frontage Features**. The actual original native artifact is one closed 9×2 grid with a title and literal a.–h. row labels, followed by one ordinance note. Those labels remain table entries, with no invented subsection/section IDs. The attachment has no printed section number; its corpus `section_number` is blank and its `citation` is the exact referring provision caption, explicitly documented in provenance.

The source-level basis is stronger than a physical page count: the original file is an explicitly linked complete printable document; the complete source glyphs, grid, image-cell ownership and trailing note reconcile. Its catalog has no structure tree, outline, page labels, annotations, embedded files or further document references; its only named destination is `_PAGE1`. `source-inspection.json` records the exact catalog/font metadata under no-image guards. The source-wide prior qualification proves the complete original grid and native glyph order. This candidate recomputes every nonwhitespace glyph's unique cell/note ownership using original coordinates and source indices, compares literal cell text in that exact order, and validates every image placement against its original cell.

The document unit contains all 2,589 native glyphs' available text, exactly 2,201 nonwhitespace glyphs once, all 18 unmerged cells and closed-border evidence, all nine `[IMAGE]` markers in their proper right-hand cells, and the exact final ordinance note. Native font/line/block/source-order metadata remains in provenance and the immutable original page IR. Source spelling and incomplete phrases such as `bach`, `tine`, and the literal cell endings are preserved without correction, inferred continuation, or OCR. This is fidelity to the available original document, not an assertion that source drafting is error-free.

The original HTML provision and printable link remain byte-identical. One separate canonical attachment record follows that exact provision; its ID is explicitly attachment-derived (`american-legal-attachment:<source SHA>`), and its inventory node is the existing required asset, now with an `included` disposition. All original 6,140 rows and their 16 fields are unchanged, as is rich provenance except for subsequent row ordinals. The new result is **6,141 rows, 6,160 inventory/disposition nodes, 0 unresolved dispositions**, and 24 canonical `[IMAGE]` positions (15 original HTML plus nine attachment placements). Four other required zero-native-glyph PDFs keep their fully bound image-policy N/A dispositions. Fifteen image reference nodes remain policy exclusions without image files.

The 988 original input files, both actual standard-verification proofs, and original coverage bytes remain unchanged. The original `pdf_legal_provision_segmentation_qualified:false` is retained: this is a newly measured complete printable **document-unit** projection, not a rewrite of the old producer's inferred-section flag. No other producer, edition, adopted-law, jurisdiction or independent legal-review gate is flipped. The shared selected-readiness contract has not been extended to AL here. **Expected package verification exit remains 2**, with `package_verified:true`, `selected_publication_ready:false`, `complete:false`.

## Qualification and evidence

`american_legal_attachment.py` is stdlib-only, as are the shared writer and shipped package verifier. The profile is pinned to this exact raw file SHA, URL, Cleveland publication identity, source-proven § 348.02 owner and printable reference. It requires a qualified retained PDF, exact full native page count/IDs/SHA-derived owner, actual binary response receipt, positive standard-family text/table qualifications, original whole-source grid/reading-order qualification, original closed cell/spans, complete glyph conservation/order, exact ordinance note and exact image-cell placements. A changed file at this URI requires requalification. Other inputs are not generalized into PDF section mappings.

`tests.json` records **56 tests** on CPython 3.12.14/macOS arm64 with `-S`: 24 real attachment-fixture cases and the prior 32 AL reader controls. Actual original PDF bytes and compact source-IR fixture (about 501 KB) are bundled. Controls include wrong file/publication/owner/reference, missing native receipt/page/cell/note/image, glyph/text/geometry/span/order corruption, false source qualification and no network/decoder operation. No third-party PDF or image code is imported by the operational profile.

`actual-consumer.json` independently checks all original 6,140×16 fields and rich source provenance unchanged, the new attachment's 18 literal table-cell values/spans, one literal source note, all 2,201 native nonwhitespace glyph indices exactly once, nine markers, original raw bytes/receipts, every JSON/CSV/TOC field and BOM, and unchanged original flags. `actual-corruption-tests.json` proves that removing the entire attachment and consistently rehashing generated output/state/manifest still fails source reconstruction; corruption of the original required PDF also refuses. Original files remain unchanged.

`relocation.json` records the complete 1,019-artifact package copied outside the project and verified by its own shipped entrypoint using ordinary Python `-S` (no `-B` needed). The command has no third-party imports, network/image/process operations, writes or outside-input reads. All source/destination hashes remain equal before/after. The original current AL standard source verification was already performed in the preceding frozen reader revision and is reused byte-identically; neither source normalization nor full native parsing was repeated here. The only new PDF inspection was catalog/page/font metadata, with no content/image/pixel extraction.

## Reproduce

From this packet directory, the already shipped package needs only ordinary Python 3.12 on the tested POSIX platform:

```sh
python3 -S package/packager-source/package.py verify --out package
python3 -S -m unittest discover -s candidate -p 'test_american_legal*.py' -v
```

The first command must return exit 2 with successful package verification. For a fresh derivative package using the unchanged retained evidence and actual source proof:

```sh
python3 -S candidate/package.py package --input package/evidence/input --proof portable-verification/read-only-proof.json --reader american-legal-native-html-publication-v1 --out fresh-package
```

`audit_actual.py`, `test_actual_corruption.py` and `test_relocation.py` recompute and write their respective receipts; preserve frozen receipts before rerunning them. The all-original-row comparison uses the preceding frozen v2 package at its authoritative project-relative location. The **shipped package verifier itself** needs no prior package, original project or collector dependencies and is read-only.

For another actual standard source verification, use the explicitly selected collector environment and `candidate/verify_input.py --reader american-legal-native-html-publication-v1 --input package/evidence/input --collector-root verification-source --publication-id 59-primary --out fresh-verification`. This helper requires the common collector environment; the corpus reader/writer/portable verifier do not.

## Integration boundary

Root owns promotion. New files are `candidate/american_legal_attachment.py`, `candidate/test_american_legal_attachment.py`, and `candidate/fixtures/cleveland-frontage-printable-source/`. Only a new import/call in `american_legal_html.py` and one `MODULES` entry in `package.py` are needed. `integration.patch` records those deltas against the captured production baseline. Preserve root's current common, readiness, other readers, helper, source bindings and documentation; do not wholesale replace the copied runtime snapshot. The original AL serial queue's external Legislature HTTP403 operator stop remains in force. This work uses no publisher traffic and supplies no access reset.
