# Technical team execution and acceptance

This package qualifies source methods with bounded live observations and retained-source replays. It does not mark any jurisdiction's full collection complete. Use the per-source README and validation report as the executable handoff; examples are bounded samples and must not be imported as complete corpora.

## Execution order

1. Apply the current source routes in SOURCE-MATRIX.json. Foster City's municipal code moved from Code Publishing to eCode360; Daly City's official link now points to Municode. Preserve the historical route as provenance, not as a current-route instruction.
2. Reproduce the offline tests in a clean environment. The parent review log binds the passing tests to the delivered Python source hashes. Use fresh output directories for changed parser/configuration/source versions; do not delete checkpoints to hide version mismatches.
3. Validate the acquisition transport in the team's environment against a bounded representative source. Browser observations in this review used the supported in-app browser. Where a standalone Playwright helper is supplied, its transport may be only syntax-checked; the package report says exactly what was exercised. A successful manual/browser observation does not certify automated end-to-end acquisition.
4. Freeze an independent inventory of every publication family. Resolve Charter, zoning, SmartCode, appendices, administrative codes, supplements, district codes, and editorial material explicitly. Navigation nodes are not provision counts. Preserve the official-city link, publisher family identity, currency wording and retrieval timestamp separately.
5. Acquire immutable source artifacts, retaining the requested and final URL, transport, retrieval time, raw hash, parser version and source-specific locator. Gate asynchronous navigation on the requested source identity/heading. Reconcile large browser captures with observed lengths/node counts; reject truncation, access challenges, empty shells and stale content.
6. Compare difficult real examples against rendered sources: long sections, parent-level operative text, nested lists, tables, images, notes, attachments and appendices. Resolve the source-specific exceptions in the package reports. Keep unresolved material visible rather than silently omitting it.
7. Run the full extraction in the team's environment. Reconcile every independent source node to exactly one documented disposition, every record to its raw artifact and locator, and any many-to-one/one-to-many mapping explicitly. Do not deduplicate by printed citation alone. Reconcile starting and ending inventory/version snapshots.
8. Verify clean and interrupted/resumed results match, CSV/JSON parity, field contract, stable source identities, and raw hashes. Review unresolved dispositions before promoting a full publication or jurisdiction to complete. Import only after these checks.

## What “validated” means here

- **Offline regression tested:** parser/identity/resume behavior was exercised on the supplied tests.
- **Retained-source replayed:** the script processed actual retained source bytes; the acquisition date is recorded separately.
- **Live route observed:** the current source identity/navigation was seen; this alone does not prove body extraction.
- **Live sample parsed:** current source text was retained and processed for a bounded sample, where the report says so.
- **Inventory captured:** an identified navigation tree or document index was retained and reconciled for its stated scope. It does not prove other families or all provisions complete.
- **Full collection qualified:** requires the full-run acceptance above. No package in this delivery has this status.

The source-specific modules share the legacy 16-field envelope and provenance/semantic sidecars, but they remain separate pilots rather than a fully integrated production scheduler. The technical team should integrate their acquisition/replay flows into its normal job, storage and monitoring infrastructure after the source gates pass.
