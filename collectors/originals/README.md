# Original publication collectors

The current [startup and corpus checkpoint](../../packages/collection-startup-and-corpus-2026-10-18/README.md) includes an actual ordinary headed Chrome run using the promoted scripts. A real interruption after one initial native response, before the first source checkpoint or operative body, resumed through the same common command and completed successfully. A separate current common read-only verification also exited 0 and accepted the primary City Code including Charter: 361 documents, 2,661 records, 377 tables and 882 exact `[IMAGE]` placeholders. All 455 retained raw/native bodies and nine normalized streams passed image auditing. Whole-jurisdiction and external adopted-law closure remain false; Employee Handbook is outside this selected publication. Literal broken source fragments remain recorded, with only their exact source-bound target coverage qualified. The preceding V7/V9 history below retains its original revision scope.

The [native and live checkpoint](../../packages/collection-native-and-live-validation-2026-10-18/README.md) adds the completed actual Flagstaff V7 interruption/resume evidence and reviewed V9 source-target qualification. All 361 documents, 2,661 records, 377 tables and 882 `[IMAGE]` placeholders remain source-bound. Three literal broken fragments stay explicit; only their exact retained target coverage qualifies. The copied current common verifier accepted a fresh V9 retained-source replay, not a new V9 live acquisition or whole-jurisdiction corpus. Use an explicit new `offline.py replay` output to upgrade old evidence. The current early-inventory recovery implementation adds a durable initialization marker and preserves interrupted native inventory generations. Its exact regression and live evidence is recorded in the [startup and corpus checkpoint](../../packages/collection-startup-and-corpus-2026-10-18/README.md).

This family supplies standalone full-publication methods for the Flagstaff City Code including Charter, and all35source-listed King County Code HTML/Word documents including Charter and editorial material. The publisher remains `official`; registry dispatch uses `adapter_family: originals`. These exact source profiles are deliberately finite. An arbitrary URL or different publication cannot be substituted through configuration.

The primary entry point is `cli.py`. It supports live `collect`, explicit offline `replay`, source-format `normalize`, read-only `verify`, and network-free `doctor`. Whole requested publications are the default; there is no hidden sample limit. Separate Flagstaff Employee Handbook, historical editions, King Board of Health Code and external adopted model books are outside these primary boundaries. `whole_jurisdiction_complete` and external adopted dependency closure remain false.

## Setup and live collection

Use Python3.12+ on macOS/Linux. The runtime uses POSIX `fcntl` locks; native Windows is not qualified. Install the pinned requirements in your own environment. The tested environment is Python3.12.14, beautifulsoup4 4.15.0, Playwright1.64.0, pypdf6.21.1 and installed ordinary Chrome155.0.8059.84 on macOS26.6.2 arm64. No Node, Codex installation, Word, LibreOffice, OCR, image library or downloaded Playwright browser is required. King HTTP/Word acquisition does not launch Chrome; Flagstaff launches installed ordinary headed Chrome using `channel=chrome` with its own disposable context.

From the repository root:

```sh
python3 -m venv /your/runtime/originals
/your/runtime/originals/bin/python -m pip install -r collectors/originals/requirements.txt
export PYTHON=/your/runtime/originals/bin/python

"$PYTHON" -B collectors/originals/cli.py doctor --config collectors/originals/configs/flagstaff.json
"$PYTHON" -B collectors/originals/cli.py collect --config collectors/originals/configs/flagstaff.json --out /your/evidence/flagstaff
"$PYTHON" -B collectors/originals/cli.py collect --config collectors/originals/configs/king-county.json --out /your/evidence/king-county

# Exact same target, config and code; durable completed stages are reused.
"$PYTHON" -B collectors/originals/cli.py collect --config collectors/originals/configs/flagstaff.json --out /your/evidence/flagstaff --resume

# Read-only, network-free full source replay and aggregate coverage recomputation.
"$PYTHON" -B collectors/originals/cli.py verify --config collectors/originals/configs/flagstaff.json --out /your/evidence/flagstaff
"$PYTHON" -B collectors/originals/cli.py verify --config collectors/originals/configs/king-county.json --out /your/evidence/king-county
```

Exit0 means the requested operation passed all implemented publication gates. Exit2 is a sound incomplete source/coverage outcome (or an operationally blocked doctor); exit1 is configuration/runtime/refusal/verifier failure. Doctor readiness is permission to attempt the configured method, not a complete legal publication claim. Preserve the structured reason in every nonzero result.

A full King run acquires both actual source-listed HTML and native Word alternatives; HTML alone cannot satisfy the required format aggregate. Known current King source gaps intentionally return incomplete: nine literal per-document index/body Updated mismatches, a required incorporated legacy MRSC URL returning404, broken internal source targets and Disposition private-font character semantics. No credential requirement has been observed, and no credential is accepted by this collector. Do not silently choose a preferred date, substitute a newer MRSC document, map an unknown private glyph, or relabel transport success as complete.

