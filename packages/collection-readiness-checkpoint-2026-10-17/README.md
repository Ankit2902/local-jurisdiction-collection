# Standalone collection readiness checkpoint — October 17, 2026

This checkpoint preserves the updated standalone collectors and selected terminal validation evidence for the original 30 jurisdictions and 100 expansion targets. It is an engineering handoff with explicit remaining gaps, not a claim that all 130 jurisdiction corpora are complete. Active longer collection jobs are not sealed into this checkpoint.

Start with the repository's current `collectors/ops/README.md`, `collectors/registry/READINESS.md`, family runbooks and `collectors/qa/READINESS.md`. Use `python3.12 collect.py setup --python python3.12`, then `plan --all` to select a publication. The common runtime was installed and exercised on macOS using Python 3.12, bundled Node and ordinary installed headed Chrome. Codex and system npm are not runtime dependencies. Other operating systems have not received equivalent live validation.

## Image requirement

The final collector policy is **no separate image acquisition or extraction; literal `[IMAGE]` in normalized text and HTML**. Source IDs, headings, image-only provisions and table-cell ownership are preserved. Image data must not leak through normalized metadata or legal notes. Native HTML, JSON, PDF and archive files remain original source evidence and may inherently contain embedded images; these are not extracted into image assets. Required nonimage documents remain separate completeness requirements. See the repository's `collectors/IMAGE-POLICY.md`.

## Selected evidence

| Retained run | Result and limits |
| --- | --- |
| `ops/live-henderson-unified-v3` | Fresh shared-launcher acquisition and verification passed for the selected municipal-code publication: 2,122 records, stable opening/closing evidence, zero separate image assets. The independently hosted Development Code remains outside this book. |
| `ops/live-henderson-unified-v2` | Preserved negative integration run: the automatic product-specific reference policy was missing. The error was fixed and a new full run passed; the failed evidence is not relabeled. |
| `ops/live-charter-unified-v4` | Fresh shared-launcher acquisition and verification passed for the separate Lincoln City Charter: 188 nodes, 174 owned bodies, 14 containers, 17 opening and 17 closing blocks. No whole-jurisdiction or global official-edition claim. |
| `gridics/cupertino-portable-v4-replay` | Full ordinary-browser native acquisition, then explicit offline normalization: 22 roots, 2,687 records, 131 tables, 35 image placeholders. Native/rendered comparisons agree. Five unexplained empty entries and 2,308 unresolved reference occurrences keep completeness false. |
| `gridics/miami-current-parser-v3` | Full ordinary-browser native acquisition, then explicit offline normalization: 32 roots, 828 records, 137 tables, 439 image placeholders. Two empty entries, 1,439 unresolved references and 112 opening/closing comparison differences keep completeness false. The comparison differences are whitespace-only diagnostics and have not been waived. |
| `official/san-mateo-full-xml-v1` | Source/Git-tree/include closure and independent replay passed for the selected Code and Charter XML: 2,652 records and 50 tables. Consult the retained coverage for its exact source and publication boundary. |
| `official/portland-all-html-v6` | All 33 observed HTML title documents captured and replayed: 3,168 records and 39 tables. Title 33 remains a separately required native component; whole-publication legal semantics are not complete. |

The `ops/integration-source-*` directories preserve the exact launcher/registry/family revisions used by the live integrations. `tested-source-baseline/` and `qa/acceptance-005-isolated/` preserve the isolated full-suite baseline: 282 test/probe executions, 30 leaf commands and no source changes. Subsequent narrow fixes are qualified by separate delta receipts. A successful historical run is not silently attributed to newer bytes. These snapshots are for offline reproduction; use the repository's current root launcher for live acquisition and its current access advisories. `selected-evidence-copy.json` records which terminal runs were copied and verifies that their bytes remained unchanged during copying.

## Remaining work

The source-family runbooks and current requirement ledger distinguish runnable configurations, synthetic tests, bounded historical samples, full native capture, complete owned text, required documents, image handling, table fidelity, resume, closing consistency and jurisdiction scope. A working runtime or representative city does not qualify every target.

Observed eCode360 and municipal.codes access stops remain in force. Their offline operator/import workflows are tested, including first-time imports without an earlier checkpoint, but synthetic complete bundles are not real complete corpora. A later Municode request also received a 403 challenge: a malformed `www...` source href had been interpreted as a publisher-relative URL. The corrected collector retains that raw locator as unresolved without requesting it or guessing a replacement. The observed stop remains in force; the correction does not authorize retries and is not evidence of a general publisher outage. Earlier successful retained publication proofs remain valid for their recorded scope and revisions.

Required documents refused by external hosts remain unresolved. Native publisher PDFs may lag a live API edition; a genuine download or matching route alone does not prove edition equivalence. San Antonio's UDC native header and live API supplement labels disagree; the scripts preserve that mismatch. PDF physical-page coverage does not prove complete legal section or table reconstruction. Intentionally omitted images alone are policy exclusions and do not create completeness failures.

Longer American Legal and official-source runs remain active; enCodePlus jobs are paused at a controlled source revision boundary, and Municode acquisition is stopped under the observed access advisory. Their compact current receipts record the observed scope without promoting pending results. Database ingestion is outside this work.

`delivered-source/` preserves the exact current collector bytes, while `tested-source-baseline/` preserves the earlier full-suite revision. The final delta report binds the later production changes to their SHA-256 hashes. enCodePlus request pacing used a nominal 3.5-second shared gate; retained timing observations remained above the original 3-second floor but included starts below 3.5 seconds. A stricter actual-start interval is not claimed by this checkpoint.
