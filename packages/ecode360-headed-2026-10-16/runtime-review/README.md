# eCode360 headed runtime review

This is an independent, **offline** review of the new ordinary headed eCode360 acquisition phase. This directory makes no publisher requests, launches no real browsers, imports no browser profiles, and contains no cookies or storage state. The sole live worker owns the sibling `ecode360/` directory.

Run the guard regression with Python 3.9 or later and only the standard library:

```sh
cd "outputs/ecode360-headed-2026-10-16/runtime-review"
python3 verify_review.py
```

The verifier checks the audit artifact manifest and runs 15 offline regressions. The tests execute the exact SHA-bound source snapshot in `evidence/reviewed-headed-probe.py.txt` against an isolated fake Playwright runtime. They test source acceptance and rejection, immediate initial/late HTTP 429 stop, persistent host-stop refusal before a later launch, publisher subdomain coverage, safe response-header retention, removal of URL queries/fragments from events, fresh headed launch arguments, and export UI guards. They never import or run the live worker's command-line serial driver. They use temporary synthetic fixtures and do not constitute live 429 or browser tests.

`RUNTIME-REVIEW.json` records the old 429 evidence, exact resumption authorization, actual successful sentinel runtime/source hashes, immutable executed source bindings, the observed new phase state, and limits. Source revisions in older receipts must be compared to their executed archives; replacing the active script does not update the meaning of an earlier receipt. The copied older standalone reports describe the previous phase. The sibling `HEADED-VALIDATION.json`, when finalized by its owner, is authoritative for the completed headed phase.

The prior Santa Rosa receipt captured HTTP 429 at `2026-10-15T19:19:56.133838+00:00` and finished at `19:19:57.169402+00:00`. That executed revision did **not record response headers**. Retry-After remains unknown; it is not evidence that the server omitted a header. The old ledgers remain immutable. A separate explicit user-authorized resumption record permitted one coordinated fresh Foster City sentinel. Its start was 8 hours, 15 minutes, 10.869710 seconds after the old receipt finished. Elapsed time itself was not clearance. That sentinel received initial/final document HTTP 200, matched the requested node/customer/publication, and captured stable legal DOM. It does not prove permanent host availability, a general passive challenge transition, or complete jurisdiction extraction.

The live worker used installed Chrome 155.0.8059.84, Playwright 1.60.0, Python 3.9.6, and macOS arm64, with `channel='chrome', headless=False` and a fresh `new_context()` without imported state. Normal operation on another platform requires installed Chrome, a desktop session/display, a supported Playwright Python environment, and normal network/TLS access. No cross-platform headed run was performed here. The old Python runtime emitted an urllib3/LibreSSL compatibility warning; the browser transport evidence does not establish portability of unrelated Python HTTP clients. A current Python with supported OpenSSL is the practical handoff choice. Browser binaries and environments belong outside the deliverable.

Any new publisher HTTP 429 creates a **separate new-phase** host-stop ledger. The response handler records selected safe headers and stops future publisher requests, including subdomains; it does not wait for the response body. The result is rejected even when source bytes had been captured earlier. A later job refuses to launch while that ledger exists. No automatic expiry, retry, or clearance follows from Retry-After in this reviewed implementation. Existing in-flight browser responses can still arrive; the guard prevents future routed requests once the event has been observed.

Ordinary publisher cookie-consent controls and legal-content download controls are distinct from security/challenge controls. No challenge control interaction is authorized or present in this path. A visible Download menu or an export capability flag is only UI evidence. Actual acquisition requires a saved file with its own bytes/hash and parse checks. Full inventories, full corpora, account/payment flows, and paid exports remain outside this review.
