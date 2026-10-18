# Six Overland Park historical / incorporated native collection methods

This isolated package establishes runnable whole-file native methods for six exact publisher-observed source URLs. Each was acquired once with ordinary HTTP through the existing shared enCodePlus gate, then normalized across every physical page under network/image-stream/render/OCR guards. All six actual runs and all captured-source artifact replays returned 0. This is **native acquisition and complete page traversal**, not a claim of complete legal text/table/section/reading-order, adopted edition, dependency or jurisdiction coverage.

The source names and effective-period labels come from the retained publisher document library. They are not dates inferred from filenames. The Johnson County cover says incorporated by Ordinance ZRR-2691 and county adoption January 25, 2007; present territory/applicability remains unresolved. Oxford is genuinely image-only on every page: no PDFium characters, PDFMiner glyphs or extracted words, 400 image objects over 200 pages. `[IMAGE]` with object geometry is the intended output; no pixels were decoded, extracted, rendered or OCRed.

| Publication ID | Scope | Pages | Source words | `[IMAGE]` | Detected / agreeing cells | CID / engine failure pages |
|---|---|---:|---:|---:|---:|---:|
| 82-cfe47a936088 | STO, effective 5/01/2026–10/1/2026 catalog label | 224 | 53,410 | 33 | 2,399 / 2,133 | 0 |
| 82-7a796760f2f3 | Traffic Code, prior to 5/01/2026 | 129 | 71,816 | 0 | 0 / 0 | 128 |
| 82-301463c368c5 | UPOC, effective 9/1/2023–9/30/2024 catalog label | 166 | 30,626 | 2 | 2,489 / 2,227 | 0 |
| 82-02572b382672 | Criminal Code, prior to 9/1/2023 | 116 | 42,748 | 116 | 372 / 313 | 0 |
| 82-34ff7d4dbd3e | Johnson County Zoning & Subdivision Regulations | 276 | 125,748 | 276 | 22,109 / 18,560 | 267 |
| 82-6eedef9a53f0 | Oxford Township Zoning & Subdivision Regulations | 200 | 0 | 400 | 0 / 0 | 0; image-only |

Each remaining failed cell and source CID literal is retained in the canonical native IR; a source-method qualification does not convert those failures to passes. Native output is page JSONL plus a seven-column native CSV, not the final 16-column corpus exporter. Full legal section/list/table semantics remain unqualified. The STO cover is a 52nd/2025 publication with blank city-adoption blanks; its effective-period label alone does not fill those blanks or establish a present adopted edition.

## Exact source provenance and gate behavior

`publisher-documents-retained.html` and its original receipt establish all six anchors. Its actual base is `https://codes.opkansas.org/municipal-code/page.aspx?name=documents`, SHA256 `1f8ed710fde6460eac7c97366870886458df11cf191aef8801520e746cd94776`. Two absolute `online.encodeplus.com` URLs were actually printed; four relative `doclibrary.aspx` links resolve against the actual `codes.opkansas.org` base. These routes are not interchangeable aliases. All six native GETs returned 200 on their exact requested URL with no redirect or refusal. `native-discovery/inventory.json` retains source anchor labels, filename headers, actual URLs, native SHA, bytes and page pins.

`gate-before.json`, `gate-after-and-timing.json` and `gate-timing.stdout` preserve the existing host stops and exact request timing. Native URLs were each requested once. The observed minimum start after the prior response completion was 4.0016 seconds; existing refusal states were unchanged. No 401/403/429 occurred. The initial discovery driver's print-only TypeError happened after the first success was committed; its preserved attempt proves that the resumed driver skipped the already completed request. No retry, gate reset, challenge handling, alternate transport or image-resource fetch occurred.

The ten official links are separately and individually classified in `landing-classification.json`; exact bodies and redirect chains are under `landing-discovery`. All ten returned 200. Nine CivicPlus pages are static title/description/widget shells with server-side rendering disabled; the remaining route is an ArcGIS Dashboard shell. Their titles and official descriptions distinguish map, service-directory, application-process, adopted-plan and standards-resource roles. Comprehensive Plan, Vision Metcalf (official description: adopted 2008), engineering standards and building-code resources retain unresolved underlying legal-publication scope. None is blanket waived as optional, and none is falsely qualified as a complete publication.

## Ordinary standalone commands

Tested on macOS, Python 3.12.14 using the exact pinned requirements in `captured/collectors/encodeplus/requirements.txt`. No Codex process, browser session, imported cookie or API key is needed. Install those requirements in an ordinary virtual environment; `PY` below means that environment's Python. The source download remains a normal shared-gate operation and will refuse any existing access stop/cooldown; immutable native byte pins refuse future changed editions.

Read-only whole-packet verification is standard-library only and never parses a PDF:

