# American Legal full-publication collector

This standalone collector supports dynamic American Legal publication selection, recursive publisher TOC inventory, pinned-edition full traversal, and genuine whole-publication native HTML export. It contains no built-in target IDs or absolute dependency paths. The registry supplies the jurisdiction, state, current source route and publication selector. All fifteen American Legal primaries in the 100-target registry are mapped; live completeness validation is limited to the publications named in `validation-summary.json`.

**Image policy:** all images become literal `[IMAGE]`. Images are never explicitly downloaded. Normalized HTML removes raster/picture/SVG/image objects, image links/posters and active CSS image URLs while retaining source IDs, headings and image-reference metadata. Browser image resources are blocked where practical; publisher security controls are left enabled. Inline image data is represented by a hash and placeholder in normalized metadata. Original publisher HTML/PDF files may contain images and remain source evidence; image binaries are not separately extracted. Intentional image omission is not a completeness gap. Nonimage PDF/document attachments remain separate required assets.

## Install

Use Python 3.12+ on macOS/Linux (the shared gate uses `fcntl`), Node20+ and ordinary installed Google Chrome. Windows locking is untested. Current PDF source proofs use Python3.12.14, pdfminer.six20251107, pypdf6.21.1 and PyMuPDF1.26.5. Earlier acquisition evidence records Python3.9.6 separately. Browser proof uses Node24.19.0, Playwright1.62.1, Chrome155.0.8059.84 on macOS26.6.2/arm64. No Codex runtime/API, imported browser profile, masking or challenge interaction is used. PyMuPDF1.26.5 now supplies PDF text geometry and native ruled-table candidates alongside the independent pypdf text engine.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r collectors/american-legal/requirements-lock.txt
npm install --prefix collectors/american-legal
```

`NODE_BIN` optionally selects Node. `BROWSER_CHANNEL` defaults to `chrome`. `PLAYWRIGHT_MODULE_ROOT` optionally identifies a package.json whose normal dependencies include Playwright. The browser bridge receives the current Python interpreter automatically for the gate. These variables permit normal installations; bundled workstation runtime paths are only in execution receipts.

## Fresh, resume and verify

A fresh output directory must not exist. An overview containing multiple independent publications requires an observed slug/title/UUID selector; a publication URL can supply its slug. `--jurisdiction` is checked against the publisher client name after punctuation/case normalization, without dropping county/city distinctions. Use explicit `--identity-alias` only for an observed abbreviated publisher identity. The registry records Louisville's `Louisville-Jefferson County` and Honolulu's `Honolulu` aliases.

```sh
.venv/bin/python collectors/american-legal/collect.py \
  --url https://codelibrary.amlegal.com/codes/san_diego/latest/overview \
  --jurisdiction 'San Diego County' --state CA --publication sandiego_ords \
  --strategy native --assets reference-only --out /NEW/PATH/index-run

.venv/bin/python collectors/american-legal/collect.py \
  --url https://codelibrary.amlegal.com/codes/san_diego/latest/overview \
  --jurisdiction 'San Diego County' --state CA --publication sandiego_ords \
  --strategy native --assets reference-only --out /NEW/PATH/index-run --resume

