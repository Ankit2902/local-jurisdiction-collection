# Current 130-target catalog

`catalog.load_catalog(cohort='all')` returns `{schema_version, cohort, targets, publications}` without network or writes. Cohorts are `expansion`, `original`, and `all`. Expansion IDs1–100 stay unchanged. Original30 use stable `original-<slug>` IDs; none overlaps the expansion list by jurisdiction and state. A publication has one owner target, an exact source/selector/configuration, its original scope and an explicit qualification status.

The frozen expansion JSON/source bundle remains separate from the original extension. `original-targets.json`, `original-publications.json` and their compact source bundle retain the original30 current routes and reviewed eCode customer identities. `readiness-overrides.json` carries source-backed acquisition strategies and dependency/alias relationships. `readiness-qualified-configs.json` qualifies exact newly observed configurations. `readiness-additional-publications.json` adds newly discovered separate publications without renumbering previous entries. A qualified configuration is not a completed corpus.

```sh
python3 -B collectors/registry/collect.py plan --all --cohort all
python3 -B collectors/registry/collect.py plan --target original-daly-city-ca
python3 -B collectors/registry/collect.py plan --target 100 --publication 100-fairfax-public-facilities-manual
python3 -B collectors/registry/verify_catalog.py
```

Use `python3 collect.py setup`, `doctor`, `run`, and `verify` from the repository root for the unified standalone runtime. The direct registry dispatcher accepts explicit `collect --target ID --publication PUB --out NEW` and `verify` commands. Planning does not contact a publisher and does not override an access stop. `--all` is planning only. Output paths resolve before family subprocess dispatch, and verification binds the chosen target/publication to the retained run before invoking its verifier.

Plans expose publication title, expected identity, current versus historical/external scope, required dependencies and configuration aliases. Sacramento's overview/Table of Resolutions candidate is an alias of the exact observed `resolutions` book, not another independently validated publication. Lancaster County publications remain external references under Lincoln's inventory; they do not become Lincoln law.

New qualification requires retained source evidence. An ordinary government landing page, document-library link or table-of-contents cover is not assumed to be a whole publication. The compact source bundles let the union verifier reconstruct identity/configuration qualification in a physically relocated collectors-only tree. Authoring scripts may require original project evidence; runtime planning and verification do not.

The eCode360403 and municipal.codes429 stops remain operational blockers. Their mapped original and expansion configurations are dispatchable inputs, while fresh live requests remain prohibited. The family operator/export/import tools are offline recovery workflows and preserve refusal history; they do not grant source access or establish full coverage by themselves.

Current requirement/gap evidence is recorded under `outputs/collection-readiness-2026-10-17/qa`. See the [QA readiness guide](../qa/READINESS.md). Neither an adapter test nor a prior bounded pass is inherited as full live proof for another target.

A required separate publication can be supplied to the unified launcher explicitly:

```sh
python3 collect.py verify --target 100 --publication 100-0506c8bf0a84 --out /proofs/fairfax-zoning --dependency 100-fairfax-public-facilities-manual=/proofs/fairfax-pfm
```

The launcher independently runs the current catalog-bound family verifier on each required proof using the owned runtime. It records exact publication/configuration, current collector and runtime hashes, and before/after hashes of every proof file. Missing, wrong-scope, partial, changed or unqualified proofs remain explicit dependency gaps. Transitive dependencies require repeated `--dependency` arguments. Supplying a cover or a native file/page capture cannot satisfy full publication text acceptance. Verification performs no publisher requests. A prior owned capture whose only remaining gap is a dependency is reverified without repeating acquisition when the exact proof path becomes available.