```sh
python3 -B -S overland_historical_native_qualification.py --packet .
```

Read-only exact captured-source verification of one complete native result:

```sh
PY full-native/82-cfe47a936088/collector-source/collectors/encodeplus/retained_native.py --verify full-native/82-cfe47a936088
```

The same command applies to any of the six IDs. It reads original bytes/configuration/captured IR, verifies every page and exact output serialization, and explicitly reports `native_parser_reexecuted:false`. It uses its captured source rather than silently adopting newer code.

For a deliberately fresh retained-source extraction of an entire pinned file, choose a **new, absent** output directory:

```sh
PY captured/collectors/encodeplus/retained_native.py --config configs/native-82-cfe47a936088.json --input native-discovery/82-cfe47a936088.bin --receipt native-discovery/82-cfe47a936088.bin.receipt.json --out /absolute/fresh-output
```

The large Johnson/Oxford sources used the equivalent `extract_shared_source.py` wrapper, which creates a same-filesystem, byte-identical hardlink for `raw/source.pdf` rather than duplicating a 114 MB/21.5 MB original. It does not modify original bytes. Treat both link names as read-only. `shared-source-retention.json` records this operation and elapsed time. Ordinary captured-source verification is unchanged. Source file copies are permitted when moving to a different filesystem, but must preserve bytes/hashes.

`discover_native.py` is the exact gated source-download/metadata driver tested live. It validates the six actual retained anchors, records every attempted result, and skips completed/failed recorded IDs on subsequent invocations; it never retries a recorded refusal. `run_historical_four.py` is the actual full four-book extraction driver. Raw sources and receipts are provided, so neither command is needed for ordinary verification. Future native acquisitions use the six exact native configs via the existing native-document adapter; the evidence qualifies the method, not guaranteed access to future changed bytes or closing currency. Never delete a gate stop to make a run succeed.

## Captured source, current candidate and legacy compatibility

The six whole-native runs executed `retained_native.py` SHA256 `ca9dc0f6376609ccc3eae96d73e77d78338e544295d4a37c00d4fe42392b440f`: the corrected f7ef image guard with only its old UPOC-specific final scope sentence changed to generic wording. Every run archives the complete exact executed family source and configuration. Those runs are immutable historical executions.

`candidate/collectors/encodeplus/retained_native.py` SHA256 `97975a50b6081bfcac012b20c5061778bceedd420cd5ac489c71759331e17555` is a **separate promotion candidate**. Its sole change from production f7ef is one explicit limit-item conditional: exact old sentence for ID `82-8fbdce15716d`; generic wording for other IDs. Guard/parser/artifact-binding behavior is unchanged. `test_wrapper_compatibility.py` proves old published full172 coverage byte-equivalence and exact captured CLI replay, and new six complete-report equivalence, without native parsing. `legacy-compatibility` is a byte-identical read-only copy of the old published full172 proof, not a new acquisition or parse. Strict code-version checks remain in force; old/current source is never silently substituted.

## Tests and proposed root integration

The 23 test methods pass: 8 real source URL/hash/MIME/refusal/image-decoder guards; 6 captured-artifact/fresh-output/corruption faults; 3 legacy/new report compatibility checks; 6 pure six-method/alias/wrong-original/rehashed missing-page/unearned edition/source-base tests. Commands:

```sh
PY -B test_methods.py
PY -B test_artifact_guards.py
PY -B test_wrapper_compatibility.py
python3 -B -S test_qualification.py
PY -B verify_methods.py
python3 -B -S verify_oxford.py
```

The last two are read-only consumer checks. `verify_methods.py` verifies all 1,111 page IDs, original/config/receipt/source/runtime bindings, all six captured-source replays and every native CSV field against the complete canonical IR. `verify_oxford.py` independently checks every page/400 marker geometries against the exhaustive zero-text metadata proof. Neither executes native layout extraction.

`registry-overlay-PROPOSAL.json` is **not installed**. It proposes exactly six native configurations and a new typed proof kind `exact-six-observed-native-receipts-full-retained-normalization`. Root owns the published packet prefix substitution and explicit registry routing. `overland_historical_native_qualification.py` supplies `audit(here,catalog)->errors` and a portable packet verifier with exact source/config/page/hash pins, all-page CSV/IR checks, false-scope protections and exact image counts. Unknown IDs/aliases do not inherit qualification. Existing current-six, UPOC2024 and Clark routes must remain intact.

Suggested production whitelist: the one backward-compatible candidate `retained_native.py`, the six config files and the pure qualification helper; overlay/path/router changes require root review. No collector production, Git, database or old sealed package was modified here. `MANIFEST.json` seals this selected packet; whole native originals, exact receipts and full normalized records are included. Full semantics/currency/dependencies are explicitly unresolved, rather than omitted from the manifest.
