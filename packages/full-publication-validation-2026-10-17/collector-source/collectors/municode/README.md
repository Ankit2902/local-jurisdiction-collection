This is an unbounded, resumable collector for whole Municode publisher publications. It dynamically inventories the client's visible CODES publications and pins each selected product, latest job and complete TOC. It preserves every returned document's own body, including container preambles and front matter, instead of selecting section-shaped leaves. A whole publisher publication is a distinct scope from a whole jurisdiction: `jurisdiction_complete` always remains false because separately hosted code families, uncodified ordinances and incorporated external standards are outside the selected book.

The normal publisher Print workflow supplies the bulk route: `GET /api/CodesContent/docIds` with product, job and selected root document IDs. Selecting a publication root expands its owned chunks and descendants. The collector reconciles that response against every pinned TOC ID. It makes conservative missing-ID batch requests when needed; unexpected IDs, duplicate ownership, unexplained empty leaves, unhandled document types and source changes prevent completion. A separate landing-page request supports the one narrowly justified root exclusion: the TOC root is structural and its own source response is an empty DocType4 publication landing page. No arbitrary structural exclusions are accepted.

Python 3.9+ uses the standard library only; `requirements.txt` intentionally contains no third-party dependencies. Node 20+, Playwright 1.62.1 and ordinary installed Google Chrome are required for live collection. `package-lock.json` pins the Node dependency graph. The shared gate uses POSIX `fcntl`, so macOS/Linux are supported; Windows portability is not claimed.

```sh
cd collectors/municode
npm ci
```

From repository root, collect a fresh primary publication with explicit ProductID:

```sh
python3 -B collectors/municode/collect.py \
  --registry collectors/registry/targets.json --target 60 \
  --product-id 14896 \
  --reference-policy collectors/municode/policies/henderson-14896.json \
  --out /absolute/FRESH/henderson
```

`--product-id` is the API ProductID / ClientContent `codes[].productId`. The `--publication-id` alias means the same product selector; it does **not** mean the native-PDF `publicationId`. If no product selector is supplied, collection traverses all currently visible CODES products for that client. A registry entry's URL supplies the client context; selection uses the observed inventory's exact product name and verifies the requested product/client identity, so separately published books can be selected without guessing a URL slug. All selected product IDs appear in coverage reports.

Without a registry, provide the normal public publisher page and explicit identity:

```sh
python3 -B collectors/municode/collect.py \
  --url https://library.municode.com/nv/henderson/codes/code_of_ordinances \
  --state NV --client-name Henderson --client-id 11734 \
  --product-id 14896 \
  --reference-policy collectors/municode/policies/henderson-14896.json \
  --out /absolute/FRESH/henderson
```

A normal headed Chrome session opens the public document and calls live public APIs. Application `/dist/` and unrelated assets are omitted while publisher security scripts remain available. No cookies are imported, no fingerprints are modified, and no challenge interaction, proxy or login is used. The pre-existing direct-HTTP stop remains in place. Every issued publisher request and every native asset redirect hop uses the existing shared `/tmp/compliSolv-municode-rate-gate` at nominal 3.5-second spacing. All concurrent operators must use the same `MUNICODE_GATE_DIR` if overriding it. A challenge, HTTP 403 or 429 persists the shared browser stop; a 429 also honors Retry-After with a minimum 300-second cooldown. This collector never clears or bypasses those stops. Resume requires the ordinary browser route to remain legitimately available.

Fresh output must be empty. The CLI takes an exclusive output-directory lock. Atomic source body/receipt commits precede checkpoint updates. Exact executed modules are retained by SHA-256, and resume requires the same source identity, selected products, reference policy, active limit and implementation revision. Before issuing network requests, resume validates every committed body's hash and request binding. It then reacquires live identity, inventory and edition metadata and refuses drift. Corrupt or mismatched cached data is not silently accepted.

```sh
python3 -B collectors/municode/collect.py \
  --registry collectors/registry/targets.json --target 60 --product-id 14896 \
  --reference-policy collectors/municode/policies/henderson-14896.json \
  --out /absolute/existing/henderson --resume
```

