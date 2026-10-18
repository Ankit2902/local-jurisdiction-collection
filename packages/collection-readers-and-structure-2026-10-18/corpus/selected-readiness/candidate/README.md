# Verified publication corpus exports

Package a previously collected and verified HTML publication into the original 16-column fulltext/TOC JSON and CSV contract. The exporter preserves canonical legal HTML, tables, lists, notes and exact `[IMAGE]` placeholders. It also delivers the independent publisher node inventory, node dispositions, record provenance, inherited coverage, immutable source evidence and a self-contained read-only verifier.

Supported readers are explicit:

| Reader | Tested whole-publication input | Scope |
|---|---|---|
| `originals-flagstaff-html-v1` | Flagstaff: 2,661 records | Selected City Code and Charter HTML |
| `municode-html-publication-v1` | Henderson: 2,122 records | Selected Municode HTML publication |
| `encodeplus-html-publication-v1` | Lincoln Charter: 188 records | Selected enCodePlus HTML publication |

These are tested serialization and fidelity results. Each package preserves its original source, dependency, edition and jurisdiction qualifications. Native PDF/Word page-to-provision conversion and other publisher readers are not supported. A new target must satisfy its reader's exact evidence and structure requirements; these three examples do not establish readiness for every jurisdiction.

## Runtime and preparation

Use Python 3.12 for the delivered workflow. The final composed readers and portable verifier were tested on CPython 3.12.14 on macOS. The earlier Flagstaff writer base was also tested on CPython 3.9.6; that is not a separate qualification of every final helper/reader on 3.9. The writer uses the Python standard library and POSIX `fcntl` locks, so native Windows execution is unqualified. Entry points suppress bytecode writes before local imports. No browser or Codex runtime is required for packaging.

The separate `verify_input.py` helper runs the selected Municode or enCodePlus family's real read-only verifier. Use the collector's installed Python environment and dependencies for that step. It binds the input files, explicitly selected collector source, Python executable, installed packages and verifier report, and forbids network and image operations. The writer itself does not import collector dependencies or rerun acquisition.

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

For Flagstaff, use the current common launcher's read-only verification receipt and its exact family JSON report:

```sh
python3 -B collectors/corpus_package/package.py package \
  --reader originals-flagstaff-html-v1 \
  --input /data/flagstaff-run \
  --proof /data/flagstaff-readonly.json \
  --family-verification /data/flagstaff-family-verification.json \
  --out /data/flagstaff-corpus
```

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

Original publisher HTML/PDF/DOCX/archive evidence may inherently contain embedded images and is copied unchanged for provenance. That does not authorize separate image extraction. The writer requires already-normalized image-free canonical input; it refuses unsafe input rather than silently modifying verified legal text. See [the collection image policy](../IMAGE-POLICY.md).

Source/readiness qualifications survive packaging. Structural landing exclusions must be source-proven and cannot silently discard legal notes. Unresolved native documents, required references, source changes or unqualified publication boundaries remain explicit. Unsupported populated separate note structures fail closed.

## Evidence and tests

The [startup and corpus checkpoint](../../packages/collection-startup-and-corpus-2026-10-18/README.md) retains exact collector revisions, actual full-publication exports, independent reviews and relocation tests. Historical evidence remains immutable; use the packet's source hashes to distinguish revisions.

Portable writer regression tests can be run from the repository root:

```sh
python3 -B -m unittest discover -s collectors/corpus_package -p test_package.py -v
```

Actual-source reader proofs and family raw-replay reports are retained separately in the checkpoint. The small shipped fixtures support bounded regression cases; they do not replace the complete publication evidence. See also the [output contract](OUTPUT-CONTRACT.reference.md).

The final checkpoint also executes this exact writer directly on the newly completed live Flagstaff collection and its current accepted common/family proofs. That current export preserves all 558 input files, 2,661 rows and 882 image placeholders. Primary-publication coverage stays accepted; broader jurisdiction, dependency and final-review qualifications stay false. The historical fidelity-base proof is retained separately.

## Isolated selected-publication readiness addition

This candidate adds `selected_publication_ready` to `validation-report.json` and `run-manifest.json`, with a named gate/binding report. Schema `flagstaff-selected-publication-readiness-evidence-1` is qualified only for `original-flagstaff-az-primary`; Municode/enCodePlus readers have no readiness-evidence adapter and remain false. It uses the actual bound standard common acceptance and family raw replay plus source structure, coverage, identity and dependency evidence. Zero missing hyperlinks alone cannot qualify it. It does not infer human/final legal review, all incorporated legal layers, edition, native capture, or jurisdiction discovery.

The existing strict `complete`, `downstream_ready`, status and CLI exits are unchanged: a sound selected Flagstaff primary can have this new flag true and still return exit 2 because jurisdiction-wide closure/final review remain false. Original coverage and all 14 data artifacts other than the augmented validation report are unchanged. Existing fresh-output/resume/source/runtime/hash/image guards remain required. The writer now ships nine stdlib-only modules, including `readiness.py`. Run `python3 -B -m unittest -q test_package test_readiness` in this candidate for the 36-test source-sensitive/fault suite. See the adjacent `AUDIT.md`, `actual-comparison.json` and `compare_actual.py` for the current/historical proof comparison. The synthetic fixture qualifies only algorithm/refusal behavior, never an actual collection.
