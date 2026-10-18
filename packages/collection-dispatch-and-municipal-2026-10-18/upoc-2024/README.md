# Historical Overland Park UPOC 2024: complete native method

This isolated packet qualifies a runnable **historical native-document method** for publication `82-8fbdce15716d`. It is not a new publisher acquisition or a complete legal-text/edition pass. Exactly one corrected v2 full 172-page extraction was executed against the retained original using the current collector. The immutable v1 predecessor remains separately preserved: an independent synthetic probe found its inline-image guard omitted dimension-only image dictionaries. The v2 guard closes that gap; GUARD-CORRECTION-LINEAGE.json and the exact source diff retain the history. Subsequent checks used the complete captured IR and did not parse the native pages again.

The actual HTTP200 PDF receipt is for:

`https://codes.opkansas.org/municipal-code/doclibrary.aspx?id=29e4fde6-8eab-4f2c-a715-8914aa24cfe0`

The exact native SHA-256 is `877c6e874d4de7873d22dd51443fd5c42169445ad2955db3836841a105a57102` (1,658,134 bytes; 172 physical pages). Its observed filename is `UPOC-Criminal-Code-Index-(2024)-Final-v2.pdf`. The catalog's `online.encodeplus.com/regs/overlandpark-ks/` URL remains separately preserved as an **unverified acquisition alias**. This method never changes a failed/missing source into that alias or infers a redirect.

The native page-7 witnesses identify Overland Park, POC-3460 and the printed 40th edition; page 8 states the 2024 copyright. The city catalog's effective-date label is retained as a literal catalog label, not inferred present applicability. This 40th/2024 native file does not replace the separately retained 42nd/2026 source.

## Verified full scope and remaining limits

The current parser emitted all 172 page records, with 28,603 source words and 46 exact `[IMAGE]` placeholders. All 745 currently canonical detected cells independently agree. The original superseded index grids retain all 514 detector cells, including all 272 false comparisons, in diagnostics. The finite source index reconstructions on pages 1 and 169 remain distinct from whole-book legal structure.

All 172 current records were compared with the prior entire-book cached IR. After explicit catalog namespace/raw-reference changes, and the documented collection-context fields (`heading`, `publication`, `jurisdiction`, `path`, `document_source_title`, `primary_source_owners`), **every other field is identical**. The comparison retains the old IR and the changed source-context ledger; no legal text, table, image position or unresolved character was corrected by guessing.

There remain 102 pages with undecoded CID literals and independent text-engine disagreements. Existing finite font diagnostics are not silently applied. `pdf_extractable_text_reconciled`, whole table/section/list/reading-order qualification, publication text, external dependency, current adopted edition and jurisdiction completeness remain false. Detected-cell agreement does not establish that every legal table was detected or correctly interpreted.

This packet carries one original successful source receipt. There was no new HTTP request or closing sweep. `start_end_consistent` is null and `closing_acquisition_performed` is false. A complete retained native file/page traversal is separate from current currency and full legal completeness.

## Ordinary commands without Codex

Use the existing pinned standalone Python environment. No new dependency was added; the native family requirements are in `candidate/collectors/encodeplus/requirements.txt` and the captured `actual-retained-full172/collector-source/collectors/encodeplus/requirements.txt`. The tested runtime was Python 3.12.14 on macOS 26.6.2 arm64, pypdf 6.21.1, pdfplumber 0.11.8, pdfminer.six 20251107, pypdfium2 5.14.0, fonttools 4.67.0 and cryptography 50.0.2. See the checkpoint for the complete exact source/runtime tuple.

For the published packet, from the repository root:

```sh
.collection-runtime/venv/bin/python \
  packages/collection-dispatch-and-municipal-2026-10-18/upoc-2024/actual-retained-full172/collector-source/collectors/encodeplus/retained_native.py \
  --verify packages/collection-dispatch-and-municipal-2026-10-18/upoc-2024/actual-retained-full172
```

This ordinary no-`-B` command has been tested. It checks the complete captured source/version/config/raw/receipt/output bindings, every page identity, the historical identity witnesses, complete JSONL/CSV serialization and the coverage report. It writes nothing, adds no bytecode, and does not rerun the native parser. Its successful exit means the retained native/artifact scope is verified; the returned legal/edition/jurisdiction flags remain false.

To rerun the **whole-book extraction** into a fresh directory, use the candidate/current installed retained-native CLI with the same original PDF and receipt. This was the method executed once for this packet:

