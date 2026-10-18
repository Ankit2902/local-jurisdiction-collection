# Verified publication corpus exports

Package previously collected, source-verified HTML into the original 16-column fulltext/TOC JSON and CSV contract. The exporter preserves canonical legal HTML, tables, lists, notes and exact `[IMAGE]` placeholders. It also delivers the independent publisher node inventory, node dispositions, record provenance, inherited coverage, immutable source evidence and a self-contained read-only verifier.

Supported readers are explicit:

| Reader | Tested retained input | Scope |
|---|---|---|
| `originals-flagstaff-html-v1` | Flagstaff: 2,661 records | Selected City Code and Charter HTML |
| `municode-html-publication-v1` | Henderson: 2,122 records | Selected Municode HTML publication |
| `encodeplus-html-publication-v1` | Lincoln Charter: 188 records | Selected enCodePlus HTML publication |
| `ecode-html-retained-incomplete-v1` | Albany, NY: 3,006 records | Corrected retained HTML from the incomplete eCode360 run; 3,253 source dispositions, 256 tables and 440 image positions |
| `american-legal-native-html-publication-v1` | Cleveland: 6,141 records | Whole publisher-native HTML export, source TOC and one exact whole printable attachment; broader coverage qualifications retained |

These are tested serialization and fidelity results, including an explicitly incomplete acquired-HTML case. Each package preserves its original source, dependency, edition and jurisdiction qualifications. In the American Legal mode, **native means the publisher's native HTML export, not a native PDF or page-to-provision conversion**. Generic PDF/Word conversion and unlisted readers are unsupported. A new target must satisfy its reader's exact evidence and structure requirements; these five examples do not establish readiness for every jurisdiction.

## Runtime and preparation

Use Python 3.12 for the delivered workflow. The final composed readers and portable verifier were tested on CPython 3.12.14 on macOS. The earlier Flagstaff writer base was also tested on CPython 3.9.6; that is not a separate qualification of every final helper/reader on 3.9. The writer uses the Python standard library and POSIX `fcntl` locks, so native Windows execution is unqualified. Entry points suppress bytecode writes before local imports. No browser or Codex runtime is required for packaging.

The separate `verify_input.py` helper runs the selected Municode, enCodePlus or American Legal family's real read-only verifier. eCode360 uses the dedicated `verify_ecode_input.py` helper described below. Use the common launcher's installed `.collection-runtime/venv/bin/python` for that step. A family-only installation is not sufficient for every helper: the shared helper also imports the pinned PDF/image guard libraries, and the eCode helper requires Pillow for its image guard. To use another Python 3.12 environment, install the explicitly pinned verification requirements before running a helper:

```sh
/path/to/collector-python -m pip install -r collectors/corpus_package/requirements-verification.txt
```

This requirements file reuses the tested common runtime pins; it does not install Codex or download a browser. It binds the input files, explicitly selected collector source, Python executable, installed packages and verifier report, and forbids network and image operations. The writer itself does not import collector dependencies or rerun acquisition.

Run the following from the repository root, replacing absolute example paths with your own. For Municode, create a fresh proof directory:

```sh
/path/to/collector-python -B collectors/corpus_package/verify_input.py \
  --reader municode-html-publication-v1 \
  --input /data/henderson-run \
  --collector-root /path/to/local-jurisdiction-collection \
  --publication-id henderson-code \
  --out /data/henderson-proof

python3 -B collectors/corpus_package/package.py package \
  --reader municode-html-publication-v1 \
  --input /data/henderson-run \
  --proof /data/henderson-proof/read-only-proof.json \
  --out /data/henderson-corpus
```

For enCodePlus, use `encodeplus-html-publication-v1` with its own collected publication and fresh proof/output directories. The `--publication-id` is a caller-assigned safe corpus namespace. It is not a verified registry crosswalk; proofs explicitly retain `registry_mapping_verified:false`. The source product/client/job/configuration remains independently bound.

For Flagstaff, the standalone helper runs the selected common launcher's real read-only verifier and produces a portable proof with its exact family JSON report. Use the existing owned collection runtime and a fresh proof directory:

```sh
/path/to/collector-python -B collectors/corpus_package/verify_flagstaff_input.py \
  --input /data/flagstaff-run \
  --collector-root /path/to/local-jurisdiction-collection \
  --runtime /path/to/local-jurisdiction-collection/.collection-runtime \
  --out /data/flagstaff-proof

python3 -B collectors/corpus_package/package.py package \
  --reader originals-flagstaff-html-v1 \
  --input /data/flagstaff-run \
  --proof /data/flagstaff-proof/read-only-proof.json \
  --out /data/flagstaff-corpus
```

The helper independently checks the input, collector/configuration and runtime bindings, matches the saved common receipt to the family log, and preserves the original receipt and report bytes. Its derivative proof adds only the relative report path, hash and lineage. Exit 0 means the proof was produced; inspect `common_exit` and acceptance before claiming source completeness. It never requests acquisition or changes source acceptance.

