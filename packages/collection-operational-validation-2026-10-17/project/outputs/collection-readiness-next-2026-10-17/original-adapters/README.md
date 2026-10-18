# Isolated original-publication adapters

These modules are proposed integration additions for `original-flagstaff-az` and `original-king-county-wa`. They do not modify the running official collector or sealed prior evidence. `configs.json` defines exact source scopes. Both collect complete source-listed publications by default; neither claims whole-jurisdiction coverage for separate related publications.

## Standalone setup

Use Python 3.12 and an installed ordinary Google Chrome. Create a virtual environment here or elsewhere, then run `python -m pip install -r requirements.txt`. Chrome is selected with Playwright `channel='chrome'`; no bundled browser download or Codex dependency is required. Tested runtime is Python 3.12.14, beautifulsoup4 4.15.0, Playwright 1.64.0, Chrome 155.0.8059.84 on macOS. Native Word ZIP/XML parsing uses the Python standard library and does not require Word, LibreOffice, lxml or image tooling.

From this directory, the full entry points are:

```
python collect.py --target original-flagstaff-az --out fresh/flagstaff
python collect.py --target original-king-county-wa --out fresh/king-county
```

Fresh directories must be empty. Exit 0 requires every implemented publication completeness gate. Exit 2 means an incomplete publication or unresolved source condition; exit 1 is a runtime/configuration error. A successfully downloaded original file is a separate transport outcome and does not override an incomplete audit.

## Source acquisition and edition policy

Flagstaff uses the publisher's ordinary headed frameset to expand every source-observed City Code root and retain its full descendant TOC. The default then acquires every distinct source-listed HTML document through ordinary same-origin Chrome requests, with fresh opening and closing native-reader inventories and source currency. Repeated Charter fragment IDs are preserved as distinct source TOC edges using root/order context; document bodies are acquired once. The normalizer reconciles every TOC edge, source heading, source block, table and required nonimage dependency. Charter is within the publisher's City Code tree; the separate Employee Handbook is outside this primary scope.

The native Print/Save controls were also genuinely exercised. Root-only selection returned only18 introductions (36,730 bytes); selecting all2,658 native controls returned HTTP200 application/x-perl with zero bytes. Those are retained failed/partial export outcomes. They are not whole-publication proof. `flagstaff_full_collect.py` retains the observed native-export workflow separately; `collect.py` uses the full HTML traversal and does not retry an empty native export.

King County reads the actual official landing index twice and requires exact equality of all source-listed HTML document URLs, headings, per-document updated claims, and native alternative links. It acquires all listed documents, not a hardcoded sample. The native stage acquires the actual Word alternatives listed by that same index and checks opening/closing inventory again. Original DOCX packages remain intact. The supplemental raw-w:t diagnostic compares literal Word/HTML strings and table counts; ordinary format layout differences do not become a semantic completeness gate. Native structural import and independent source DOM/XML audits qualify ownership and text separately. Index/body updated claims remain separate; conflicts prevent edition completeness. The County Code index includes Charter and editorial documents; Board of Health Code is a separately linked publication outside this primary boundary.

All legal source blocks, including introductory matter, container history, tables, and source notes, receive one owner. Source-order block indices and document hashes are retained. Citation numbers are never deduplication keys. Heading-only or unknown source conditions require explicit disposition rather than silent deletion. Image-only content retains its heading/identity and literal `[IMAGE]`.

## Offline replay and source import

Normalization performs no network requests:

```
python king_normalize.py --source evidence/king-county-live-v2 --out fresh/king-normalized
python king_native_audit.py --html-source evidence/king-county-live-v2 --native-source evidence/king-county-native-word-v2 --out fresh/king-native-audit.json
python flagstaff_html_normalize.py --source evidence/flagstaff-html-full-v2 --out fresh/flagstaff-normalized
python king_word_import.py --source evidence/king-county-native-word-v2 --out fresh/king-word-normalized
```

Read-only verification uses a temporary scratch directory to recompute all normalized records and coverage from original source bytes. It compares all deterministic output files and refuses a changed parser revision. It does not change either evidence input:

```
python verify.py --family king --source evidence/king-county-live-v2 --normalized evidence/king-county-normalized-final-v6
python verify.py --family flagstaff-html --source evidence/flagstaff-html-full-v2 --normalized evidence/flagstaff-html-normalized-qualified-v3
```

A relocated whole retained source directory is an offline import: use the same source directory structure/checkpoint/receipts and run the normalizer into a NEW directory. This imports hash-verified retained evidence and does not relabel it as fresh acquisition. An arbitrary operator HTML/PDF file, a missing receipt, or an excerpt is insufficient to bootstrap a complete publication. Native source receipt URL/selection/edition/closing checks remain required. Manual publisher downloads without this provenance stay unqualified until independently bound to a full source inventory.

## Durable resume and access stops