.venv/bin/python collectors/american-legal/verify.py /NEW/PATH/index-run --offline
```

Default strategy is `traverse`: dynamically inventory the full publication, fetch every independently inventoried renderer-owned doc/index range, and retain full legal HTML/text, parent/path, body-block IDs, tables/spans/relationships, links and notes. Strategy `native` inventories the same complete independent TOC, selects the whole code's visible Download checkbox, chooses Save HTML, asserts the actual posted whole-code scope/version, follows the new job's OPEN link and partitions every native rich block into exactly one independent TOC owner. Extra headings, absent middle nodes, duplicate IDs, leaked descendant bodies and unowned native text fail closed. There is no first-N default.

`--max-items N` is an explicit bounded diagnostic limit on inventory/traversal and always forces incomplete status. `--assets download` is the default for nonimage required assets. `--assets reference-only` deliberately retains references without downloading those documents, forces attachment incompleteness where such references exist, and is useful for large ordinance indexes. It does not suppress the original native PDF for an independently PDF-published unit. Source-explicit incorporated/adopted nonimage standards are required even with extensionless URLs. Unknown types remain unresolved. Nonimage downloads are screened by HEAD; image MIME responses become placeholders without a GET. CSS image dependencies become placeholders; known fonts/styles remain separately qualified.

Exit codes are **0** for sound complete publication text plus required nonimage asset bytes, **2** for a sound incomplete scope/limit or failed acquisition, and **1** for verifier corruption/reconciliation failure. `verify.py --allow-incomplete` returns0 only when the retained evidence recomputes consistently while its explicit incomplete flags remain intact. It does not promote coverage.

## Checkpoints and access stops

Atomic raw-cache and checkpoint writes bind requests to source URLs, original hashes, publication identity and independent inventory hash. Resume revalidates every cached source, refreshes current publication identity, rejects edition/configuration changes, rebuilds outputs deterministically and fetches only uncached legal ranges. Exact executed revisions are retained by content hash in each run's `script-versions/`; `scripts/` retains the latest run revision. A native export job is durably checkpointed immediately after its publisher POST. Resume validates that original whole-book scope/edition and downloads the same UUID through the observed public publisher download route using an ordinary headed browser. The original UI scope and posted job are retained; no cookies/fingerprints are imported and no second job is created for an existing checkpoint. Actual HTTP status/headers and download failure/length checks are retained. `export-checkpoint.json` binds the completed download hash and original scope UI to that job. A policy change requires a new directory; prior proof is retained under its original policy. The historical stage's final current-source live run was `index-current-final`; `index-no-images-final` is supporting current-policy resume proof. The earlier `index-native-final`, `form-based-pdf-final` and `ordinance-index-live` normalized outputs are superseded by the image policy. Only the renderer reference's retained raw packets are recomputed for the comparison.

The shared publisher gate is `/tmp/compliSolv-american-legal-full-gate` unless `AMLEGAL_GATE_DIR` is set. All processes must share it. Starts are separated by3.5seconds.403/429/challenge stops persist, Retry-After is recorded, and there is no reset command. A challenge requires operator investigation, not another transport/profile/proxy attempt. Direct HTTP returned403 in this stage and remains stopped; the previously qualified ordinary headed-browser route succeeded. Unrelated export-panel polling is omitted during renderer traversal. Fresh whole-export creation follows the visible publisher controls; resumed existing jobs use their observed public UUID download route under the same gate.

Legal-source errors and access blocks stop acquisition and retain durable successful work for resume; failed/interrupted runs cannot pass verification. Unavailable nonimage assets retain their actual HTTP response and a bound unavailable disposition, allow other assets to proceed, and keep attachment completeness false.403/429/challenges always stop the publisher. An exclusive per-output file lock rejects concurrent writers to the same output directory. A missing required document is never treated as a justified exclusion merely to finish. `--retry-unavailable-assets` permits an explicit resume to retry cached unavailable HEAD/binary responses once per asset, preserving immutable earlier response history. It cannot override the publisher access-stop gate. HEAD405/501 falls back to a genuine GET only for an explicit known nonimage file extension; actual downloaded bytes are still format-validated. A corrupted or wrong-edition cache is refused. Same-book references detected in adopted/incorporated language are bound to acquired independent TOC/body IDs; an absent target remains unresolved. References to another book remain required documents.

## Outputs and interpretation

- `run.json`: requested/observed identity, pinned edition, dynamic publication family inventory, policies, executions and status.
- `requests.json`, `raw/*`: original publisher response bytes, response metadata, hashes, scope/ready UI evidence and source URLs. Original HTML/PDF can contain images.
- `inventory.json`, `inventory-end.json`: independently reconstructed recursive TOC nodes, parent/path, source render ranges and pending inventory.
- `checkpoint.json`: acquired IDs bound to inventory hash.
- `sections.jsonl/csv`: exactly one owned TOC-node record. `html` and `text` are normalized under the image policy; original bytes remain in `raw`.
- `pdf-pages.jsonl`: all pages from every retained native publication or required attachment PDF, separate from TOC-node records. Shared PDF bytes use explicit owner aliases, not duplicated page bodies. Positioned text spans/fonts, independent engine character agreement, reading-order diagnostics and ruled-table candidates retain geometry. Unknown table/column layouts remain explicitly unqualified. Raster image objects and page vector graphics become metadata-only `[IMAGE]` markers; no rasterization or image binary extraction occurs.
- `assets.json`: required nonimage assets, deliberate image placeholders, unresolved references and format qualification.
- `coverage.json`: recomputed inventory/missing/extra/duplicate/ownership, text, nonimage attachment, edition, native-file and image-policy fields. Jurisdiction completeness is always false because one selected publication does not enumerate every jurisdiction family.

A complete native PDF file and every extracted page do not by themselves qualify legal-provision segmentation or PDF reading order. `native_publication_files_complete` and `pdf_text_layer_extraction_complete` are separate from `publication_text_complete`. Image omission is intentional; PDF text/section qualification limitations are unrelated to omitted image content. A native HTML file can be complete while linked nonimage ordinances remain unacquired.

## Offline proof and fault tests

```sh
.venv/bin/python collectors/american-legal/test_faults.py
.venv/bin/python collectors/american-legal/verify.py \
  collectors/american-legal/fixtures/nested-synthetic.zip --offline
.venv/bin/python collectors/american-legal/verify.py \
  collectors/american-legal/fixtures/live-index.zip --offline --allow-incomplete
```

The ZIP verifier reads files directly without extraction, network or output writes. It recomputes independent TOC branches, all source hashes, ownership, outputs and coverage instead of trusting a stored success flag. The synthetic fixture is clearly labeled and is not live-law proof. Tests exercise actual production collection/cache/resume: after2 committed nodes, interruption is rejected, resume fetches only3 remaining nodes, and outputs equal an uninterrupted5-node run. Faults include middle-branch loss with all top roots retained, truncated native bodies, duplicate/omitted outputs, corrupt bytes, changed edition, mismatched checkpoints, missing asset dispositions, explicit limits, and image no-fetch/placeholder cases.

An additional whole-body comparison recomputes all30 raw renderer provisions and compares native bodies, raw block IDs and table text/spans:

```sh
.venv/bin/python collectors/american-legal/compare.py \
  /EVIDENCE/index-current-final /EVIDENCE/ordinance-index-live
```

The reference's old normalized outputs are not trusted; its raw response packets are recomputed under the final image policy. Both folders are in the new evidence package, with no dependency on earlier sealed packages. Compact offline comparison fixtures are also included:

```sh
.venv/bin/python collectors/american-legal/compare.py \
  collectors/american-legal/fixtures/live-index.zip \
  collectors/american-legal/fixtures/renderer-reference-raw.zip
```

The renderer-reference ZIP is a raw-only comparison input, not a standalone final-policy collection run. The 54.8MB Cleveland PDF can take several minutes per complete verification because every page is reparsed; its acquisition already ran that verification successfully.

## Prior validated scope and active readiness work

The prior sealed validation established that the genuine independently published San Diego County Comprehensive Ordinance List has30 TOC entries (cover plus1998–2026), all explicit leaves. Full index traversal and a whole-publication native HTML export reconcile all30 IDs and97 rich blocks. The index contains1940 distinct nonimage ordinance-PDF references; those were deliberately not mass-downloaded, so complete ordinance corpus and nonimage attachment completeness are false. This is whole **index-publication** text proof, not a nested whole municipal regulatory code proof.

The historical sealed stage retained Cleveland's independent212-page Form-Based Code PDF and an initial native main-code file. The later readiness acquisition completed the genuine nested primary:6,140 TOC nodes,459 independently captured branches in each of two equal start/end sweeps,43,676 uniquely owned native blocks,322 tables/7,738 cells and5 required PDFs. Its original executed-v3 output is immutable. Independent browser DOM QA subsequently found31 inline-spacing discrepancies; the new serializer fixes source adjacency and the followup package records a new, separately versioned replay and independent re-audit. Inventory/file success alone does not certify lexical table fidelity.

Before scaling, choose each independently published code/charter/zoning/policy family, review county applicability, allocate time for full dynamic inventories and nonimage required documents, and audit special formats. No full runs across all100 jurisdictions have been performed or implied.

## Readiness extension

The active readiness work is recorded in `validation-summary.json` and the new `outputs/collection-readiness-2026-10-17/american-legal` package. The original nested Cleveland primary acquisition is terminal; its original source/execution lineage remains separate from the followup normalization replay and current-source validation. Do not equate the prior index proof or source route mappings with completed primary regulatory-code verification.

All retained PDF attachments now get normalized page records. PDF character agreement, positional text and qualified simple ruled-grid geometry are tested; ambiguous parallel columns, diagram fragments and incomplete ruled grids remain explicit diagnostics. Automatic table candidates do not certify all tables or legal reading order. The offline PDF inspection CLI can qualify already retained native bytes without a new publisher acquisition:

```sh
.venv/bin/python collectors/american-legal/inspect_pdf.py \
  --pdf /PATH/native.pdf --source-url https://example.gov/document.pdf \
  --owner-id publication-id --out /NEW/PATH/pdf-inspection
.venv/bin/python collectors/american-legal/inspect_pdf.py \
  --out /NEW/PATH/pdf-inspection --verify
```

The live-index fixture was recomputed under the current verifier from its unchanged original raw evidence and explicitly records offline reprocessing. This is compatibility replay, not a new live acquisition.

The earlier readiness checkpoint retained45 passing production-path fault cases; current suites and exact counts are recorded separately in the followup receipts. A real localhost headed-browser interruption test also confirms that an in-flight interrupted RPC closes its owned browser processes (0 remaining; 0.083 seconds), without publisher traffic. The active Cleveland run deliberately interrupted a real submitted native job, then resumed the same UUID and retained the actual 22,331,790-byte HTTP200 HTML download; the terminal receipt now retains the complete independent end sweep. Current parser qualification additionally requires the followup source-fidelity audits.

The delivered validator also rejects accidentally supplied separate image bytes before any decoder or XML image parser. A regression mocks both raster and SVG decoders to raise; image URL, MIME and signature cases still return policy-excluded. The completed original Cleveland executed-v3 source predates that defensive unreachable-path removal and remains separately retained; its live execution is not relabeled.

Image MIME types, data URI schemes, input image types and existing CSS image syntax are matched without regard to case. Uppercase image references receive the same literal placeholder, metadata redaction and no-transport disposition; an original raw-cell audit covers the uppercase case as well. The later executed-v5 snapshot is distinct from retained v3/v4 live or implementation revisions.

## Controlled source-fidelity followup

New evidence belongs to `outputs/collection-readiness-followup-2026-10-17/american-legal`; prior packages and executed snapshots remain immutable. The collector runtime in `executed-v6` is distinct from original Cleveland `executed-v3`. A normalization replay copies retained source evidence to a fresh sibling directory, retains the acquisition execution history unchanged, snapshots the new parser separately and recomputes all output and coverage. It never sends publisher requests. Execute from an immutable source snapshot when other development may continue.

```sh
.venv/bin/python collectors/american-legal/replay.py \
  --from /EVIDENCE/original-acquired-native-HTML-run \
  --out /FRESH/PATH/normalization-replay
.venv/bin/python /FRESH/PATH/normalization-replay/normalization-scripts/verify.py \
  /FRESH/PATH/normalization-replay --offline
```

`normalization-replay.json` binds original run/native/output hashes, new output hashes, parser revisions and Python runtime. `scripts/` still describes the historical acquisition; `normalization-scripts/` describes the new replay. A replay is not a fresh acquisition or a new source-edition check.

The inline serializer preserves source adjacency across emphasis, superscripts and styled word fragments. It adds whitespace at rendered block/row/cell boundaries, including nested tables. Source comparisons retain case and punctuation. Independent original HTML browser-DOM cell audits are separate from the Python parser audit; both are needed because identical separator-based text extraction can reproduce the same error in parser and auditor.

Tagged PDFs use the publisher's full forward `StructTreeRoot/K` order, page/MCID ownership, source roles and table span attributes. Every source reference must be accounted for exactly once; unknown/unbound nonartifact glyphs, duplicate references, unsupported object references, unknown roles and unencountered source content fail qualification. Explicit Artifact text is retained as source metadata and excluded from body only by that source declaration. The forward tree preserves cross-page continuations even where a native reverse ParentTree device reports an empty structure path. Literal ActualText variants remain separate from visible Unicode. Geometry contributes only documented word/line separators. No broad case, punctuation or compatibility normalization is used for source-fidelity acceptance.

Each image logical entry remains exactly `[IMAGE]`. Direct Figure-owned vector glyph labels are retained in a separate searchable `available_figure_text` ledger, bound to Figure ID, source reference, page, MCID, hash and source order; these are available source text, never OCR or image transcription. Explicit Caption/text child subtrees remain in the logical body at their source position. The original212-page Form-Based Code has236 Figures and no separately tagged Figure descendants; the generic Figure+Caption case is nevertheless tested. Its102 direct Figure text blocks contain8,629 original characters. Original source image bytes remain only inside the retained native publication; no image stream is decoded or extracted.

`pdf-pages.jsonl` owns each source text block once. The first page carries `tagged_document` with the full source inventory, logical sequence, table grid and clearly labeled derived full-book text/table views. Page-level available-label views refer to those owned blocks. Complete source reconstruction is distinct from inferred legal-provision segmentation, which remains false. `pdf_image_xobject_count_complete` is false for a tagged profile that inventories source Figures instead of image resources; an unknown image-resource count is not reported as a known zero.

Untagged PDFs remain conservative. A page with zero native source glyphs, empty pypdf text and no positioned text is explicitly policy-N/A for text fidelity, with original image draw operations represented by `[IMAGE]`; scanned text is not claimed as transcribed. A separate narrow profile can qualify a single closed native grid only when every original nonwhitespace glyph and its exact order, every cell border/span, optional single-line trailing ordinance citation and every image draw/cell placeholder reconcile. Rotation/cropping, annotations/ActualText outside the profile, open/ambiguous grids, unowned operative text and unsupported layouts remain unqualified. Table-border graphics preserved as a qualified grid are not mislabeled as an extra image.

The tagged parser's durable per-page cache binds source, full source-inventory and parser hashes. An interruption after page1 must resume to byte-identical whole-book output without fetching retained native bytes; JSONL uses deterministic key ordering. A read-only verifier always reparses original source rather than trusting cache success.

```sh
.venv/bin/python collectors/american-legal/test_faults.py
.venv/bin/python collectors/american-legal/test_pdf_tags.py
.venv/bin/python collectors/american-legal/test_pdf_native.py
.venv/bin/python collectors/american-legal/test_pdf_publication.py
.venv/bin/python collectors/american-legal/audit_native.py /EVIDENCE/native-HTML-run
.venv/bin/python collectors/american-legal/audit_pdf_tags.py /EVIDENCE/tagged-PDF-publication-run
```

The independent PDF auditor imports neither `model` nor `pdf_tags`. It reconstructs original roles/order/MCIDs/ActualText/table cells with PDFminer and compares every page against a separate MuPDF native glyph device with image decoding disabled, including available Figure text. `--owner` explicitly selects a PDF owner when a run contains more than one tagged PDF. Raw/native Unicode disagreements remain visible; availability of a full file or a sampled page never promotes an entire book. Current full-book outcomes and residuals are in the followup validation summary, not inferred from synthetic faults.

The current independent font-encoding check permits only an observed, explicitly bound `ff` ligature interpretation: original Type1 font Encoding Differences must map the exact reader CID to `/f_f`, the independent native glyph must have the same font and position, and both literal Unicode sequences remain in the audit receipt. The original source label remains `Coffee`; native `Coﬀee` is retained as a source-encoding-resolved variant, never silently substituted. Wrong-font and moved-glyph faults fail. Every other character comparison remains strict. Run `test_pdf_encoding.py` for the compact2.7KB derived-font fixture; its original native source hash/page/font ID and synthetic nature are recorded alongside it.

## Completed followup proof and remaining scope

The final clean Cleveland retained-source replay (`cleveland-final-v6`) passes full recomputation:6,140/6,140 nodes,459 independently retained branches in each equal start/end sweep,43,676 uniquely owned original blocks,322 tables/7,738 cells and all5 required PDFs. Independent Chrome source-DOM QA prepares images inertly before attachment and confirms all322 tables/7,738 cells with0 mismatches and0 resource requests. Independent source-PDF QA confirms four policy-N/A no-glyph pages plus the fifth page's2,201 nonwhitespace glyphs,18 cells,188 original border edges and9 literal cell-image placeholders; image-stream decode tripwires remain untouched. Original executed-v3 proof and the31 detected inline discrepancies remain retained separately.

Fresh live `form-based-current-v6` completes the independent single-node Form-Based Code publication and the genuine54,780,031-byte native212-page PDF, closing edition check, all-page normalization and fresh read-only source recomputation. The final independent full-book audit passes25,210 source nodes,11,662 references,143 tables/6,658 cells,190,391 nonimage body characters and all102 available Figure-label blocks/8,629 characters. All212 native page checks pass:211 strict Unicode matches and one explicitly source-encoding-resolved `/f_f`/`ﬀ` variant. Both literal variants and per-instance original font/CID/position proof are retained.236 logical Figure entries remain `[IMAGE]`; no image stream is decoded, rendered, extracted or OCRed. The PDF's embedded document creation date is March2024; its containing publisher bundle is2026 S-28, which does not imply that the native file was rewritten in2026.

The frozen v7 package has87 network-free cases across five suites (46 existing production faults,21 tagged/Caption/label cases,9 native-grid cases,7 whole-PDF collection/resume cases,4 exact encoding-binding cases). Its collection/parser runtime is byte-identical to the live v6 runtime; independent auditor, standalone inspector packaging and regression updates have their own exact source hashes. Installation metadata records Node20 minimum from Playwright1.62.1's actual engine declaration; proof used Node24.19.0. The dependency lock records the tested shared Python3.12 runtime, including fonttools4.67.0 and pdfminer.six20251107.

The remaining14 primary publications are running serially from the frozen revision under the shared access-stop gate. Their own receipts determine completion; source-route mapping, synthetic tests and these two completed Cleveland scopes never promote all15 primaries, all separately published books or an entire jurisdiction. The1940 underlying San Diego ordinance PDFs remain an explicit uncompleted secondary-document scope until genuine acquisition/qualification. DOCX/XLSX/ZIP container-byte validation does not qualify those documents' legal text. Unsupported PDF layouts and inferred legal-provision segmentation remain explicit limitations.

### Image metadata hardening revision v8

Revision v8 closes prefixed and multiline `data:image/` payload leaks in arbitrary
HTML attributes, reference metadata, PDF structure attributes and node/inline
ActualText. Images remain excluded from transport and decoding. Opaque image
metadata values become literal `[IMAGE]` with source hashes. Every syntactically
bounded quoted base64 image URI inside ActualText becomes `[IMAGE]` while the exact
surrounding prose remains available. An ambiguous unquoted mixed ActualText value
retains its safe source prefix and original hash, and makes source interpretation
qualification false; the collector cannot silently accept that value as complete
legal text. Multiple image URIs are processed individually.

Run the additional 25 offline policy probes with:

```sh
python test_image_metadata.py
```

Together with the existing five suites, revision v8 has 112 passing tests. The
retained genuine Cleveland HTML and PDF proofs keep their original v3/v6/v7
execution lineage. Their metadata exposure/differential receipt identifies whether
this policy-only revision affects those exact source bytes; that receipt is an
offline compatibility check, not a fresh publisher acquisition. The remaining
primary live queue continues its already frozen v7 source independently.


### Native auxiliary notes and fresh-directory resume revision v9

Revision v9 retains publisher footnote headings and tables that appear outside
`rid-*` rich blocks. A fragment qualifies only with one independently inventoried
section owner in its source wrapper, an immediately preceding `Notes` heading,
and unique reciprocal section-local `text--n` / `foot--n` anchors. The original
fragment, DOM path, marker labels, source hash and section owner remain in
`native_auxiliary_fragments`. Original rich-block ownership is still reconciled
exactly once. Other unowned text, ambiguous owners, missing reciprocal links and
duplicated blocks fail closed. Note cells use the same HTML/image normalizer:
images become exact `[IMAGE]`, without payload retention, transport or decoding.

The first Dallas v7 live run downloaded a genuine44,379,988-byte whole-code native
HTML export but stopped on two such source footnote tables. A separate v9 retained
source normalization reconciles4,542 independently inventoried nodes,53,570 rich
blocks,4 auxiliary fragments,583 tables and70,000 cells. The independent Python
original-DOM audit passes all table text/tags/spans/nesting. Distinct inert-browser
source QA is reported separately. This does **not** complete Dallas:339 unique
required nonimage references and the independent closing inventory/edition check
remain outstanding. The old failed run and its executed v7 source are preserved.
The complete Cleveland HTML normalized JSONL and CSV remain byte-identical under
this revision; its historical acquisition/PDF proofs keep their earlier revisions.

To resume an old same-image-policy acquisition without modifying its directory,
use the new standalone operator wrapper. The source must have intact raw hashes;
output must be fresh and outside the original. It copies original evidence,
retains an original-file manifest and execution history, invalidates PDF parser
caches, records operator lineage, then invokes ordinary `collect.py --resume`.
It rechecks live edition identity and obeys the same persistent publisher gate.
It does not reset access stops, redownload valid cached native bytes, or acquire
images. Source edition drift remains a failure requiring a fresh collection.

```sh
python collectors/american-legal/resume_copy.py \
  --from /EVIDENCE/original-failed-or-acquired-run \
  --out /FRESH/PATH/operator-resume
python collectors/american-legal/verify.py /FRESH/PATH/operator-resume --offline
```

`--prepare-only` performs the copy/checks without starting a browser or publisher
requests, prints the exact resume command, and leaves `operator-prepared` status,
which the verifier rejects as incomplete. Run that printed command once ready;
keep its source directory frozen during execution. `--upgrade-assets` may only
strengthen an original `reference-only` policy to nonimage `download` in the fresh
copy. `--retry-unavailable-assets` explicitly retries prior nonimage HTTP failures;
it cannot bypass403/429/challenge stops. Wait for other American Legal batch work
to finish before starting another publisher job. Current live queue remains its
original immutable v7 revision and is never relabeled v9.

Run `test_native_notes.py` and `test_resume_copy.py` in addition to the six existing
suites. The new cases exercise omissions/ownership/reciprocal-link drift, original
raw corruption, stale image policy, unsafe paths, fresh-copy preservation and
incomplete-state rejection. v9 has129 passing cases including the auxiliary-note
multiline image payload/no-transport/no-decoder regression. The precise retained
source results, remaining gaps, original live queue status and frozen source hashes
are recorded in the v9 section of `validation-summary.json`.


### Declared-image anchor hardening revision v10

A source anchor/link whose `type` declares an image now receives `[IMAGE]` even
when its URL uses an opaque extension or a `data:application/octet-stream` URI.
Normalization removes that known-image payload, retains available label text and
source/descendant IDs, and keeps image references excluded from download. Ordinary
nonimage document anchors remain required documents. This is a narrow HTML context
fix; transport, browser/rate gate, PDF parsing and existing metadata redaction are
unchanged. Run `test_image_context.py` for two direct `html_record` regressions
with network/image-decoder tripwires and a nonimage control. All131 cases pass.

A hash-bound scan of the complete retained Dallas and Cleveland native HTML files
finds zero anchors/links with the changed declared-image predicate (24,168 and
17,461 anchors/links inspected). The added branch therefore cannot change those
exact normalized outputs. This is a source-exposure/equivalence proof, not a fresh
acquisition or new full replay. Their original executed revisions remain intact.
The independent inert Chrome Dallas audit also passes583 tables/70,000 cells with
zero mismatches/resource requests;339 required nonimage references and the closing
source checks still prevent Dallas completion. Frozen v9 and the live v7 queue
are preserved separately. No new publisher traffic, image decoding, extraction,
rendering or OCR was used for this revision.


### Source-reference and dependency compatibility revision v11

The v11 lock changes only SoupSieve2.8.4 to3.0.3 to match the actual shared
Python3.12.14 runtime. All six declared family requirements and BS4's indirect
`soupsieve>=1.6.1` constraint are satisfied; all twelve lock pins match.
Use the exact lock for a tested standalone Python installation. The ten fixture
suites pass137 cases on SoupSieve3.0.3. Full retained-source comparisons pass for Dallas (4,542 records) and Cleveland
(6,140 records). Dallas differs only in the fifteen explicit asset aliases; all
other fields and CSV bytes match. Cleveland JSONL and CSV are byte-identical.
The root reviewer independently reran all 137 fixtures. The compact receipts
are in [the v11 proof directory](../qa/followup-proof-receipts/american-legal-v11/).
No environment was modified while the original publisher job ran.

The alias profile addresses only `http://"https://files.amlegal.com/pdffiles/...pdf`
when its embedded exact HTTPS URL and same numeric ordinance citation are
independently observed as a direct href in a different inventoried owner of the
same native source SHA/edition. Citation must equal the PDF basename. It retains
the original malformed href in HTML/raw reference metadata and adds explicit
`source_alias` corroboration to the required asset reference. Unknown citation,
missing independent owner, wrong edition and other unsupported matches fail
closed; images stay excluded. No destination is guessed or waived. Dallas has
fifteen such occurrences of one malformed duplicate32195 URL, with a valid direct
32195 URL in its Code Comparative Table.339 raw required URLs map to338 required
acquisition targets only when this source relationship is proven. No attachment
bytes or semantic qualification are inferred from the alias.

The browser profiles remain distinct. Standalone `package.json` pins Node
Playwright1.62.1, matching the earlier genuine AL live proofs. The shared launcher
uses the official Python Playwright1.64.0 wheel's bundled core
1.64.0-beta-1791568591000 with Node24.21.0/Chrome155.0.8059.84 and exports
`COLLECTION_PLAYWRIGHT_CORE`, `PLAYWRIGHT_MODULE_ROOT`, `NODE_BIN` and `PYTHON`.
A close-only AL bridge RPC qualifies module/dependency wiring without launching
Chrome or requesting publisher content. The shared setup's separate headed doctor
proof does not relabel earlier AL publisher runs or qualify a new shared-profile
live AL acquisition. No local/global environment or persistent gate was reset.

Live Dallas continuation must wait until the original entire serial queue has
finished, its child is gone, the publisher slot is unoccupied, and the persistent
gate allows work. The queue immediately advances after each child, so completion
of Fort Worth alone is not a free slot. A fresh operator directory preserves the
failed v7 run/native job and must perform a fresh overview/edition check before
cached source reuse. Required documents and the closing inventory remain pending.

### Explicit short dispositions

Two Fort Worth units have source-explicit dispositions that the generic minimum-text-length check missed: an own body exactly `[Repealed]` and a numbered native Section heading ending `RESERVED.`. The collector now retains their exact text, IDs and blocks and adds source-fragment evidence for the disposition. It does not infer a disposition for the other seven unresolved units. The rebased source passes 146 tests, including nine portable actual-source/fault cases; all original fields in those nine records match except the two classification/evidence additions. See [the evidence](../qa/followup-proof-receipts/american-legal-fortworth-status/). The two unavailable required exhibits and existing PDF semantic limitations still prevent complete Fort Worth acceptance. This is an offline normalization correction, not a new full acquisition.
