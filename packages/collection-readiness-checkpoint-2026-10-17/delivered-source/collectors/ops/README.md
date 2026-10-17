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

## Select and collect one publication

The catalog contains both the original jurisdictions and the expanded scope. Use `plan --all --cohort original` or `plan --all --cohort expansion` to narrow it. Publication IDs are stable and separate primary codes from secondary books and required publication dependencies. A target alone selects its primary publication; specify `--publication` for another book.

```sh
python3.12 collect.py plan --target 67 --publication 67-052d9663670b
python3.12 collect.py doctor --target 67 --publication 67-052d9663670b
python3.12 collect.py run --target 67 --publication 67-052d9663670b --out /absolute/path/collections/lincoln-charter
python3.12 collect.py verify --target 67 --publication 67-052d9663670b --out /absolute/path/collections/lincoln-charter
```

Use a fresh output path. The job record and progress logs live in a sibling `.collection-jobs` directory; the command prints their exact locations. Repeat the same `run` command after a recoverable interruption to resume the bound job. The launcher refuses an existing nonempty output without a matching job, a changed publication/configuration, or a changed collector/runtime. Follow the adapter's explicit migration procedure or start a fresh output when changing code. It does not silently re-label old evidence as a current live run.

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
