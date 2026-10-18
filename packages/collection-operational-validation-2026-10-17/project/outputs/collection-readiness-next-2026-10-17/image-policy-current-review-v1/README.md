# Bounded current-code image-policy review

This review inspects the published IMAGE-POLICY, current runtime deltas, selected prior exact-scope evidence, shared launcher/delegation, normalized/binary auditors, and source DOM audit entrypoints. It modifies no collector, QA, registry, stop, source or historical package. No publisher requests, heavy PDF replays, image rendering/decoding/extraction or OCR were performed.

The existing lightweight regression run covers all six publisher families plus original-source HTML/Word adapters: four-family identity/image-only/CSS/SVG/table behavior; recursive six-family image metadata; official and American Legal collection paths with separate-image request tripwires; original-source MIME-before-read and Word media-member tripwires; eCode multiline attributes; Municode legal Notes; American Legal native PDF metadata; Gridics image MIME/signature and observed CSS guards; and normalized-output/binary auditors. Network connections were disabled in child Python processes. **72 existing checks in12groups passed** after invoking four local-import/main-style test scripts correctly. Initial invocation errors and corrected commands/logs are preserved; they were test-entrypoint mistakes, not silently discarded code failures.199 selected source/policy/test files were hash-stable during that run.

Three concrete QA issues were reported to the parent and QA owner:

1. Municode raw-table audit attached raw Docs.Content before removing image/SVG/CSS/data-URI elements.
2. enCodePlus raw-table audit had the same attachment order.
3. New official attachment-pages.jsonl and native-attachments qualification JSON were outside the normalized-image auditor's recognized outputs.

The owner has now patched the two raw-table paths to use shared inert-template preparation **before** live attachment. My narrow source rescan confirms there is no raw setContent path, Python body slicing fails closed, the exact reviewed inert JS is used, and network blocking/CSP remain. Source hashes are in qa-inert-fix-source-rescan.json. The owner is responsible for the bounded actual-source execution receipt. Earlier table audits retain a historical inline-image rendering limitation; an old table match is not retroactively an image-policy pass.

The auditor scope patch now recognizes attachment-pages.jsonl and recursively examines native-attachments/*.json. I independently reran its updated existing six-test suite successfully. That six-test receipt is separate from the initial72-check source revision.

No additional concrete collector regression was found in the reviewed paths. This is **not** an unconditional all-QA or full-publication fidelity certification. Source-only review, mocked/fixture execution, prior actual evidence, and owner execution receipts have separate scopes. Original native PDFs/HTML/archives may embed images; those originals are not separately extracted image assets. Image policy deliberately excludes graphic interpretation; source-proven no-glyph PDF pages may be N/A with [IMAGE], while lost available glyphs remain failures. Legitimate browser security/challenge controls remain untouched and all persistent access stops remain active.

The review JSON records the exact initial source hashes, corrected regression status, findings, prior evidence hashes, and limitations. Nothing here promotes the Infrastructure guard or changes current PDF/helper source while official replays are active.
