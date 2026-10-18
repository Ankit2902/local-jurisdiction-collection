# Offline HTML corpus readers

The composed writer registers `originals-flagstaff-html-v1`, `municode-html-publication-v1`, and `encodeplus-html-publication-v1`. It packages already verified, source-owned HTML IR. It never collects, requests publisher pages, renders HTML, opens image APIs, or invents sections from native pages. The raw evidence and source/config/version bindings remain alongside the 16-column corpus. Required PDF or other attachment bytes are not silently treated as a legal transcription.

Use the interpreter and installed dependencies appropriate for the explicitly chosen family verifier. The writer/readers use the Python standard library. The separate `verify_input.py` tool invokes the chosen family verifier and imports installed image libraries only to install refusal tripwires before any family code import. It records the Python executable hash, Python version, package versions, exact collector-file maps, and input maps before and after. This describes that verification environment; it does not infer equality with the acquisition environment or current production collector revision.

The examples below assume the reviewed composition has been copied to `collectors/corpus_package` in a checkout. Set the paths to actual retained inputs and exact selected collector source. An old source snapshot can verify an old corpus without being called the current production runtime. A changed collector that cannot reproduce the input must fail; do not alter the old checkpoint or invent a passing proof.

```sh
PY=.collection-runtime/venv/bin/python
CORPUS=collectors/corpus_package
```

## Municode HTML

Select one complete retained book. The tested historical book is Henderson Code of Ordinances, product 14896 / job 475955 / Supplement 59, under the retained `live-henderson-unified-v3` run. It contains 2,122 source-owned output records and 2,123 fullTree inventory nodes. Its landing record is an evidenced structural exclusion; the 24 `NewOrds` landing metadata entries are retained raw and reported as outside the codified-book transcription. No uncodified-ordinance or whole-jurisdiction closure is added.

```sh
"$PY" -B "$CORPUS/verify_input.py" \
  --reader municode-html-publication-v1 \
  --input /path/to/retained-henderson \
  --collector-root /path/to/exact-captured-source/collectors/municode \
  --publication-id 60-primary \
  --out /path/to/new-henderson-proof

"$PY" -B "$CORPUS/package.py" package \
  --reader municode-html-publication-v1 \
  --input /path/to/retained-henderson \
  --proof /path/to/new-henderson-proof/read-only-proof.json \
  --out /path/to/new-henderson-corpus
```

The reader follows fullTree child order, preserves owned parent bodies, and records every inventory disposition. Nonempty raw **or** normalized separate Notes/Footnotes currently refuse the whole export: their placement needs a qualified source schema. This applies to structural landing exclusions too. The tested Henderson source has no such populated fields. There is no partial silent omission.

## enCodePlus HTML

The tested historical input is the separately published Lincoln City Charter. All 188 inventory/body units are represented, including 14 structural containers and 174 owned bodies. Rows follow observed acquisition-block and TOC order, while original ID-sorted JSONL positions remain in provenance. Source body DOM parent/path evidence controls hierarchy; TOC declared depth does not.

```sh
"$PY" -B "$CORPUS/verify_input.py" \
  --reader encodeplus-html-publication-v1 \
  --input /path/to/retained-lincoln-charter \
  --collector-root /path/to/exact-captured-source/collectors/encodeplus \
  --publication-id 67-052d9663670b \
  --out /path/to/new-charter-proof

"$PY" -B "$CORPUS/package.py" package \
  --reader encodeplus-html-publication-v1 \
  --input /path/to/retained-lincoln-charter \
  --proof /path/to/new-charter-proof/read-only-proof.json \
  --out /path/to/new-charter-corpus
```

`--collector-root` may name the family folder containing `verify.py`, or the captured checkout containing `collectors/encodeplus/verify.py`. Native-document/page modes and unsupported body kinds refuse. Source-owned HTML notes, lists, table HTML, blanks, and exact `[IMAGE]` markers remain within the canonical body HTML. The reader does not substitute a detector table, plain convenience text, or diagnostics for the canonical body.

## Flagstaff HTML

Use the existing actual common read-only verification proof and its actual JSON family report. This does not require the MC/EP verification helper and does not change its historical exit status or acceptance gates.

```sh
"$PY" -B "$CORPUS/package.py" package \
  --reader originals-flagstaff-html-v1 \
  --input /path/to/verified-flagstaff-operational-root \
  --proof /path/to/actual-common-verify.json \
  --family-verification /path/to/actual-family-report.json \
  --out /path/to/new-flagstaff-corpus
```

An actual common family log may be supplied explicitly when its **complete bytes are the actual JSON family report**. A console transcript or non-JSON log refuses. The shared Flagstaff mapping documentation remains authoritative for its source hierarchy and exceptions. An older incomplete family receipt is not upgraded by packaging.

## Safe report selection and portable verification

`verify_input.py` emits `family_verification_path: "family-verification.json"` and the exact family-report hash in the proof. This permits omitting `--family-verification` in the MC/EP commands. The default resolver accepts only a nonempty normalized relative POSIX path beneath the proof folder. Absolute paths, `..`, backslashes, symlink components, missing files, non-JSON reports, and report-hash mismatches refuse. Historical absolute log paths are never followed implicitly. The explicit option remains supported.

`--publication-id` is a caller-assigned safe namespace slug (1–128 ASCII letters/digits/underscore/hyphen, starting with a letter or digit). The helper does **not** verify a catalog crosswalk. The proof states `registry_mapping_verified: false`. The source product/client/job or enCodePlus config/inventory remain independently bound and visible.

```sh
"$PY" -B "$CORPUS/package.py" verify --out /path/to/new-corpus
```

Portable package verification uses the copied proof/report/input/source bytes. It never reads the original absolute family-log or collector-tree locations. Fulltext JSON/CSV and TOC JSON/CSV carry all 16 string fields in exact contract order; CSVs have a UTF-8 BOM. Canonical HTML is preserved exactly, including lists/tables/notes/[IMAGE]. Known image elements, active image attributes/CSS and embedded pixel metadata refuse rather than being stripped by the writer. Raw original evidence remains original.

A successful serialization can return exit **2** because inherited publication/edition/jurisdiction/independent-review gates remain false or absent. In the tested Henderson and Charter packages, `package_verified` and `serialization_complete` are true while `downstream_ready` and `complete` remain false. Exit 0 from the verification adapter means the standard verifier returned and its inputs/source/environment stayed unchanged; the actual report and original false gates remain explicit. No new publication acceptance is added.

For the actual source-sensitive reader tests, point `CORPUS_READERS_FIXTURES` at the selected proof bundle containing `packages/{henderson,charter}/evidence/input` and `{henderson,charter}-proof` folders. The selected COPY-PLAN maps the final packages/proofs to exactly that portable layout. No hardcoded project path or source editing is needed.

```sh
CORPUS_READERS_FIXTURES=/path/to/selected/fixtures \
  "$PY" -B -m unittest test_html_readers -v
```

Run that command from the copied corpus-package source folder. The independent consumer auditor is a separate standard-library script; it imports no reader or writer implementation.