The complete entry point supports `python collect.py --target <target> --out <existing-output> --resume`. It requires the same target and exact executed module/configuration revision. It invokes resumable stages and read-only verification of completed normalized output. Partial malformed normalized output requires explicit operator review; it is not silently overwritten.

King HTML acquisition writes each response and receipt before advancing an atomic checkpoint. `python king_acquire.py --out <existing-html-source> --resume` accepts only exact executed acquisition code, unchanged source bytes and no retained failure. It validates the current index before acquiring only missing documents, then performs a new closing inventory check. A completed hash-verified capture resumes without any publisher request. `python king_native.py --source <html-source> --out <existing-native-source> --resume` applies the same missing-only and exact-version rules to the source-listed Word alternatives. Source failures are never automatically retried. Flagstaff full HTML acquisition also checkpoints each document. `python flagstaff_html.py --out <existing-source> --resume` checks exact code and raw hashes, retains the original opening inventory, freshly validates the publication before acquiring only missing documents, and recomputes the closing inventory. An interrupted partial closing remains in the ledger as an abandoned attempt; its source bytes are never overwritten. Retained failures and publisher stops prevent automatic resume. Native export is atomic at publication-file level; failed/empty exports remain incomplete.

Both adapters use the same persisted per-host official gate as the running official collector, default `/tmp/compliSolv-official-publication-gate`, with at least 3.5 seconds between source requests. Browser document/XHR/fetch requests and HTTP redirects reserve the same gate. Any 403, 429, Retry-After, or challenge causes a persisted operator-review stop. Existing stops are not cleared, retried, or evaded. Stopped eCode360, municipal.codes, Municode, Spokane static and Louisiana health hosts are explicitly forbidden. Cleanup closes only the browser/context created by this run.

No image resources are separately requested/downloaded/extracted/rendered/OCRed. Browser image/font/media requests are blocked; detected image responses are not read. Original source HTML and Word files may inherently contain image markup or embedded image files; these remain inside originals. Normalization replaces image/SVG/picture/CSS/background/embedded-image forms with `[IMAGE]`, preserves IDs/reference hashes, and redacts image data in metadata. Nonimage attachments remain separate required dependencies unless an explicit retained-primary-document or source-backed independent-reference disposition resolves them.

## Evidence and limits

`executed-acquisition/` records exact code at the start of each acquisition. Earlier failed/partial attempts remain immutable. Normalization fingerprints distinguish later offline parser work from original acquisition. `validation-summary.json` records terminal live scopes, exact commands, counts and unresolved conditions. Synthetic fault tests are separate from real source validation. Do not promote current successful transport, a retained-source replay, a partial native preview, or a passing stop test into a complete publication claim.


## Current source fidelity and reference recovery

The isolated model uses a DOM boundary text walker. Inline runs remain adjacent (`T` + `itle` becomes `Title`, `1<sup>st</sup>` becomes `1st`); blocks, lines and table cells separate text. HTML comments, declarations and processing instructions do not enter legal text. Whole-cell span/row metadata and literal `[IMAGE]` placeholders are preserved. The original get-text separator output is retained as an unqualified historical attempt, not selected final proof.

Native Word import never opens `word/media/*` or image OLE binaries. It preserves paragraph/table order, notes and source XML hashes; actual `PBrush` and `Word.Picture.8` OLE relationships are explicitly pictures under the image policy. Unknown OLE documents remain required and unresolved. Known ASCII Word symbols in ordinary Unicode fonts and hard/soft hyphens are decoded without reading image members. The earlier raw-w:t cross-format diagnostic ignores Word layout/symbol/note constructs and is not an assertion that22 native legal bodies differ. Final qualification depends on the independent raw-DOM/XML audits and the explicitly selected parser revision.

King County's incorporated legacy MRSC Appendix C link redirects to404. The current publisher's actual publications page links a December2025,90-page PRA PDF; original bytes were acquired, hashed and parsed without extracting pixels. `king_mrsc_binding_candidate.py` retains the official publisher's scope explanation and a closing current-route check. The current Appendix C scope must be reconciled with the County's dynamic incorporation wording and qualified through the strict PDF importer before automatic substitution. No credential requirement has been observed; this is a source-reference/edition issue. Nine official index-versus-body update-label mismatches remain visible in both HTML and Word. The compared fields are the index's per-document `(Updated: …)` claim and each original document's literal `UPDATED …` marker, not HTTP Last-Modified, download time, or legal effective date. Exact labels/context are retained and neither value is silently chosen. These publication-update consistency gaps prevent an edition-complete claim even when every source document has been acquired.

