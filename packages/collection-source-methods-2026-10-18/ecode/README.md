# Albany external statutory-citation classification — source remains incomplete

This isolated candidate resolves a classification gap for 21 historically unresolved source anchors across 18 URLs. It does not fetch external law, acquire Albany attachments, restore publisher access, supply source closing evidence, or make the selected publication complete. The original HTTP403 stop remains in force. No publisher requests or image acquisition/decoding/rendering/OCR occur. Retained publisher/native PDF files are not parsed; existing synthetic asset-fault controls are separate.

Each newly qualified citation must have an explicit source `statref` class, matching source owner, exact HTTPS `municipal.codes` forwarding route without query/fragment, a literal label matching the law section/article or U.S. Code title, and surrounding source text naming the corresponding external law. Download attributes or nonempty MIME declarations prevent this new classification. New York section/article tokens reject filename-shaped paths. Required-asset classification takes precedence in the actual collection ledger. Existing previously qualified namespace behavior is unchanged.

The newly observed New York routes identify Alcoholic Beverage Control (ABC), Correction (COR), Mental Hygiene (MHY), State Finance (STF), Public Lands (PBL), Not-for-Profit Corporation (NPC), Real Property (RPP), and Highway (HAY) laws. U.S. routes identify title-only USC citations to titles 8, 10, 26 and 29. Classification means the publisher-authored anchor is an external statutory reference within the existing selected-publication scope boundary. The referenced law is **not acquired, verified as current, or certified as an external adopted-law closure**. The original citation text and URLs remain present.

`corrected-statref-source-census.json` is the durable 21-occurrence fixture and primary source-review evidence. It includes original raw hashes, exact owner/class/label/context, raw anchor line/position and occurrence-specific context hashes. The earlier ledger and first review report reused the first context for STF163 occurrence2 and RPP/A6-A occurrences2/3. Those immutable reports remain historical; the corrected census explicitly records all three errata. The runtime extractor always walks individual anchors and never uses the review ledger as an acquisition or classification input.

V1–V4 are superseded. The peer found that extracting context text before image normalization could copy SVG image payload text into new metadata. Final V5 obtains context text through the existing strict `normalized_images` pipeline; graphic-descendant anchors refuse qualification. Original source/anchor hashes are retained. The context hash is explicitly named processed_owner_context_html_sha256: the existing own-body pipeline already absolutizes local note-fragment hrefs. Twenty actual contexts match raw hashes directly; HAY331 has exactly two such href transformations with a separate equivalence witness. Regressions cover multiline SVG payloads, image-only law context, malformed graphic ancestry, ordinary legal text, wrong owner/namespace/label/context, query/fragment/lookalike hosts, MIME/download attributes, and filename-shaped statutory URLs. They forbid network/process/base64/Pillow operations. Superseded revisions and findings must not be treated as final image-policy passes.

The final derivative uses all retained source, not a chapter/sample. Its intended scope is the same acquired Albany opening snapshot: 401 raw artifacts, 400 successful HTML responses, 3,253 inventory/dispositions and 3,006 canonical records. Every canonical body, table, note, source ID, source URL and image placeholder remains unchanged. Only the 21 source-link classifications and their newly attached provenance may change. New metadata is audited with the normalized-image auditor. The opening publisher identity is AL0934/code336787, currency label2026-07-06; absent closing evidence prevents any statement of current whole-publication consistency.

Four genuine required PDF documents remain unqualified:

| Source attachment | Source owner | Retained outcome |
| --- | --- | --- |
| AL0934-211a Appendix I.pdf | 7682547, Chapter211 Grading and Mining | HEAD403; zero document-body bytes |
| AL0934-211b Appendix II.pdf | same | Not requested after the stop |
| AL0934-211c Appendix III.pdf | same | Not requested after the stop |
| AL0934-375a Table of Zoning Map Amendments.pdf | 38067105, Chapter375 Unified Sustainable Development | Not requested after the stop |

`four-PDF-raw-source-owner-bindings.json` binds their original raw anchors without copying image icon markup into normalized metadata. A source PDF link/icon is not a downloaded PDF. The only previously retained unique Albany publisher PDF is a bounded §1-13 export, already audited in the earlier source-recovery package; it does not satisfy these four attachments. No required PDF body or new native parse is present here.

There are no retained root-end or contents-end artifacts after the final acquired body. Required documents, opening/closing consistency, edition and access gates remain false. A403 alone does not establish that credentials are required. Operational completion needs legitimate source access restoration and explicit operator review under the existing stop policy, plus genuine matching publisher documents and an actual closing sweep after acquisition. Supplying authentic local publisher exports through the existing operator import workflow can be reviewed offline; it cannot turn a bounded export into a whole-publication or currency proof. No automatic retry/reset is introduced.

Use ordinary Python3.12 with the selected collector requirements and `collectors/corpus_package/requirements-verification.txt`. The separate raw verifier helper preflights its dependencies. The shipped corpus writer/verifier is standard-library only; only macOS arm64 is tested and POSIX fcntl locking is used. No Codex service/browser is required for this offline handoff.

Exact final commands will use the self-contained final corpus input and a fresh disjoint proof/output directory. The selected verifier source must match the checkpoint fingerprint; a historical or current source is never silently substituted. Standard reconstruction can return `verified:true` while publication `complete:false`; corpus verification must retain expected exit2 and false downstream/selected-publication readiness.

Root owns promotion/Git. Only the two runtime modules in `promotion.json`, the durable25-case regression test, and its21-occurrence source fixture are proposed. Copied writer modules are exact proof snapshots, not instructions to overwrite later shared changes.


## Requested stopping point

Final V5 source and its25-case fixture/tests are frozen. The already-running exact standard source verifier (handle82673) finished with exit0, verified:true and complete:false. The final corpus export and relocated verification were **not started**, as requested; no final export or production promotion is claimed. STOPPING-POINT.json records terminal/pending status. No new validation, acquisition, production or Git work will start during this pause.


Completed final standard command (ordinary configured Python, no network):

```sh
"$ECODE_PY" -B verify_ecode_input.py --input albany-statutory-classification-v5 --collector-root albany-statutory-classification-v5/executed-source --publication-id albany-ecode-acquired-html --out actual-standard-proof-v5
```

That output is frozen; choose a fresh disjoint output to rerun after resumption. The equivalent standard publication-completeness exit remains2. Future corpus export and relocation checks are pending, not successful outcomes.
