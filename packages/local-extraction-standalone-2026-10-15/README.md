# Standalone local-code acquisition handoff — 15 October 2026

This package addresses the **24 jurisdictions previously dependent on CUA** in the 30-jurisdiction validation handoff. It supports both the retained CUA path and new Codex-free acquisition/local-processing paths. It does not recalculate the current database backlog or perform whole-code collection.

The six Sol subagents tested the remaining publisher/browser gaps, real publisher downloads, official alternatives and runtime diagnostics. Independent review then reran the delivered offline suites and verified the evidence manifests.

| Outcome | Jurisdictions | What was actually validated |
|---|---|---|
| Bounded standalone acquisition and export passed | Berkeley, Petaluma, Sonoma, Everett — **4** | Fresh ordinary headed Playwright. Three cities have matching legal-body/currency snapshots; Everett has one actual publisher HTML download and parsed section, without a fresh repeated endcheck. |
| Standalone acquisition partly qualified | Bellingham — **1** | Initial legal capture and 13 exported records; later HTTP 429 prevented the final consistency check and completion of the live job. |
| Manual publisher export plus standalone local importer passed | Flagstaff, Fremont, San Carlos, Burien, Renton — **5** | Actual publisher HTML downloads; 43 bounded records verified. Unattended network acquisition still returned challenges. |
| Primary standalone acquisition remains unqualified | eCode360 jurisdictions — **14** | Twelve new initial 403 responses and one 429; Foster City's earlier 403 is retained, and its new headed probe was deferred by the host-stop ledger. |

**These are bounded method qualifications, not completed corpora.** Municipal.codes fresh body acquisition still uses independently retained earlier CUA inventories. Fresh standalone whole-publication inventory acquisition, full body coverage, attachments and coherent full-run version checks remain implementation gates. The 44 Municipal.codes records include Bellingham's 13 partial-pilot records. Across Municipal.codes and CodePublishing there are 87 primary-code sample records, plus seven separate Charter sample records.

Start with the [24-city source matrix](SOURCE-MATRIX.md), its [machine-readable version](SOURCE-MATRIX.json), and the [execution plan](EXECUTION-PLAN.md). Each matrix entry carries the earlier discovery record, new evidence, source URLs, currentness limits, official alternatives and next action. The authoritative phase reports are named `STANDALONE-VALIDATION.json`; copied earlier E2E reports remain historical evidence.

## Choose the executable path

**Municipal.codes:** read [its runbook](municipal-codes/README.md). `standalone_acquire.mjs` performs ordinary headed legal-page acquisition. `standalone_ui_export.mjs` exercised the publisher's Share → Save → Web Page (HTML) flow for Berkeley and Everett. Direct navigation to advertised export URLs failed; the normal UI produced actual browser blob downloads. `prepare_standalone.py` replays the retained fresh acquisitions into verified CSV/JSON and provenance outputs. Live scripts need Node, pinned Playwright and a graphical Chrome session, but no Codex. The success does not qualify headless server scheduling. Preserve the recorded host stops for Bellingham and Sonoma when planning later live work.

**CodePublishing:** read [its runbook](codepublishing/README.md). An operator selects the required title/chapter, uses Print/Save Selections → HTML → Save, and retains the unchanged file. `register_manual_export.py` records the file and operator's source/time/selection attestation. `import_publisher_export.py` validates the publication, edition and explicitly selected chapters, then creates local exports without a browser, network or Codex. All five cities passed this path. During this validation CUA operated the ordinary public UI; the documented human workflow replaces that UI helper. It is not evidence of unattended acquisition. `run_publisher_pilots.py` reproduces the five retained download-to-export pilots offline.

**eCode360:** read [its runbook](ecode360/README.md). The standalone acquisition and importer code is delivered, but no primary-code live success is claimed. The successful-acceptance branch has synthetic tests only. Initial 403 responses do not establish that passive verification or an ordinary headed browser could never work. The host was rate-limited; the final helper stops the host and records Retry-After rather than continuing a queue. The exact earlier executed revision and its limitations are preserved. Do not blindly restart the batch.

