# Running local code acquisition without Codex

Choose the method qualified for the jurisdiction in the accompanying source matrix. A successful browser page, a downloaded file and a verified legal export are separate milestones. Use the per-method evidence to determine which stages can run unattended and where an operator is still required.

## Standalone browser acquisition

Run the delivered family script with its documented browser channel and headed/headless setting. A headed Playwright run is ordinary standalone automation and does not require Codex, but it does require a graphical browser environment. The recorded result does not automatically qualify a headless server deployment or a different browser release.

Install the declared dependencies in a dedicated environment. Use a fresh browser context for the demonstrated automated paths. Do not depend on a Codex session, a transferred user profile, or previously retained source HTML. Save new acquisitions to new output directories so a replay cannot be confused with fresh retrieval.

Before accepting an acquired document, check the final URL, publisher/jurisdiction identity, expected heading or source node, displayed edition markers and actual legal content. Retain the original response or rendered source, receipt, timestamp and hash. Run the parser and verify the exported text and structure against those exact bytes.

An access challenge is a failed acquisition. A rate-limit response stops further work for the affected host; record Retry-After where provided and leave the run incomplete. A future retry needs a new run and should respect the publisher's timing. Do not keep a scheduled collector retrying challenged pages or substitute a retained successful capture.

## Operator publisher exports

Where the family report qualifies an ordinary publisher download workflow, an operator can perform that browser step without Codex and then run the local importer. Follow the documented publication selection and export format exactly. Record the selected scope, source URL, retrieval time and displayed edition marker before saving the file.

Retain the publisher's original file. Browser Print to PDF, publisher-generated PDF, publisher HTML, and a saved web page are different inputs; record which one was acquired. A publisher export may rewrite anchors and remove navigation, so it must use the corresponding tested import profile rather than being passed indiscriminately to a rendered-page parser.

Use the family importer for legal records. The shared [export intake utility](publisher-exports/export_intake.py) can additionally check file signature, size, hash, expected sample text and retained table structure. It does not authenticate an operator's provenance statement or prove complete coverage. Scanned PDFs and missing expected text remain review-required; an integrity pass alone does not mean successful legal-text extraction.

Account or subscription requirements are prerequisites where documented. A visible Download button does not establish anonymous access, and an advertised format does not establish that it was successfully downloaded. Workflows requiring an unavailable account remain unqualified rather than being counted as automated successes.

## Official alternative sources

An official city-hosted charter or title can provide a useful separate publication even when the main publisher path is blocked. Preserve its official discovery link and document identity, and compare its amendment/current-through evidence with the required scope. Do not substitute a historical or partial document for the entire current municipal code.

For an image-only PDF, downloading the file and producing OCR are separate results. Retain the original PDF and rendered page, label OCR output, and review legal text against the page before using it as a corpus record. A bounded page experiment does not qualify every page or layout in the document.

## Extending the bounded pilots

Once the demonstrated method is reproduced on the technical team's machine, enumerate and classify the full in-scope publication inventory. Acquire in resumable, paced batches and preserve all failures. Reconcile each source node and attachment to an explicit disposition. Compare versions and inventories across the run, then review difficult tables, lists, appendices and image content before accepting a complete corpus.

The scripts and validation artifacts support that implementation work. Database import and complete-jurisdiction collection remain outside this validation pass.
