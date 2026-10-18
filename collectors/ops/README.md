# Technical-team launcher

The repository-root `collect.py` installs an isolated runtime, selects an inventoried publication, runs its complete-publication adapter and invokes that adapter's independent verifier. A runnable configuration is **not** proof of a complete publication. Read the output coverage and unresolved items before accepting a delivery.

## Set up a graphical collection host

The integrated environment has been tested on macOS with Python 3.12 and ordinary installed Google Chrome. The publisher gates use POSIX file locks. Linux with a graphical session is supported by the implementation but has not received the same live platform validation; native Windows is not qualified. Install Python 3.12 and Chrome before setup.

From the repository root:

```sh
python3.12 collect.py setup --python python3.12
python3.12 collect.py doctor --browser
python3.12 collect.py plan --all
```

Setup creates `.collection-runtime`, installs the exact direct dependencies in `requirements.txt`, checks dependency consistency, and launches ordinary headed Chrome against a local page with all network requests blocked. It does not contact publishers. The official pinned Python Playwright wheel supplies both its browser driver and Node runtime; system Node/npm are not needed. Browser binaries are not downloaded by this command. Actual Python, Node, package and Chrome versions are recorded in `runtime.json`. Setup can be repeated in its own directory after a failed installation; it refuses a nonempty unowned directory.

To choose another runtime directory, put the global option before the command:

```sh
python3.12 collect.py --runtime /absolute/path/collection-runtime setup --python python3.12
```

## List the full inventoried publication scope

`plan --all` lists the 130 primary publications. To list all 225 known publication entries, including secondary books and unqualified discoveries, use:

```sh
python3.12 collect.py plan --all-publications
python3.12 collect.py plan --all-publications --cohort original
python3.12 collect.py plan --target 82 --all-publications
```

Planning uses only Python's standard library and can run before setup. It sends no publisher requests and creates no runtime or collection output. Each entry retains its exact source, dependencies, qualification and access advisories; unsupported entries have no collection command. The catalog is a finite known scope, not proof that every separate publication has been discovered. `--all-publications` is plan-only and cannot be combined with `--all` or `--publication`; actual collection and verification remain explicit single-publication commands.

Setup checks the actual owned Python interpreter before installing dependencies, records its version, and doctor compares it with Python 3.12 and the setup receipt. An existing wrong-version interpreter is refused rather than silently replaced.

## Select and collect one publication

The catalog contains both the original jurisdictions and the expanded scope. Use `plan --all --cohort original` or `plan --all --cohort expansion` to narrow it. Publication IDs are stable and separate primary codes from secondary books and required publication dependencies. A target alone selects its primary publication; specify `--publication` for another book.

```sh
python3.12 collect.py plan --target 67 --publication 67-052d9663670b
python3.12 collect.py doctor --target 67 --publication 67-052d9663670b
python3.12 collect.py run --target 67 --publication 67-052d9663670b --out /absolute/path/collections/lincoln-charter
python3.12 collect.py verify --target 67 --publication 67-052d9663670b --out /absolute/path/collections/lincoln-charter
```

Use a fresh output path. The job record and progress logs live in a sibling `.collection-jobs` directory; the command prints their exact locations. Repeat the same `run` command after a recoverable interruption to resume the bound job. The launcher refuses an existing nonempty output without a matching job, a changed publication/configuration, or a changed collector/runtime. Follow the adapter's explicit migration procedure or start a fresh output when changing code. It does not silently re-label old evidence as a current live run.

Required PDF attachments must have explicit text and table qualifications for each document before the launcher accepts a full publication. The primary HTML and required binary acquisition may pass while this semantic gate remains incomplete. A successful PDF file-integrity check, page count, or parent-level aggregate flag cannot qualify an unassessed attachment. Read `acceptance.pdf_structure_dimensions` for the exact document URL and missing or failed dimension. Required non-PDF documents likewise need explicit document text and structure qualifications; inspect `acceptance.nonpdf_document_structure_dimensions`. A nonempty DOCX or archive is binary capture, not qualified legal content.

Named enCodePlus targets bind the exact selected entry and the full `collectors/encodeplus/targets.json` file. A configuration edit invalidates the prior job/proof binding even when the command line is unchanged. After a collector or configuration upgrade, use an explicit offline `verify` of retained evidence before accepting it under the new version; historical receipts are not automatically upgraded.

`verify` is offline and leaves source evidence unchanged. Its logs and attempt records live under the owned runtime's `verifications` directory. A previously successful job's repeated `run` performs verification only. Every attempt records source hashes before and after execution; changes during execution prevent a verified result.

## Interpret the result

- Exit `0` from `setup`/`doctor` confirms runtime/preflight checks only. Doctor sends no publisher requests and cannot prove a live collection will succeed.
- Exit `0` from `run` requires both the adapter's acquisition and selected-scope verifier to pass with no retained access stop or in-flight source change. It never claims jurisdiction completeness. Consult the family-specific coverage fields and required publication dependencies.
- Exit `2` means the selected scope is incomplete, verification failed, or source changed. Keep the source bytes, checkpoints and logs for review.
- Exit `3` indicates setup, job binding, access preflight or another operator action is required. CLI usage errors may also return `2`.