```sh
.collection-runtime/venv/bin/python -B collectors/encodeplus/retained_native.py \
  --config collectors/encodeplus/configs/native-82-8fbdce15716d.json \
  --input packages/collection-dispatch-and-municipal-2026-10-18/upoc-2024/actual-retained-full172/raw/source.pdf \
  --receipt packages/collection-dispatch-and-municipal-2026-10-18/upoc-2024/actual-retained-full172/raw/source.pdf.receipt.json \
  --out /absolute/fresh-upoc-2024-output
```

Before integration, substitute the packet's `candidate/collectors/encodeplus/` for the two `collectors/encodeplus/` source/config paths; no code edits are needed. Extraction validates exact native bytes, successful actual URL/MIME/filename receipt and physical-page pins; runs the existing full parser; and retains the complete original, current outputs, exact collector-source snapshot and false completeness dimensions. Existing outputs are refused. There is no partial traversal, automatic resume or network fallback in this offline command. Use a genuinely new output for another extraction; `--verify` is the read-only path.

For a future authorized publisher acquisition, the **existing gated native collector** uses the same new config:

```sh
.collection-runtime/venv/bin/python -B -m collectors.encodeplus.native_document \
  --config collectors/encodeplus/configs/native-82-8fbdce15716d.json \
  --out /absolute/fresh-native-publisher-output
```

That future command is not claimed as executed here. It retains the existing publisher gate/stops, pins the entire historical bytes/pages, and performs its actual opening/closing requests. A refused route or changed file fails rather than silently substituting another host or edition. Root must integrate the explicit catalog override before the common `collect.py run --target 82 --publication 82-8fbdce15716d` dispatch is advertised as available.

## No-image policy and tests

Original native PDFs may contain images. The extraction guards prohibit network access, image-stream decoding, PIL pixel paths, PDFium image-data/bitmap access, page rendering and OCR. The actual corrected whole-book extraction recorded zero forbidden operations. Before that run, original-decoder stubs proved Image subtype and plain/slash W/H and Width/Height cases refuse across PDFMiner and both pypdf stream classes; ordinary text/page/font controls remain allowed. The independent peer also verified eleven image-context forms. Normalized JSONL, CSV and coverage are byte-identical to v1, while the corrected source/checkpoint/archive bindings are new. Native image identities/positions remain metadata with literal `[IMAGE]`; there are no separately extracted image files.

From the selected packet directory:

```sh
/path/to/pinned/python -B test_retained_native.py
python3 -B -S test_qualification.py
python3 -B compare_cached.py
```

The thirteen retained-method tests exercise exact full-page scope and unchanged false limits, observed URL versus catalog alias, wrong/truncated bytes before parsing, refusal/MIME/filename/receipt corruption, overwrite refusal, forbidden image/network APIs, missing/reordered pages, cover witness corruption, read-only replay without native calls, corrupt artifacts, escaping source symlinks and read-only same-source hardlinks. Five pure qualification tests cover the exact historical kind/config/archive, scope/ID/alias/current-flag refusal, source/page/hash/kind faults, missing/corrupt archives and escaping config symlinks. No test reparses the PDF.

## Qualification and promotion boundary

`REGISTRY-OVERRIDE-PROPOSAL.json` proposes a distinct kind, `historical-observed-native-receipt-full172-retained-current-parser`, with `mapped_only` and `full_live_verified=false` preserved. The pure `historical_upoc_qualification.audit(here, catalog)` validator binds the exact historical ID, actual source URL, config, successful receipt, original native SHA, full 172-record/CSV inventories, all page/word/image denominators and explicit unresolved flags. Its compact original witness archive is separate from the six current-native-anchor qualifications and Clark's live native proof. Core/root own the shared routing/overlay integration; none was edited here.

The exact executed native config and family source are unchanged since extraction. New regression files live outside the family root so `code_hashes` remains exactly the captured 55-file tuple. `WHITELIST.json` proposes only the new config, reusable retained-native CLI, portable external regression and historical qualification helper/archive/manifest. All other source copies are context. Do not replace unrelated collector files.

The exact executed config has an original-context short evidence pointer; `EVIDENCE-REFERENCES.json` supplies its published repository-relative equivalent without rewriting executed bytes. The selected packet includes the referenced original receipt. `SOURCE-PROVENANCE.json` identifies the immutable local prior source/cached-IR origins; it does not promise restoration of unrelated large local evidence.