An interruption can leave uncommitted raw artifacts; they are retained but never accepted merely because a file exists. Committed content units and assets are reused. Failed/deferred assets can be retried once per explicit resumed invocation with `--retry-assets`, after the operator resolves any shared access stop; the flag does not clear stops. `--allow-asset-host example.gov` explicitly permits a source-referenced external required asset host. Redirects remain restricted to publisher hosts or explicitly allowed hosts. `--batch-size` controls fallback request batches. `--max-items N` is diagnostic only: it limits content request units, is bound to the checkpoint, and **always forces incomplete status**, even when a bulk response happened to contain the entire book. Start a fresh unbounded run for completion rather than removing a limit from an existing checkpoint.

Images are deliberately omitted under the user’s [image policy](../IMAGE-POLICY.md). Ordinary images, picture alternatives, inline SVG, image-only provisions, image file links and CSS image references become literal `[IMAGE]` in normalized text and HTML. Source locators and attributes remain in `image_omissions` and the reference ledger; raw original publisher HTML may inherently contain image references. No separate image binaries are downloaded, extracted, rendered or OCRed. Ordinary browser image resources are blocked while challenge controls remain untouched. Known image URLs issue no acquisition request; extensionless attachments receive a gated HEAD check and an image MIME causes deliberate omission without a body GET. Unknown MIME fails closed.

Required **nonimage** file links and recursively referenced nonimage CSS dependencies are inventoried and acquired separately. Responses retain bytes, URLs, redirect hops, hashes and status; qualification is format-aware and fails closed. Empty/truncated PDF bodies fail; a plausible PDF header/trailer remains `unqualified` because the standard-library core has no complete PDF integrity parser. Required PDFs therefore prevent attachment/publication completeness even after transport succeeds. ZIP-family files require a valid central directory and every member CRC; Office ZIP containers also require their content-type manifest. Plain UTF-8 text/CSS/CSV and JSON receive explicit decoding/type checks. Other binary formats remain unqualified. These checks make no legal-semantic assertion. Missing, blocked or invalid required nonimage attachments prevent attachment/publication completeness. Intentional image omissions do not block completeness and do not claim transcription of image contents. Unknown ordinary external hyperlinks remain unresolved by default, protecting extensionless appendices from silent exclusion. An explicit reference policy can classify an ordinary hyperlink as a separately hosted family boundary or reference-only link with a nonempty, source-backed reason and optional owner IDs. A policy cannot exempt embedded media or obvious file/document links. The supplied Henderson policy applies only to the publisher's Title 19 zoning pointer, whose body explicitly redirects to the official development-code revisions webpage; that separately hosted code is not collected. Its owned pointer text is retained, and jurisdiction completeness remains false.

Outputs are `checkpoint.json`, raw response bodies and receipts, runtime sessions, exact executed sources, top-level `coverage.json`, and per-product `publications/PRODUCTID/{sections.jsonl,sections.csv,coverage.json}`. Record units are publisher-owned documents/chunks, including containers, headings, front matter, tables and leaf provisions; they are not uniformly legal sections. Records retain stable IDs, heading/path, parent, product/job, text, image-free normalized HTML, the original body hash and normalized HTML hash, tables/spans, links and their source attributes, notes and footnotes. Container bodies remain owned by their source DocID; descendant records are not concatenated into parents or duplicated. Identical wording under distinct genuine source IDs is preserved. An image-only source body becomes `[IMAGE]`, retains its source ID/heading and remains a record. Original raw API source bytes retain provenance; normalized HTML has no active image tags or image fetches. Image omission metadata remains distinct from required nonimage attachment failures.

Coverage separately reports inventory/reconciliation, owned body counts, justified exclusions, missing/extra/duplicate IDs, parse errors, container ownership, references/assets, start/end consistency, publication text completeness, attachment completeness and jurisdiction completeness. Start/end signatures are recomputed from retained metadata/TOC bytes rather than trusting success booleans. Completion requires every selected publication to reconcile with stable source metadata, all required nonimage attachments acquired and all encountered images replaced by placeholders, no active limit and a finished run. An incomplete or failed collection exits 2; a scoped complete collection exits 0.

