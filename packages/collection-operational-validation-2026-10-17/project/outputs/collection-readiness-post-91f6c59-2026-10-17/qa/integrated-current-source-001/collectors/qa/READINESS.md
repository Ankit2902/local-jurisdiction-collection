# Publication readiness acceptance

This stage audits all130 distinct target governments and every concrete publication/candidate in the active union catalog. It retains original publication scope, current/historical/external applicability, source identity, dispatchability, testability, exact evidence and unresolved requirements. The earlier `validation-matrix.json`, 126-case report and release manifests describe the prior sealed stage; they remain historical evidence.

`build_readiness_ledger.py --out NEW_JSON` creates a fresh per-publication ledger. It separates configuration availability, existing publisher access prohibitions, prior exact source proof, and new readiness acceptance. Every row has explicit identity, full inventory, owned text, required documents, table fidelity, image policy, closing consistency, resume, setup/CLI and legal-structure requirements. Family tests never establish another publication's full live pass. Native PDF/page capture does not establish section/table semantic equivalence. Required separate publication dependencies are explicit, including Fairfax's complete Public Facilities Manual root rather than its cover.

```sh
python3 -B collectors/registry/verify_catalog.py
python3 -B collectors/qa/test_readiness_catalog.py
python3 -B collectors/qa/test_ops_acceptance.py
python3 -B collectors/qa/test_all_family_image_metadata.py
python3 -B -m unittest collectors.qa.test_gridics_acceptance
python3 -B collectors/qa/test_image_audit.py
```

These tests use temporary gates, durable-state directories and synthetic law, and perform no publisher requests. They test real production dispatch/model/verification entry points. Source changes during a launcher run, wrong-target verification, unowned outputs, dependency gaps, native-only zero exits, runtime/shim drift, host-scoped cooldowns and lost temporary stop files cannot silently pass.

Actual source fidelity is audited separately. `municode_raw_tables.cjs RUN FRESH_REPORT` reads original hash-bound API Docs.Content, checks exact publication/job queries and body ownership, and compares original offline Chrome DOM cell text/tag/rowspan/colspan against normalized tables. `encodeplus_raw_tables.cjs` reads original source pages, removes descendant section ownership, and compares exclusive source tables. Neither uses normalized HTML to reconstruct the expected cells. Chrome has JavaScript disabled and every network request blocked. Zero source tables is explicitly not applicable, not failure. These scripts need the unified runtime's Node/Playwright environment.

`audit_municode_queue.py --status STATUS_JSON --out NEW_QA_DIR --runtime RUNTIME` applies the independent audit to explicitly indexed completed jobs, keeping source checkpoint/script hashes with each report. Failed/partial runs remain partial. Actual source QA has already exposed and preserved failed Fairfax outputs caused by inline fragment spaces and hidden date-sort keys; corrections require a new source-bound derivative and a fresh audit.

`audit_images.py RUN` checks binary signatures and every JSON response's image MIME/body reference, including UUID-named receipts and opaque `.bin` payloads. Empty image HEAD bodies and original native PDF/HTML/ZIP files are allowed; separate image bytes are not. The six-family metadata probe checks full data-image payload redaction, cell-owned placeholders, stylesheet/source/object branches and comments. It does not render/extract image pixels.

Reports are written to fresh paths under `outputs/collection-readiness-2026-10-17/qa`. Prior failures remain retained, and read-only replays must not modify source proof. Database ingestion and legal-currentness opinions remain outside this work.

`run_readiness.py --out NEW_LOGS` combines the current union/CLI/ops/dependency/image/Notes/Gridics acceptance with the complete offline family suite. Run it from a physically isolated exact collector copy during concurrent development. It hashes source before and after, and source drift invalidates the combined receipt even when individual commands pass. CLI refusal tests run the real dispatcher under a hard subprocess adapter-launch tripwire, so a newly qualified target cannot accidentally start acquisition. The earlier `acceptance-001` incident is retained as an interrupted test-safety failure and is never a proof.

`audit_normalized_images.py RUN` inspects actual normalized JSONL records and recursive metadata for active image elements/attributes/CSS and inline pixel payloads. `audit_municode_inventory.py RUN` independently reconstructs raw TOC IDs and exact Docs-to-record body hashes, parent paths and closing TOC equality without importing a family parser. These are bounded fidelity dimensions, separate from a claim of complete legal serialization.

The current requirement ledger accepts only explicit `--receipts` with exact project-relative evidence paths and SHA256. Positive dimensions are counted separately; actual Henderson unified runtime/source coverage and raw-table/image audits are preserved even while actual interruption/resume and full semantic rendering requirements remain open. Native-only, partial dependency and access-stopped proofs cannot close those gaps.

`readiness-requirements.json` is the sealed compact checkpoint ledger: its 224 entries, 186 dispatchable configurations and 128 stopped configurations remain historical. The active [follow-up ledger](followup-requirements.json) currently records 225 entries, 193 dispatchable configurations, 32 unqualified candidates and 131 stopped configurations across all130governments. See [follow-up source findings](FOLLOWUP-READINESS.md); no full-readiness count is inferred from dispatchability. This operational prohibition records specific observed events, not a blanket service-availability claim. Actual earlier successful source captures remain credited. `proof-receipts/` retains compact source/table/image/stop witnesses; larger immutable evidence and interrupted candidates remain under the new readiness output directory.
