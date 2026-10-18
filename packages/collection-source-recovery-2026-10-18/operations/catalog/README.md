# Catalog-to-handoff gap audit after 716cfcb

This is an offline operational and scope audit of the actual 225-entry, 130-government union catalog. It does not rerun source-fidelity audits, acquisition, native parsing or publisher requests, and does not infer that a runnable config is a qualified completed publication. No production, database or Git writes were made. `publication-gap-matrix.json` gives every exact publication ID, owner, URL, collection/verification plan, stop, source profile, existing corpus reader and remaining action; `unqualified-30.json` preserves all30 exact recorded unsupported reasons and source references.

## What can be operated now

- 195 configurations dispatch; 30 do not. All195 plans were constructed offline and all30 unqualified entries refused dispatch as expected.
- 154 catalog entries carry observed workflow advisories;153 of these have runnable configurations. The remaining42 runnable configurations have no catalog advisory (24official/18enCodePlus). Absence of a catalog advisory does not prove live availability or release any shared or external-host stop.
- Current source-family collectors and source-specific exporters exist. The separate16-column `corpus_package` layer has143 potentially compatible runnable configurations by its declared input profiles, including21ecode360 configurations whose reader is deliberately retained-incomplete only. This is capability/shape eligibility, not143actual export proofs. The other52 runnable profiles have no currently qualified `corpus_package` reader:23official,18municipal.codes,6enCodePlus standalone natives,3Gridics,2AmericanLegal PDFs. Existing rich/native/legacy exporters must be reused and qualified; this is not a claim that they have no parser or output.
- Five actual retained publication exports are sealed in `packages/collection-readers-and-structure-2026-10-18`: Flagstaff2661, Henderson2122, LincolnCharter188, Albany3006, Cleveland6140. Their reviewed source-qualified scopes are not inherited by other entries. Only exact Flagstaff primary currently receives selected-publication readiness; strict corpus/jurisdiction gates remain false. The strict ledger's zero all-requirement passes is not a contradiction of this narrower acceptance.

## Prioritized actionable gaps

| Priority | Finding | Exact action and qualification boundary |
|---|---|---|
| P0, concrete code defect | The active ledger mixes current catalog plans with copied prior flags:9 stale/missing dispatch flags and26 stale/missing access flags/evidence. | Review `ledger-candidate/current-status.patch`. It refreshes both qualification fields and both stop fields from current catalog, preserving copied prior values under explicitly historical metadata. Six actual225-row tests pass. No readiness/requirements/active-proof result changes. |
| P1, CLI handoff | Existing `plan --all` means130primaries, not all225publication entries. Secondary selection is possible only with explicit IDs/API enumeration. | Root/Major is preparing additive read-only `plan --all-publications`; retain current `--all` semantics and single-publication acquisition. Until promoted, use the exact per-entry commands in the matrix or catalog API, not an invented flag. |
| P1, configuration/scope | All30 entries remain non-dispatchable for exact reasons listed below. | Qualify authoritative source identity/inventory and choose native/HTML/document-set adapter. A city homepage, document-library link or map portal must not become a whole legal book by assumption. |
| P1, offline opportunity | Historical UPOC2024 `82-8fbdce15716d` has retained172-page source and a source-pinned parser profile but remains an unqualified genericHTML/TOC candidate. | Qualify a historical native config using SHA877c6e… and exact observed `codes.opkansas.org` receipt. The catalog's `online.encodeplus.com` alias is not qualified by that profile; do not assume equivalence. Preserve CID/edition/source-structure gaps. No new publisher request is needed to assess existing evidence. |
| P1, canonical handoff | 52runnable profiles have source-specific outputs but no qualified16-column common corpus reader. | Build finite adapters from canonical rich IR plus independent source inventories/dispositions. Do not flatten native page counts into legal sections or substitute superseded detector text. Start with already reviewed native logical profiles/closed HTML sources; keep failed semantic/dependency dimensions explicit. IDs and existing exporter paths are in every affected matrix row. |
| P2, documented audit runtime | Bare system `python3 -B collectors/registry/verify_catalog.py` failed here because BS4 is absent. Catalog planning is stdlib; qualification auditing imports BS4. | Run with the installed supported collectorPython, or clarify the runbook dependency boundary. The exact owned Python3.12 runtime audit passes130/225/195 with no requests. No dependency or source code was changed. |
| Scope, not flag repair | Required separate books/external standards, historical alternatives, aliases and discovered books outside225 remain unresolved. | FairfaxZoning explicitly depends on `100-fairfax-public-facilities-manual`; Sacramento resolution alias is one sourcebook, not a new proof; county/township references and historical Overland books retain their roles. FlagstaffEmployeeHandbook and KingCountyBoardofHealth are separately known unresolved scopes, not primary completion. |

`collectors/registry/READINESS.md` still says131stopped in the audited version; the current catalog and JSON ledger summary say154. Root/Major is correcting the registry prose separately. Root has already updated the QA guide's current top-level counts; historical checkpoint tables remain historical and are not counted as bugs. Likewise the root Overland successful receipt is explicitly superseded for required-PDF semantics by the later integrity checkpoint/current gate. It must not be relabeled a current complete proof, but no rewrite of its immutable historical record is proposed.

## The30 unqualified entries

Reasons are copied exactly in `unqualified-30.json`:

- **S1:** Known government route lacks a qualified publication inventory/content selector; it is not assumed to be a complete publication (22official entries).
- **S2:** Exact secondary enCodePlus TOC identity/base configuration remains unqualified; observed landing/link alone is insufficient (7entries). Native file evidence can support a different explicitly qualified adapter; the wording must not be interpreted as proving that every linked document needs a TOC API.
- **S3:** Observed family route was not accepted; access challenge retained, no retry authorized (BellinghamCharter).

| Publication ID | Government / retained title | Reason |
|---|---|---|
| `4-0b0195a762ff` | Dallas — Volume IV Chapter 51P Planned Development District Regulations | S1 |
| `5-684f5e2d3984` | Fort Worth — Zoning Ordinance Appendix A | S1 |
| `15-4cb58ccd8b21` | Boston — Boston Zoning Code | S1 |
| `42-e21aaee60b51` | Salt Lake City — Policies, Procedures, Administrative Rules and Executive Orders | S1 |
| `52-eeabc8ab461c` | Manchester — Separate zoning/subdivision regulations | S1 |
| `67-b8a8412beb82` | Lincoln — Lincoln-Lancaster County Comprehensive Plan | S1 |
| `82-0d03e44d2a87` | Overland Park — Maps | S1 |
| `82-cfe47a936088` | Overland Park — Standard Traffic Ordinance (STO: Effective 5/01/2026 - 10/1/2026) | S2 |
| `82-7a796760f2f3` | Overland Park — Traffic Code (Prior to 5/01/2026) | S2 |
| `82-8fbdce15716d` | Overland Park — Uniform Public Offense Code (UPOC: Effective 10/1/2024 - 10/1/2026) | S2 |
| `82-301463c368c5` | Overland Park — Uniform Public Offense Code (UPOC: Effective 9/1/2023 - 9/30/2024) | S2 |
| `82-02572b382672` | Overland Park — Criminal Code (Prior to 9/1/2023) | S2 |
| `82-1c7aee0a7a4d` | Overland Park — Developer Resources | S1 |
| `82-3e17cb77766f` | Overland Park — Permits & Licenses | S1 |
| `82-a1fff72907c4` | Overland Park — What's Happening in my Neighborhood? | S1 |
| `82-702e19cf3533` | Overland Park — Development Handbook | S1 |
| `82-85d1e5938f4a` | Overland Park — Comprehensive Plan | S1 |
| `82-af76927ebdd0` | Overland Park — Vision Metcalf | S1 |
| `82-556d66d43b24` | Overland Park — Civil Engineering - Design and Construction Standards | S1 |
| `82-36ba4b2b2941` | Overland Park — Building Code | S1 |
| `82-34ff7d4dbd3e` | Overland Park — Johnson County Zoning & Subdivision Regulations | S2 |
| `82-6eedef9a53f0` | Overland Park — Oxford Township Zoning & Subdivision Regulations | S2 |
| `82-71fc0df74ade` | Overland Park — Overland Park, KS | S1 |
| `89-d0f7be3c16b5` | Stamford — stamford | S1 |
| `90-5918edb057f6` | Cambridge — cambridge-zoning | S1 |
| `95-152a3da8bd28` | Baton Rouge / East Baton Rouge Parish — baton-rouge-udc | S1 |
| `95-4408caae6a9e` | Baton Rouge / East Baton Rouge Parish — baton-rouge | S1 |
| `96-7e8795b1baee` | Clark County — clark-title30 | S1 |
| `96-55b5a35f127a` | Clark County — clark-county | S1 |
| `original-bellingham-wa-family-charter` | Bellingham — charter | S3 |

## Commands and evidence limits

The normal publication operation remains explicit and singular:

```sh
python3 collect.py plan --target TARGET --publication PUBLICATION
python3 collect.py run --target TARGET --publication PUBLICATION --out /ABS/NEW
python3 collect.py verify --target TARGET --publication PUBLICATION --out /ABS/RETAINED
```

These are plans/instructions, not permission to contact a stopped publisher. All225 exact parameter sets and source identities are in the matrix. Unsupported entries intentionally have no executable acquisition command. Dependency verification uses `--dependency PUB=/ABS/PROOF`, retaining separate proof qualification.

The catalog audit was run with the tested Python3.12.14 executable:

```
outputs/collection-readiness-post1997ee1-2026-10-17/fresh-setup/runtime-v1/venv/bin/python -B collectors/registry/verify_catalog.py
```

It returned PASS for130governments/225entries/195dispatchable. The bare systemPython failure is a missing BS4 environment, not evidence of bad catalog sources. The isolated ledger regression command is `SUPPORTED_PYTHON -B ledger-candidate/test_current_status.py`; it uses actual225catalog rows, all195dispatch plans and30refusals, exact history preservation and unchanged requirements/readiness. It does not run collectors or reinterpret any legal source.

`audit_catalog.py --repo REPO --out NEW_AUDIT_DIRECTORY` regenerates scope/plans from the selected repo, but expects the adjacent isolated ledger candidate when testing that patch. It writes only audit evidence. Historical source pins record the exact bytes used here; later root promotion may intentionally change them. Routine evidence verification should hash this manifest rather than regenerate into this frozen directory.

Images remain exact `[IMAGE]`. This audit did not fetch, decode, extract, render or OCR images, open PDFs or create native source derivatives. Immutable original evidence may intrinsically embed images; this audit did not inspect those payloads.