Publisher PDF/Word availability depends on publication permissions and login. The [publisher-export findings](publisher-exports/EXPORT-FINDINGS.json) distinguish observed controls, actual downloads, unknown availability and untested formats. The documented [eCode360 API](https://developer.ecode360.com/) is a possible supported integration using municipality-issued credentials; no credentials were obtained and that path is untested. No account creation, purchase or vendor outreach occurred.

## Official alternative publications

[All 24 official-site findings](official-alternatives/OFFICIAL-ALTERNATIVES.json) are retained with discovery links, HTTP receipts and currency limits. No current complete replacement municipal code was qualified in this bounded search; that does not establish that none exists.

- **Emeryville Charter:** actual fresh HTTP acquisition, an eight-node source inventory and two exported sections. The city page identifies adoption in 2014 but supplies no current-through amendment marker. Use [the Charter qualification script](official-alternatives/qualify_charter.py) and [its runbook](official-alternatives/README.md).
- **Santa Clara Charter:** actual ordinary HTTP download of a 29-page official scanned PDF, separately identified from proposed revisions. The later [OCR pilot](ecode360/README.md) uses macOS Vision/PDFKit and a compatible SDK. The first operative page was visually checked and yielded five complete provisions; section 303's page-boundary heading remains unresolved. The remaining pages and full Charter are unqualified. The official-alternatives report covers download only; the eCode360 companion report records this later OCR result.

These separate Charter results do not close the Emeryville or Santa Clara primary municipal-code gaps. Historical adoption ordinances, repealed codes and empty downloads were not substituted for current codes.

## Validation, fixes and evidence

Independent review passed **143 Python tests**, **37 Node checks**, and **3,828 child-manifest hash references**. Those are regression/integrity checks, distinct from the fresh live results above. Logs, exact commands and source hashes are in [independent-review](integration/independent-review/RESULTS.json), [Node review](integration/independent-review/NODE-REVIEW.json), [manifest review](integration/independent-review/MANIFEST-REVIEW.json), and [the consolidated summary](VALIDATION-SUMMARY.json). The shared intake utility additionally checked actual publisher exports; an intake integrity pass alone is not full legal extraction.

The new real downloads exposed two parser differences that are fixed and covered by regressions: CodePublishing IDs on child anchor elements, and Everett's exported anchor versus its canonical source route. Everett's fix retains the original anchor and raw-source hash, permits only a narrowly verified source-node match, and refuses empty aggregate exports. Fremont's imported sample preserves eight legal tables and their rows/cells, along with complete source text and order.

An earlier Everett currency check selected a statutory footnote instead of the site footer. The [correction record](municipal-codes/CURRENCY-CORRECTION.md) documents the exact error. The corrected retained before/after notices and new standalone download all agree: **Ordinance 4203-26, passed September 16, 2026**. The previous sealed handoff was not edited.

The successful live script revisions are retained alongside receipt hashes. Final transport hardening was tested offline after live work stopped; it was not silently represented as the exact live-executed revision. [Runtime diagnostics](integration/runtime-diagnostics/README.md) include successful independent browser controls and distinct publisher challenge results. Only macOS was exercised; Linux/Windows setup guidance is not cross-platform execution proof. Runtime installations, browser profiles and imported cookie state are not included.

## Verify or reproduce locally

Unpack the complete archive and keep its relative directory structure. Verify it before creating new outputs within the directory:

```sh
python3 verify_bundle.py
```

Use each family's pinned dependencies and commands for deployment. For an independent offline regression environment, use a modern Python with OpenSSL, then:

```sh
python3 -m venv .review-venv
.review-venv/bin/python -m pip install -r requirements-review.txt
.review-venv/bin/python integration/run_offline_review.py
.review-venv/bin/python integration/review_node.py --node /absolute/path/to/node
.review-venv/bin/python integration/review_manifests.py
```

These review commands write new review logs/results, so run them in a working copy after the initial integrity verification. Use new output directories for parser replays. Do not use `verify_bundle.py --write` to conceal changed evidence; that option deliberately creates a new manifest and is for reviewed releases only.

The next implementation step is to reproduce the chosen bounded method on the team's machine, qualify fresh inventory acquisition, then extend by publication family with resumable acquisition, explicit unresolved-node dispositions and full-run version reconciliation. The source matrix identifies the remaining prerequisite for each jurisdiction. The complete collection and database import remain outside this handoff.