## Explicit retained-source replay

The operational offline import uses the same normalizers and the same collection-root verifier. Pass whole hash-verified source captures with their original checkpoint/receipts. It copies them into a NEW directory, preserves original acquisition provenance, reruns all normalization and closure gates, then verifies the resulting operational root. A loose HTML/DOCX/PDF file or an excerpt is insufficient. This is explicitly historical acquisition plus current-code normalization; it makes zero publisher requests and never becomes a fresh full live execution claim.

```sh
"$PYTHON" -B collectors/originals/cli.py replay --config collectors/originals/configs/flagstaff.json \
  --source /retained/flagstaff-full-source --out /your/evidence/flagstaff-replayed

"$PYTHON" -B collectors/originals/cli.py replay --config collectors/originals/configs/king-county.json \
  --source /retained/king-html --native-source /retained/king-word --out /your/evidence/king-replayed

# Resume the same explicit replay after a durable boundary, never as live collection.
"$PYTHON" -B collectors/originals/cli.py replay --config collectors/originals/configs/king-county.json \
  --source /retained/king-html --native-source /retained/king-word --out /your/evidence/king-replayed --resume
```

The optional `offline.py` wrapper runs the real `cli.py replay` or `verify` with socket, urllib, shared-transport and browser-start tripwires. It is a verification guard, with no alternate normalization/acceptance implementation. Replace `cli.py` with `offline.py` in an offline replay/verify command. The recorded full operational proofs use that wrapper and actual retained source captures.

A completed normalization is reverified on resume. An interrupted normalization staging directory remains immutable; a new numbered generation is parsed and atomically promoted only after terminal normalization. An interrupted source-copy staging directory requires operator review and a new output, rather than silently accepting a partial copy. Source/config/code drift, retained acquisition failures and access stops do not automatically resume. Replaying historical evidence cannot resume live acquisition. Use a new explicit replay to qualify a new code revision; ordinary production caches are never silently upgraded.

## Source-format normalization and historical proof inspection

Use format-specific commands when an operational collection root is unnecessary:

```sh
"$PYTHON" -B collectors/originals/cli.py normalize --config collectors/originals/configs/flagstaff.json --format html \
  --source /retained/flagstaff-full-source --out /your/evidence/flagstaff-normalized
"$PYTHON" -B collectors/originals/cli.py normalize --config collectors/originals/configs/king-county.json --format word \
  --source /retained/king-word --out /your/evidence/king-word-normalized
"$PYTHON" -B collectors/originals/cli.py verify --config collectors/originals/configs/king-county.json --format word \
  --source /retained/king-word --normalized /your/evidence/king-word-normalized
```

Explicit source-format verification supports exact old stage proofs with their current equal parser fingerprints. It does not manufacture a config-bound operational root or replace the required King format aggregate. The full-root verify refuses foreign/unbound config/source/revision metadata, reconstructs each format from raw evidence in temporary scratch, compares deterministic outputs and recomputes the strong coverage fields rather than trusting stored booleans. Input evidence is unchanged.

## Output and binding contract

`checkpoint.json` has schema `originals-collection-checkpoint-1`, `publisher: official`, `adapter_family: originals`, full typed `config`, repeated `source_identity`, exact runtime fingerprints, acquisition mode, stage, origin, errors and complete flag. `collection-start.json` binds the same full config/target and exact code. `coverage.json` exposes:

- `publication_text_complete`, including qualified source characters;
- `publication_bodies_acquired_and_owned`, separate from character/edition qualification;
- `attachments_complete`, including required nonimage references;
- `legal_structure_qualified`, for the implemented ownership, heading and table gates;
- `source_consistency_complete`, including opening/closing inventory, current-source update labels and source navigation;
- `publication_accepted` and `complete`, requiring every required format and all implemented primary gates;
- `whole_jurisdiction_complete: false` and `external_adopted_legal_dependency_closure_complete: false`;
- per-format exact summaries, source scope, errors and independent review status.

Independent final review is tracked separately. A structural gate or own replay is not an inherited independent audit. The retained Flagstaff source-DOM and King DOM/XML reports bind their exact source/record/model scope; integration summaries record which final deltas were actually reviewed.

Flagstaff uses `source/` and `normalized/`; King uses `html-source/`, `native-source/`, `normalized/` and `native-normalized/`. HTML legal output is `records.jsonl` and `records.csv`; native Word legal output is `records.jsonl`, including foot/endnotes and header/footer source parts. `document-audits.json`, `dependencies.json`, `relationships.json` and source inventory files retain reconciliation and reference metadata. Nonimage attachments are never silently optional. Character/source-empty profiles are finite raw/XML/hash-bound dispositions; changed source bytes invalidate them.

