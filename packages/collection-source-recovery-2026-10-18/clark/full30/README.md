# Clark County current Title 30 and associated documents — full file/page validation

This run selects the actual official group labelled **Title 30 - Effective 9/17/2026**: one core code and 29 associated map PDFs. It excludes the separate 66-file historical group. This is a selected official publication bundle, not the entire county code or all uncodified law. `config.json` is an isolated source-derived candidate; the production catalog is unchanged.

The first fresh official-page response matched the frozen discovery bytes, group, labels, and ordered 30-URL inventory. The fresh core PDF matched the previously retained 12,199,096-byte native original. The opaque filename containing `10.7.2026` does not establish an October effective date; the selected source group and prior cover state September 17. Source text and locators are retained literally.

`run.py` uses the exact `runtime/` official collector snapshot and the already installed fresh-setup runtime. It first captures all 30 original native PDFs using ordinary shared HTTP transport with its existing persisted host gate and 3.5-second spacing. It stops on refusal or source mismatch; it does not reset gates, retry denials, change hosts, use browsers, or fetch page resources. Native PDF headers are checked without normalizing before capture terminal. The normal collector's `--from-cache` implementation then imports authentic successful native files and performs fresh discovery, full all-page coordinate normalization, a later actual discovery response, and all-file later native responses. These later bytes supply closing checks; cached bytes are not presented as a closing response.

All image/pixel/render APIs are guarded. Original PDFs may contain intrinsic embedded images; those original source bytes remain intact. No separate image resource is requested, decoded, extracted, rendered, or OCRed. Normalized omissions use the exact `[IMAGE]` marker and preserve available native text/labels. A map filename is not evidence of absent native text. File/page capture does not qualify legally correct reading order, arbitrary table detection/spans, complete legal-unit hierarchy, dependency closure, or current-law/edition applicability. Semantic/jurisdiction flags remain separate and conservative.

## Commands

The executed interpreter is recorded exactly in `runtime-receipt.json`; the tested environment is Python 3.12.14 at:

```
/Users/oliverflint/My Drive/Claude/Projects/CompliSolv 2.00/outputs/collection-readiness-post1997ee1-2026-10-17/fresh-setup/runtime-v1/venv/bin/python
```

The ordinary standalone full collector entrypoint for a newly authorized run and an empty new output is:

```sh
"$PYTHON" -B /absolute/path/to/clark-title30-live-v1/runtime/collect.py \
  --config /absolute/path/to/clark-title30-live-v1/config.json \
  --out /absolute/path/to/NEW-EMPTY-OUTPUT
```

No limit flag is used. This is the same standard collector used in the successful executed run; the recorded run additionally performed a separate capture-first phase, then used standard `--from-cache` to defer normalization until all 30 initial native captures were terminal. The standard collector intrinsically excludes separate image resources and never renders native pages. It may interleave capture and parsing in a fresh direct CLI run. Existing transport host stops apply; an old successful receipt is not permission to retry a later denial.

Historical guarded capture-first driver (already executed; **do not automatically rerun/retry**):

```sh
"$PYTHON" -u -B /absolute/path/to/clark-title30-live-v1/run.py
```

After collection is terminal, read-only offline verification is:

```sh
"$PYTHON" -B /absolute/path/to/clark-title30-live-v1/verify_guarded.py
```

The guarded verifier invokes the standard `runtime/verify.py` against `run/`. It reparses the original native files, checks the bound source/receipts/inventory/cache/checkpoints, exact output/CSV correspondence, and closing evidence, while refusing network and image APIs. Exit 0 means requested file/page level only. It is not full legal-semantic qualification. The verifier does not modify the captured run. New capture/verification evidence is outside prior sealed packages.

`capture-audit.json` binds the successful initial 31 responses (one page plus 30 PDFs), 47,115,273 native PDF bytes, their exact native and receipt hashes, and final host. `opening-identity.json` holds the fresh selected group. `run/cache-import.json` explicitly records authentic initial native reuse, source snapshot and config. `run/checkpoint.json` and `run/coverage.json` distinguish file/page completion from all other dimensions. `status.json` is the live driver status; final receipts/summary are written only after terminal outcomes.

## Terminal producer outcome

The executed full collector terminated with exit 0 at 2026-10-18T03:52:56.364856+00:00, for requested `file_pages` only: 30 documents, 381 physical pages, 229 `[IMAGE]` markers and all 30 later native checks matching the initial hashes. The later official page is byte-identical to opening. The initial and closing receipts are actual distinct requests. It retains 226 detected tables/7,488 cells, with 196 independent cell disagreements and 43 pages having review conditions. Native text engines and source word/glyph conservation agree on all pages, but U+F0FC remains unqualified on core pages 225 and 226. `cell-disagreements.json`, `page-review-conditions.json`, and `unmapped-codepoint-pages.json` retain exact source ownership and evidence. Legal-semantic, reading-order, dependency/edition and whole-jurisdiction claims remain unqualified. The separate read-only verifier outcome is recorded in `verify.stdout`/`verify.stderr`; consult the final summary rather than inferring it from producer exit 0.

The single planned guarded verifier terminated exit 0 at 2026-10-18T03:55:57.274171+00:00 after 150.068 seconds. All 177 run files were byte-identical before/after and all forbidden-call counters were zero. It qualifies requested file/page level only. It measured 149,304 native source words, 354 pages with applicable native glyph comparison and 27 source-proven no-native-text-glyph pages. `SUMMARY.json` is the final compact result. No further parsing or publisher requests were made.

The compact mirror omits only the duplicate initial `capture/raw/*.bin` bodies: exact byte-identical counterparts remain under `run/raw/`, with original receipts and `compact-body-aliases.json` retained. The complete original capture remains outside the compact mirror. The historical capture-first driver is execution provenance and should not be rerun in place. To collect a newly authorized source use the ordinary standard command above with a new empty output. Portable byte/proof verification (no PDF parser/dependencies/network) is `python3 -B /absolute/path/to/packet/verify_packet.py`; redirect output outside the frozen packet.
