# Target and publication registry

The registry provides an explicit primary configuration for each of the 100 assigned targets. `verification.json` records the current exact counts: 63 Municode, 15 American Legal, 11 eCode/municipal.codes, 3 enCodePlus and 8 official-source primaries. Every primary is dispatchable. This is a configuration result, not 100 full live publication passes.

`targets.json` preserves the exact sequence, government name, state and city/county scope from `expanded-scope-index.json`. `publications.json` contains the primary configurations plus separately known publications, historical alternatives and unresolved candidates. A runnable candidate has a qualified adapter configuration. An unsupported candidate has a reason; an official landing page or document library is not silently treated as an acquired publication. Counts of candidates are not counts of independently current publications.

The historical `prior_validation` fields describe bounded samples only. Base mappings remain `validation_level: mapped_only` and `full_live_verified: false`. Family implementation tests and specifically completed publications are recorded separately in adapter validation summaries and the QA validation matrix. Collecting a primary book does not close a jurisdiction: each target retains an unresolved required-scope ledger for uncodified enactments, adopted standards and undiscovered families.

## Run explicit plans

Run these commands from the repository root. Python 3.12 is tested; use each adapter's requirements and, for browser families, its documented Node/Playwright/ordinary Chrome setup. The registry itself uses only Python's standard library.

```sh
python3 -B collectors/registry/collect.py status
python3 -B collectors/registry/collect.py plan --target 70 --python python3
python3 -B collectors/registry/collect.py plan --all --python python3
python3 -B collectors/registry/collect.py collect --target 70 --out /fresh/reno-admin
python3 -B collectors/registry/collect.py collect --target 70 --out /fresh/reno-admin --resume
python3 -B collectors/registry/collect.py verify --target 70 --out /fresh/reno-admin
```

There is no all-target collection command. `plan --all` sends no requests. Collection and verification require one explicit target and output. The output path is resolved before adapter dispatch. Existing nonempty output requires explicit resume; adapter checkpoints apply their stricter source/version/options checks.

Select a separate publication with its exact `publications.json` ID:

```sh
python3 -B collectors/registry/collect.py plan --target 67 --publication 67-052d9663670b
python3 -B collectors/registry/collect.py collect --target 67 --publication 67-052d9663670b --out /fresh/lincoln-charter
python3 -B collectors/registry/collect.py verify --target 67 --publication 67-052d9663670b --out /fresh/lincoln-charter
```

That entry uses the source-observed Lincoln City Charter config, separate from the Municipal Code. Other known runnable configurations include exact Municode product selectors, American Legal publication slugs, Aurora UDO/Charter, Fairfax Zoning, Baltimore Charter, Portland Title 33 posted PDFs and qualified official native-document sets. Historical alternatives stay labeled historical. The registry verifier checks every generated configuration against retained identity/source evidence.

Before invoking a family verifier, the wrapper checks the requested target and publication against the run's pinned configuration. Wrong-government runs and another product from the same publisher/client fail this check. The adapter then independently verifies retained raw inventory, parsed output, consistency and assets. A matching wrapper config alone cannot establish corpus completeness. Verification may exit nonzero for valid but explicitly incomplete evidence; see each adapter's verifier exit codes.

## Scope corrections and limits

- Reno selects Administrative Code product 14160; its separately published Land Development Code has a different explicit product selector.
- eCode numeric sample routes are replaced by source-observed customer aliases for whole-Code scope. Municipal.codes configs select exact `/CC`, `/Code` or `/EC` publication roots; Aurora `/UDO` and `/Charter` are separate.
- American Legal titles, publication slugs and accepted government-name aliases come from retained source redux metadata. Louisville/Jefferson Metro and Honolulu retain their full assignment names while accepting the publisher's abbreviated client labels.
- Arlington County's primary selects the current 80-document portal adapter. Full inventory plus bounded native-document flow is tested; the mapping does not claim all 80 documents have been acquired. The legacy posted-chapter set is a separate alternative and does not replace current scope.
- Portland's primary HTML-title configuration keeps unresolved Title 33 explicit. A separate posted-PDF configuration can acquire that native file set; future effectivity and page-versus-section semantics remain visible.
- Primary source inventories are not exhaustive inventories of every law applicable within the government. County territory, consolidated government and independently incorporated municipalities require their retained scope notes and explicit publication selection.

The [image policy](../IMAGE-POLICY.md) is explicit in each configuration: normalized images become literal `[IMAGE]`, source IDs/headings remain, and no standalone image downloads occur. Intentional image omission is not a missing-attachment failure. Original publisher HTML/PDF bytes remain source evidence and may contain images. Required non-image documents remain subject to acquisition and reconciliation.

## Offline audit

```sh
python3 -B collectors/registry/verify.py
python3 -B collectors/registry/test_registry.py
```

These commands are read-only and send no network requests. Tests cover exact 100-target identity, missing/duplicate/foreign mappings, unobserved Municode products, eCode subtree mistakes, historical sample promotion, wrong-target same-family verification, wrong-product same-client verification, output path resolution and refusal of all-target execution. Nonzero means the configuration audit or a fault test failed. `source-evidence.zip` contains the exact compact raw identity/inventory documents and original 100-target index used by the audit; its manifest verifies every retained byte. A relocated collectors-only copy therefore does not require the original large validation packages. Original logical evidence paths remain visible inside that bundle.

`build_registry.py` is an authoring tool, not a collection dependency. It deterministically rebuilds mappings from the repository's immutable historical inventories and current adapter configs. Ordinary collection does not import old package code or require an absolute original workspace path. Portable plans use `python3`; `--python` chooses a concrete interpreter for actual dispatch.
