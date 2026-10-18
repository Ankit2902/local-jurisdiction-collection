The existing `plan --all` command lists one primary publication per target. To discover every entry in the shipped publication catalog, including secondaries and unqualified discoveries, use:

```sh
python3.12 collect.py plan --all-publications
python3.12 collect.py plan --all-publications --cohort original
python3.12 collect.py plan --target 82 --all-publications
```

Planning uses only the Python standard library. It can run from a fresh checkout before setup and from another working directory when `collect.py` is given by path. It sends no publisher requests, creates no collection output, and requires no owned runtime, Chrome, Node, Codex or native PDF/image library. The selected catalog is still finite; this does not assert that all separate government publications have been discovered.

`--all-publications` is plan-only. It cannot be combined with `--all` or an explicit `--publication`. A `--target` restricts the listing to that government's inventoried entries. `targets` counts distinct governments; `publication_count` counts the plans. Each entry preserves its publication ID, role, title, source URL, scope, dependencies and observed access advisories. Unqualified entries retain `runnable:false` and their reason, without a fabricated command. A runnable configuration is not a verified or complete publication. Existing publisher stops remain in force.

The ordinary `run --target ... --publication ... --out ...` command remains an explicit single-publication action. No all-publication collection or verification action is added. Full-scope discovery and acquisition acceptance are separate.

The composed launcher also incorporates the reviewed owned-interpreter correction: setup records the actual owned Python version, and doctor checks it against Python3.12 and the setup receipt. This does not add same-version executable binary pinning.

Root documentation that currently describes `plan --all` as listing primary and secondary publications should instead use `plan --all-publications`; retain `--all` where a primary-only list is intended. Root owns production documentation edits.