Read-only offline verification recomputes raw hashes, identities, edition bindings, ownership, asset coverage and normalized outputs in a temporary directory. No browser, network or Node is needed:

```sh
python3 -B collectors/municode/verify.py /absolute/existing/henderson --offline
```

`--allow-incomplete` verifies the retained evidence without asserting completion. The default refuses incomplete publications. It never writes into the retained run.

Network-free tests exercise the real orchestrator through a synthetic transport, then prove that missing/duplicated/corrupt/wrong-edition/interrupted source, missing/corrupt assets, limits and identity-mismatched resume cannot pass. A resumed interrupted acquisition must produce byte-identical normalized outputs to an uninterrupted run, reusing the committed bulk response:

```sh
python3 -B collectors/municode/test_faults.py
node collectors/municode/test_transport.cjs
python3 -B collectors/municode/check_fixture.py
python3 -B collectors/municode/verify.py collectors/municode/fixtures/synthetic-complete --offline
```

The synthetic complete fixture is explicitly labeled synthetic, uses a nonexistent fixture jurisdiction and proves mechanics only. The retained fee-table fixture is one actual source-backed provision and proves parser/table behavior only. Neither is live full-publication evidence. Large live raw evidence and outputs stay outside Git under the project's `outputs/full-publication-validation-2026-10-17/municode`. See `validation-summary.json` for exact final execution hashes, scope, counts, proof paths, runtime and limitations. The implementation accepts the 63 mapped Municode targets across the 100-target registry; full ingestion of those 63 targets has not been validated or performed.

The final validation uses `live-henderson-policy-final` in the external evidence directory. Its completeness claim is for the pinned Henderson Code of Ordinances only, with images deliberately omitted as `[IMAGE]`. Earlier `live-henderson-final` and `attempts/henderson-before-explicit-reference-policy` runs each acquired four PNGs before the user clarified the image policy. Those source files remain immutable historical evidence; they are superseded and are not the final collection behavior. `live-henderson-no-images-final` is an intermediate image-free revision retained separately; final code and proof use the policy-final path. The root request and print-root probes show API discovery, not independently qualified final collection.

For optional independent table QA, run `node collectors/municode/table_qa.cjs /absolute/run/publications/PRODUCTID/sections.jsonl /absolute/SEPARATE/table-qa.json`. It sends no network requests and compares every table-bearing normalized HTML record with the parser’s cell text/spans/tag metadata using ordinary headless Chrome. This checks the source-derived, image-sanitized table HTML; it does not transcribe image contents or establish separate-family coverage.

The final tested development invocation uses CPython `/Library/Developer/CommandLineTools/usr/bin/python3` 3.9.6, Node 24.19.0, Playwright 1.62.1 and Google Chrome 155.0.8059.84 on macOS arm64. `NODE`, `PYTHON` and `PLAYWRIGHT_MODULE_ROOT` were set to available local executables/module roots; these are optional environment overrides, not dependencies on Codex. A normal installation uses Python 3.9+, Node 20+, `npm ci` in this component, and installed Chrome. The offline verifier and Python tests need only Python’s standard library and work after relocation.

The final attachment/inline-image hardening revision is newer than the original full live Henderson capture. Collection/browser transport is unchanged. The original exact executed full-run sources remain immutable, and the stronger current verifier reproduces that full run’s outputs without changes because it has zero required nonimage attachments and no inline image data payloads. `final-hardening-single-node-smoke` freshly exercises the current code on the observed image-bearing §15.33.130; it is explicitly a single-node smoke, not a second full publication run. See `validation-summary.json` for the distinct full-run and current portable implementation hashes.

Normalized image omission/reference metadata never duplicates a full inline `data:image` payload. It records MIME, source-string SHA-256, character count and source locator; the original raw source may retain the original URI. Regression tests cover inline picture/srcset/CSS data images and assert the payload is absent from the complete normalized record/coverage JSON.