The material runtime JSON inputs are `configs.json` (finite internal reference rules), `source_dispositions.json` (source-empty own-body disposition), `source_character_dispositions.json` (17exact source-bound Unicode recoveries), and the selected `configs/*.json` typed publication configuration. Copy all top-level Python modules and these JSON/config files plus `requirements.txt` to run independently; no old output-package import or absolute project-code dependency exists.

## Access and images

Both profiles share `/tmp/compliSolv-official-publication-gate`, or `OFFICIAL_GATE_DIR`, with the official family. Requests and redirects are serially gated at3.5seconds per host.403/429, Retry-After and challenges persist a stop. Never reset stops, change routes to evade them, import cookies, disable TLS, rotate identities or interact with challenges. Existing stopped eCode360/municipal.codes/Municode/Spokane-static/Louisiana-health routes are forbidden. Cleanup closes only the run's own context/browser.

No separate images are requested/downloaded/extracted/rendered/OCRed. Browser image/font/media resources are blocked; detected image HTTP bodies are not read. Original native DOCX/PDF files may intrinsically contain images. Normalization emits exact `[IMAGE]` positions, preserves IDs/captions/reference hashes and removes active image markup/payloads recursively. Word image/OLE picture members are never opened. Known image-bearing metadata attributes use whole-value hash boundaries; quoted inline legal image data preserves surrounding prose, and ambiguous unquoted image data fails closed. Known image contexts are classified before inline data handling, even when their claimed MIME is a nonimage type. Encoded image-reference metadata is replaced with [IMAGE] plus source hashes without decoding. Unsupported nonimage inline documents also are not decoded; they remain required, unqualified dependencies and block attachment completeness. Ancillary cached source dates are not promoted into currency claims.

## Network-free qualification

```sh
"$PYTHON" -B -m unittest discover -s collectors/originals/tests -v
```

The historical operational revision preserved 70 inherited tests and passed 99 tests at that revision; later recovery and source-navigation tests are recorded separately below and in the current checkpoint. New operational tests cover strict typed identity/formats, actual CLI method wiring, failed-source false coverage, zero-network full replay, required Word participation, exact config/revision resume, interrupted generation preservation, corrupt raw sources and independently recomputed coverage. Compact actual-source table and Word XML fixtures preserve source hashes, fee cell/span semantics and unresolved symbol positions. Provenance mode cannot be relabelled live, and inventory-only Chrome disables downloads and registers no saver. Synthetic inventories remain explicitly synthetic and are not live proof. The family validation summary separately records actual full retained-source operational proofs, exact source revisions and remaining upstream limits. At that historical freeze, the final-wrapper fresh live Flagstaff run was pending. Subsequent actual acquisition and interruption/resume receipts are retained in the checkpoints linked above, outside the bound source tree. Retained-source replays never count as that fresh acquisition.

## Reviewed legal structure and recovery revision — October 18, 2026

The current revision preserves 800 typed source notes, 5,254 links and 11 source list wrappers in the retained full Flagstaff primary publication. All 2,661 records retain their text, table cells and atomic block ownership. Nested same-owner groups emit the outermost sanitized source wrapper once; each nested group retains its association. Ambiguous containment or ownership fails validation. Three publisher links point to absent source targets, so source consistency and publication acceptance remain false. No target is invented.

King County applicability was checked against all 35 HTML and 35 native Word documents. The HTML changes add 16 source note metadata entries across eight owners; all other fields in 5,844 HTML records are unchanged. All 57,195 Word records are byte-identical. Existing source, reference and font gaps remain unresolved.

The exact candidate passed 108 independently rerun regressions. Two real SIGINT/CLI-resume process tests used recorded retained-source transport. They prove process recovery for their tested boundaries, not live Chrome or publisher recovery. Interrupted normalization keeps its old attempt immutable and writes a fresh attempt. That historical revision refused resume during the initial native inventory before its first source checkpoint. The current initialization module addresses this boundary with durable ownership, preserved attempts, exact revision/source binding and retained access-stop checks. See the startup checkpoint for the actual tested boundary and current live result; the earlier retained-source process tests alone do not establish live recovery.

Only macOS 26.6.2 arm64 with Python 3.12.14 was tested. The image rule is unchanged: no separate image fetching, member reads, decoding, rendering or OCR; normalized images are exact `[IMAGE]`, with captions, legal text and source identity preserved. Native originals remain immutable.

See the [frozen evidence and independent reviews](../../packages/collection-structure-recovery-2026-10-18/BUNDLE-MANIFEST.json). Run the nine focused cases with `python -B collectors/qa/run_originals_legal_structure.py --source collectors/originals --receipt /fresh/path/tests.json` from the repository root. Historical candidate status text in that frozen packet describes its original review stage; this runbook and current validation summary record promotion.