Legacy Symbol-font characters have their original declared fonts and code/literal variants retained. Exact source-bound PDF Unicode recovery qualifies17 specific F025/F0B2/F0B0 occurrences, preserving original Word XML/raw hashes and HTML fragments. The actual source-listed Title9/Title16 PDFs provide explicit ToUnicode mappings and unique section/context matches. Disposition318 Word F0BE occurrences map only to private U+F8E7 in the actual source PDF; its embedded font lacks post/cmap semantic names and has no ActualText. Those positions and corresponding320 HTML font runs remain unqualified. No font-wide mapping, glyph rendering or pixel inspection is used. Both normalizers independently require `character_semantics_complete`; they cannot become complete merely because other gaps resolve. `king_symbol_audit.py` records exact same-document unit/cell literal matches as supplemental provenance and does not infer Unicode glyphs from a font name.

Nine Charter own-body-empty nodes are explicit structural parents of following decimal childsections; children retain their own text and IDs. Charter650.40 is instead an exact-hash source disposition: original HTML and Word, and original53page CharterPDF page19, all place its empty own-body heading immediately before Section670. The normalizer retains it as `confirmed_published_empty_own_body`, does not infer repeal, and refuses that disposition for changed source hashes.

Explicit inventory migration used by the selected Flagstaff live run:

```
python flagstaff_html.py --out fresh/flagstaff --inventory-source evidence/flagstaff-full-export-v3 --import-inventory-capture evidence/flagstaff-html-full-v1
```

This is a NEW run with hash-verified retained source-derived inventory and exact acquisition provenance, fresh final-code body requests, and fresh closing validation. It is not described as an entirely fresh final-code acquisition of the opening TOC. Only the recorded parser-only missing-currency-marker attempt is accepted by this narrow migration path; source access failures cannot be imported to bypass a stop.

Run the network-free fault suite with `python -m unittest discover -s tests -v`. Current tests include missing/duplicate/corrupt/wrong-edition/interruption faults, exact resume/missing-only acquisition, preserved interrupted closing, version refusal before browser startup, retained access-stop refusal, native image-member-read tripwires, required unknown OLE/PDF dependencies, native note positions, DOM inline joins and comment exclusion.

The selected Flagstaff body capture predates the added top-level root guard. After its complete body/reader closing, `flagstaff_root_guard.py --source evidence/flagstaff-html-full-v2 --opening-source evidence/flagstaff-full-export-v3` retains the exact earlier native root opening and performs fresh native root/disclaimer closing. Its separately hashed receipt and archived pre-finalization checkpoint make this explicit retained-source plus fresh closing validation. The default new collector performs root checks at both ends automatically. Browser HTTP200 challenge titles also cause a persisted publisher stop; no challenge control is interacted with.

Selected final metadata policy replaces a whole known image-bearing attribute/metadata-field value with `[IMAGE]` and hashes its full original value. Newlines and tabs cannot leave a continuation payload behind. Visible legal DOM siblings and captions remain intact. `offline-tests-final-preflight-v6.log` records70 network-free tests, including actual native root anchors, multiline metadata preservation, exact source chronology and route binding, legacy glyph guards, and no image body/member reads. The final verifier independently checks opening/body/closing timestamps, exact whole-index route coverage, native DOCX URL identity, raw hashes and source errors before replaying normalized content.


## Selected candidate freeze

The selected final outputs are Flagstaff `evidence/flagstaff-html-normalized-qualified-v3`, King HTML `evidence/king-county-normalized-final-v6`, and King Word `evidence/king-county-word-normalized-final-v8`. Final read-only proof receipts use matching `flagstaff-final-v3`, `king-final-v6`, and `king-word-final-v8` names. Every normalization snapshots exact code at its start and fails if any captured module changes before completion. Historical outputs and receipts retain their earlier exact revisions.

King Word owns57,158 body units,30 foot/endnotes and7 ancillary header/footer source parts separately (57,195 records). It retains13 body image positions plus1 ancillary picture placeholder. The source footer's cached1997 text is ancillary source content, not a current publication update date. Native media/OLE picture members are never opened.

The final70-case offline suite includes exact-source character profiles, PUA rejection, header/footer ownership, mandatory-profile preflight and network tripwires. Known metadata attributes have explicit whole-value redaction boundaries. A quoted inline image URI in legal prose is replaced without removing surrounding text; ambiguous unquoted legal-text image payload fails closed.

Both originals remain isolated integration candidates. Prior King independent source-DOM/XML conservation reports are retained with their exact reviewed scope; final glyph/ancillary/metadata deltas require follow-up. Flagstaff's377-table independent source-DOM review is queued and is not recorded as passed. Primary Flagstaff completeness and successful own raw replay do not substitute for independent promotion review. King remains incomplete even when full raw replay agrees.

Copy all top-level Python files and JSON configuration/profile files, plus `requirements.txt`, together; `module-manifest.json` lists the precise required module closure and hashes. The source evidence directory is an explicit CLI argument and may be relocated intact. No code imports an old package or external project directory. Run `python verify.py --family king-word --source evidence/king-county-native-word-v2 --normalized evidence/king-county-word-normalized-final-v8` for the native stream. All normalized legal streams are named `records.jsonl`; HTML also emits `records.csv`. Word notes and ancillary parts are records within the same JSONL stream.