Current registry configurations include unqualified discoveries and publisher-blocked sources. These are deliberately not promoted by setup success, synthetic tests, a working sample or a successful representative city. The authoritative live readiness evidence remains publication-specific.

## Publisher stops and resuming

Publisher-specific shared gates remain authoritative. The launcher also mirrors observed refusals under `~/.local/state/local-jurisdiction-collection/observed-access-stops.json`, so a new output path or deletion of temporary files cannot silently erase an access stop. It never clears a publisher gate. Temporary cooldowns preserve their actual expiry; access refusals require the documented authorized recovery path. An unrelated external reference is not treated as a required document; an unresolved required external source can block that publication.

For an existing run, `doctor ... --out /absolute/path/output` inspects required external-source gates found in its coverage. A ready preflight does not authorize bypassing a challenge or ignoring a refusal. Consult each publisher runbook for authorized downloads and offline import procedures.

## Images and retained originals

All adapters are subject to [the image policy](../IMAGE-POLICY.md): no separate image download/extraction, and literal `[IMAGE]` in normalized HTML/text, preserving image-only source IDs and headings. Original publisher documents may inherently contain embedded images; those immutable files are source evidence. Required nonimage attachments remain separately reconciled. A placeholder is not a transcription of a diagram or scanned legal text.

The launcher does not upload data, alter the database, or send credentials. Acquisition outputs can be large; choose a disk with adequate space and preserve job metadata alongside the evidence.

## Flagstaff and King County original sources

The original-source adapters also use the common launcher and the existing official-source access gates:

```sh
python3.12 collect.py plan --target original-flagstaff-az
python3.12 collect.py run --target original-flagstaff-az --out /absolute/new/flagstaff
python3.12 collect.py verify --target original-flagstaff-az --out /absolute/new/flagstaff
python3.12 collect.py run --target original-king-county-wa --out /absolute/new/king-county
python3.12 collect.py verify --target original-king-county-wa --out /absolute/new/king-county
```

Flagstaff uses installed ordinary headed Chrome for the complete current code publication. King County requires both source-listed HTML and Word alternatives; collecting HTML alone cannot satisfy its aggregate. Both adapters replace images with `[IMAGE]`, block separate image acquisition, and preserve source text and table ownership. See the [original-source adapter runbook](../originals/README.md) for exact scope, standalone commands and retained-source replay.

Acceptance requires explicit text, required nonimage attachment, legal structure and source consistency results. An offline replay records its retained-source origin and zero publisher requests; it cannot establish a fresh live acquisition. Known King County date, reference and character-mapping conflicts remain incomplete. Separate Flagstaff Employee Handbook, King County Board of Health Code and external adopted model books require their own qualified collections.

## Explicit enCodePlus workflow actions

The active registry now dispatches six exact Overland Park native documents through `collectors.encodeplus.native_document`, using literal observed publisher URLs and pinned original file hashes/page counts. For example:

```sh
python3.12 collect.py run --target 82 --publication 82-4b983dc51ab6 --out /absolute/new/solid-waste
python3.12 collect.py verify --target 82 --publication 82-4b983dc51ab6 --out /absolute/new/solid-waste
```

A verified native file and all-page capture can return family exit0 while the shared launcher returns2 with `native_capture_verified:true` and `publication_accepted:false`. The native adapter deliberately leaves legal section segmentation, reading order, table semantics and edition acceptance qualified. This is not an image omission failure: images intentionally become `[IMAGE]`, and native originals may inherently contain images without separate image acquisition.

For HTML publications, request the visible publisher export on the **initial** job if it is needed:

```sh
python3.12 collect.py run --target 67 --out /absolute/new/lincoln --native-export
```

Ordinary repeated `run` reuses the exact original job options and performs offline verification after a successful capture. It does not retry a failed export. An explicit same-revision export retry on an existing matching HTML job originally created with native export is:

```sh
python3.12 collect.py run --target 67 --out /absolute/new/lincoln --native-export --retry-native-export
```

Explicit revision migration is supported only for existing exact enCodePlus HTML/native jobs:

```sh
python3.12 collect.py run --target 67 --out /absolute/new/lincoln --upgrade-code
```

The launcher preserves the prior job bytes/hash, source/configuration/runtime binding and original options. The family verifies old script snapshots and cached response hashes, records checkpoint history, reparses every retained source and acquires fresh closing witnesses. An HTML upgrade with original `native_export:true` deliberately revalidates that entire requested workflow, including a new export attempt. Same-revision `--retry-native-export` is the separate action when no code upgrade is needed. Failed export prefixes/results and prior checkpoint histories remain retained.

These actions do not adopt unowned outputs, change publication/configuration or enable native export on a job originally created without it. Start a fresh job when original options differ. Wrong-family actions, missing checkpoints, corrupt lineage and mismatched source/configuration are refused. Existing access stops and cooldowns still apply before any request; no flag clears or bypasses them. Family direct commands remain available for explicitly supported migrations of evidence not owned by the shared launcher.