For retained incomplete eCode360 input, select the **exact retained executed-source directory** whose top-level Python files match `checkpoint.json` → `code_fingerprint`. For the supported retained-run layout, this is `/data/albany-retained-run/executed-source`. Unlike the other helper, eCode's `--collector-root` is not the repository root and does not auto-resolve `collectors/ecode`. It must directly contain the exact `engine.py` and matching top-level `.py` file set. Do not substitute the current engine for a historical executed revision.

```sh
/path/to/collector-python -B collectors/corpus_package/verify_ecode_input.py \
  --input /data/albany-retained-run \
  --collector-root /data/albany-retained-run/executed-source \
  --publication-id albany-ecode-acquired-html \
  --out /data/albany-retained-proof

python3 -B collectors/corpus_package/package.py package \
  --reader ecode-html-retained-incomplete-v1 \
  --input /data/albany-retained-run \
  --proof /data/albany-retained-proof/read-only-proof.json \
  --out /data/albany-retained-corpus
```

`verify_ecode_input.py` has **no `--reader` argument**. It calls the explicitly selected standard `engine.verify` and requires positive raw reconstruction with unchanged input/source/runtime. Its exit 0 means that the proof was produced, even when the standard family CLI and resulting corpus package correctly return exit 2 for incomplete publication coverage. The corrected Albany input retains its 403/access stop, missing closing inventory and four unqualified required PDFs. A raw-source review found that the historical eCode normalizer omitted nested definition/list bodies in 860 records. The current parser preserves those bodies and has an independent all-source comparison covering 3,006 records, 256 tables/8,549 cells, notes, links and all 440 image positions. Three uniquely owned definition self-links are narrowly classified as inline references; genuine document links remain required. Twenty-one restored statutory-link occurrences remain unresolved. Use the [corrected V3 corpus and exact source proof](../../packages/collection-source-recovery-2026-10-18/ecode/README.md). Earlier sealed packages reproduce the old IR and must not be treated as full raw-source text. Packaging does not retry acquisition or promote attachment, edition or publication completeness. Its emitted row order follows literal publisher `data-position`; original rich-IR ordinals and every source disposition remain in provenance. This mode refuses bounded/subtree inputs and complete or other eCode modes that have not been separately qualified.

For Cleveland's American Legal publisher-native **HTML** export, use the shared helper with its explicit reader name. Here `--collector-root` may be the repository root, as shown, or the selected `collectors/american-legal` directory containing `verify.py`. Use the Python environment required by that exact source revision; the helper records the selected code and installed runtime rather than inferring equivalence to the acquisition runtime.

```sh
/path/to/collector-python -B collectors/corpus_package/verify_input.py \
  --reader american-legal-native-html-publication-v1 \
  --input /data/cleveland-native-html-run \
  --collector-root /path/to/local-jurisdiction-collection \
  --publication-id cleveland-native-html \
  --out /data/cleveland-native-html-proof

python3 -B collectors/corpus_package/package.py package \
  --reader american-legal-native-html-publication-v1 \
  --input /data/cleveland-native-html-run \
  --proof /data/cleveland-native-html-proof/read-only-proof.json \
  --out /data/cleveland-native-html-corpus
```

The American Legal reader requires an acquired, unbounded `strategy: native` run with `identity.is_pdf: false`, unchanged opening/closing publication identity, the complete independent source TOC and exact native block ownership. It preserves source HTML, tables, notes, passthrough containers and literal locators; conflicting scalar hierarchy values remain explicit rather than guessed. PDF/page and limited acquisitions are refused. Required-document dispositions and inherited completeness stay separate from HTML fidelity: the tested Cleveland corpus now includes the exact whole printable attachment linked by §348.02, inserted immediately after its source owner. Its nine-row/two-column table, ordinance note and nine `[IMAGE]` positions are source-bound. The attachment has a blank section number and does not turn a physical page into an inferred legal section. Other PDFs still require their own independently qualified source profile; generic page diagnostics are not canonical legal records. All original 6,140 HTML row field values and producer coverage remain unchanged. Source-proven no-glyph image-only attachment exclusions do not qualify an attachment with available text, and this reader does not invent PDF legal segmentation or infer current legal edition, dependency closure or jurisdiction readiness. Helpers produce proof only; inspect the saved family report and inherited coverage.

The `--publication-id` in the Municode/enCodePlus/American Legal shared helper and the dedicated eCode helper is a safe caller-assigned corpus namespace. It does not create a registry crosswalk or change the source publication identity.

An explicit `--family-verification` accepts the actual JSON family verifier output. Omitting it is allowed only when the proof supplies a safe relative `family_verification_path` and the matching report hash. Historical absolute log paths are never followed implicitly. Do not manually change a frozen proof to claim that it originally contained a relative path.

## Resume, verification and exit status

Repeat the same packaging command with `--resume` after an owned interruption. Source, proof, reader, publication ID and code bindings must match exactly. A fresh output must be empty and disjoint from the input. Corrupt, foreign or unexpected files cause refusal. Writes are atomic; completed resume is read-only.

After copying the finished package elsewhere, verify it with the code embedded in that package:

```sh
python3 -B /copied/henderson-corpus/packager-source/package.py verify \
  --out /copied/henderson-corpus
```

The verifier checks the complete file inventory, reconstructs the source-bound projection, and compares every JSON/CSV field, row order and derived TOC value. It does not follow historical source paths or modify the package.

- Exit `0`: package verified and every inherited required readiness gate is true.
- Exit `2`: package verified, but required source/readiness qualifications remain incomplete. Inspect `package_verified`, `complete`, `validation-report.json` and `inherited-coverage.json` together.
- Exit `1`: invalid input, unsupported mapping, corrupt evidence or verification failure.
- Exit `75`: test-only injected packaging interruption after a durable artifact boundary.

The input-verification helper's exit `0` means its read-only proof was produced successfully. It does not add publication acceptance or waive the family report's unresolved conditions.

## Text, hierarchy and images

Each corpus row has exactly these ordered string fields: `jurisdiction`, `code_name`, `division`, `title`, `subtitle`, `chapter`, `subchapter`, `article`, `part`, `subpart`, `section_number`, `section_name`, `citation`, `full_text`, `source_url`, `scrape_date`. JSON contains `metadata` and `provisions`; CSV uses a UTF-8 BOM. Derived TOC rows change only `full_text` to empty and do not substitute for the independent source inventory.

`full_text` is the verified canonical HTML, including source tables/spans, enumeration, notes and image placeholders. Diagnostic or superseded detector text is not appended to it. Reader-specific source witnesses establish hierarchy and displayed locators; unsupported or ambiguous roles remain blank with provenance. Records retain their source identity and ownership. Acquisition timestamps are not legal effective dates.

All images remain the exact literal **`[IMAGE]`**. No separate image assets are fetched, copied, decoded, extracted, rendered or OCRed. Active image markup, CSS image locators and image payloads in normalized text or recursive metadata cause refusal. Declared image context is recognized even for opaque URLs, nonimage data-URI labels and whitespace around image MIME values. Ordinary PDF links and inert omission provenance remain valid.

Original publisher HTML/PDF/DOCX/archive evidence may inherently contain embedded images and is copied unchanged for provenance. Intrinsic embedded images in those immutable originals are not separate image assets and are not removed or decoded. This provenance copy does not authorize separate image fetching, member extraction, pixel decoding, rendering or OCR; normalized legal output still uses only the exact `[IMAGE]` placeholder for image content. The writer requires already-normalized image-free canonical input; it refuses unsafe input rather than silently modifying verified legal text. See [the collection image policy](../IMAGE-POLICY.md).

Source/readiness qualifications survive packaging. Structural landing exclusions must be source-proven and cannot silently discard legal notes. Unresolved native documents, required references, source changes or unqualified publication boundaries remain explicit. Unsupported populated separate note structures fail closed.

## Evidence and tests

The [startup and corpus checkpoint](../../packages/collection-startup-and-corpus-2026-10-18/README.md) retains exact collector revisions, actual full-publication exports, independent reviews and relocation tests. Historical evidence remains immutable; use the packet's source hashes to distinguish revisions.

Portable writer regression tests can be run from the repository root:

```sh
python3 -B -m unittest discover -s collectors/corpus_package -p test_package.py -v
```

Actual-source reader proofs and family raw-replay reports are retained separately in the checkpoint. The small shipped fixtures support bounded regression cases; they do not replace the complete publication evidence. See also the [output contract](OUTPUT-CONTRACT.reference.md).

The final checkpoint also executes this exact writer directly on the newly completed live Flagstaff collection and its current accepted common/family proofs. That current export preserves all 558 input files, 2,661 rows and 882 image placeholders. Primary-publication coverage stays accepted; broader jurisdiction, dependency and final-review qualifications stay false. The historical fidelity-base proof is retained separately.

## Selected-publication readiness

`selected_publication_ready` appears in `validation-report.json` and `run-manifest.json`, with a named gate/binding report. Schema `flagstaff-selected-publication-readiness-evidence-1` is qualified only for `original-flagstaff-az-primary`; other readers remain false unless they have a separately qualified evidence contract. It uses the actual bound standard common acceptance and family raw replay plus source structure, coverage, identity and dependency evidence. Zero missing hyperlinks alone cannot qualify it. It does not infer human/final legal review, all incorporated legal layers, edition, native capture, or jurisdiction discovery.

The strict `complete`, `downstream_ready`, status and CLI exits are unchanged: a qualified selected Flagstaff primary can have this flag true and still return exit 2 because jurisdiction closure and final review remain false. Original coverage and all 14 data artifacts other than the augmented validation report are unchanged. Fresh-output, resume, source, runtime, hash and image guards remain required. Run `python3 -B -m unittest -q test_package test_readiness` from `collectors/corpus_package` for the 36-test serialization and readiness suite. The [source-scope audit and actual comparisons](../../packages/collection-readers-and-structure-2026-10-18/corpus/selected-readiness/AUDIT.md) distinguish the current accepted primary from historical incomplete inputs. Synthetic fixtures qualify algorithm and refusal behavior only.
