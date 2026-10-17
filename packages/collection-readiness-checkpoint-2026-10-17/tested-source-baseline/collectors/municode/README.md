Current readiness work is in progress under `outputs/collection-readiness-2026-10-17/municode`; the prior `ebe1edb` delivery and its evidence remain sealed. The current queue contains 63 primary configurations, 24 qualified secondaries and the source-qualified Daly City original target (88 publication configurations). Configuration coverage is not a claim that all 88 publications have passed live validation. Each batch status records source-bound full acquisition and read-only verification separately, with pending and incomplete entries explicit.

Use the root operations setup/launcher or install Python 3.12 requirements and the locked Node dependencies, then run `python collectors/municode/runtime.py` to check the resolved Python, real PDF parser, Node and Playwright before issuing requests. Node 20+ and ordinary installed Chrome are required. `NODE` selects Node, `PYTHON` selects the gate interpreter, and either normal local `npm ci` resolution, `NODE_PATH` or `PLAYWRIGHT_MODULE_ROOT` can supply Playwright. No Codex-specific runtime path is required.

Full serial queue, from repository root:

```sh
python collectors/municode/batch.py \
  --registry collectors/registry/publications.json \
  --additional-registry collectors/registry/original-publications.json \
  --scope all --out /absolute/FRESH/municode-batch
```

Add `--resume` for an interrupted batch using exactly the same sources/configuration. Each publication has a durable own output directory, stdout/stderr and an offline verification report. Finished whole publications are skipped. `--retry-incomplete` or `--retry-publication ID` explicitly selects an incomplete attempt; these never clear access stops. A code or source-policy change stops dispatch at the next publication boundary. Start a fresh batch with `--previous-batch /absolute/earlier/status.json`; same-client/product complete live proofs are reused only after the stronger current verifier succeeds and the reference policy still matches. Incomplete earlier attempts remain incomplete and retain their provenance. Keep referenced batch directories together when relocating.

Exact source-backed product policies live under `policies/product-PRODUCTID.json` and are automatically loaded for an explicit single-product collection. They identify separately published sibling books or clearly reference-only links from observed source text. They cannot exempt obvious embedded/file attachments. An unknown external link remains unresolved rather than being silently discarded.

The gate distinguishes an external required-document host refusal from a publisher refusal: the external host receives a persistent host stop and the document stays failed; a Municode publisher challenge/403/429 stops the whole publisher queue. Existing direct-HTTP stops remain untouched. Unknown binary MIME stays blocked; observed nonimage filenames such as a publisher `.pdf` may use `application/octet-stream`, with subsequent real-parser validation mandatory. Known image URLs and image MIME never trigger a body download.

This is an unbounded, resumable collector for whole Municode publisher publications. It dynamically inventories the client's visible CODES publications and pins each selected product, latest job and complete TOC. It preserves every returned document's own body, including container preambles and front matter, instead of selecting section-shaped leaves. A whole publisher publication is a distinct scope from a whole jurisdiction: `jurisdiction_complete` always remains false because separately hosted code families, uncodified ordinances and incorporated external standards are outside the selected book.

The normal publisher Print workflow supplies the bulk route: `GET /api/CodesContent/docIds` with product, job and selected root document IDs. Selecting a publication root expands its owned chunks and descendants. The collector reconciles that response against every pinned TOC ID. It makes conservative missing-ID batch requests when needed; unexpected IDs, duplicate ownership, unexplained empty leaves, unhandled document types and source changes prevent completion. A separate landing-page request supports the one narrowly justified root exclusion: the TOC root is structural and its own source response is an empty DocType4 publication landing page. No arbitrary structural exclusions are accepted.

The current readiness runtime is Python 3.12 with pinned `pypdf==6.21.1` from `requirements.txt`. PDF qualification uses the real strict parser, not header checks. The root operations launcher owns reproducible environment setup; direct invocation runs a network-free preflight before acquisition. Node 20+, Playwright 1.62.1 or 1.64.0 and ordinary installed Google Chrome are accepted for live collection. The locked npm installation remains 1.62.1. Root operations may transparently expose the official Python Playwright 1.64.0 bundled core (exact build `1.64.0-beta-1791568591000`); its alias must report the exact underlying official core version. Python Playwright does not publish 1.62.1, so the npm version must not be blindly reused as a pip pin. Version 1.64.0 and its exact bundled core build are separately accepted by preflight. The root unified launcher completed a fresh full Henderson run (`ops/live-henderson-unified-v3`) with actual Python Playwright 1.64.0, official core 1.64.0-beta-1791568591000 and Node 24.21.0; all 2,122 records, closing metadata, family verification and selected-scope verification passed. The prior v2 failure is retained: default product policy filename wiring was absent, then fixed using the exact already qualified source-backed policy. `package-lock.json` pins the Node dependency graph. The shared gate uses POSIX `fcntl`, so macOS/Linux are supported; Windows portability is not claimed.

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

Required **nonimage** file links and recursively referenced nonimage CSS dependencies are inventoried and acquired separately. Responses retain bytes, URLs, redirect hops, hashes and status; qualification is format-aware and fails closed. Empty/truncated PDF bodies fail; a plausible PDF header/trailer alone fails. A valid PDF must pass pinned pypdf strict catalog, cross-reference, all-object, physical-page and content-stream checks. Image streams are not decoded or extracted. A failed or unavailable parser prevents attachment/publication completeness. ZIP-family files require a valid central directory and every member CRC; Office ZIP containers also require their content-type manifest. Plain UTF-8 text/CSS/CSV and JSON receive explicit decoding/type checks. Other binary formats remain unqualified. These checks make no legal-semantic assertion. Missing, blocked or invalid required nonimage attachments prevent attachment/publication completeness. Intentional image omissions do not block completeness and do not claim transcription of image contents. Unknown ordinary external hyperlinks remain unresolved by default, protecting extensionless appendices from silent exclusion. An explicit reference policy can classify an ordinary hyperlink as a separately hosted family boundary or reference-only link with a nonempty, source-backed reason and optional owner IDs. A policy cannot exempt embedded media or obvious file/document links. The supplied Henderson policy applies only to the publisher's Title 19 zoning pointer, whose body explicitly redirects to the official development-code revisions webpage; that separately hosted code is not collected. Its owned pointer text is retained, and jurisdiction completeness remains false.

Outputs are `checkpoint.json`, raw response bodies and receipts, runtime sessions, exact executed sources, top-level `coverage.json`, and per-product `publications/PRODUCTID/{sections.jsonl,sections.csv,coverage.json}`. Record units are publisher-owned documents/chunks, including containers, headings, front matter, tables and leaf provisions; they are not uniformly legal sections. Records retain stable IDs, heading/path, parent, product/job, text, image-free normalized HTML, the original body hash and normalized HTML hash, tables/spans, links and their source attributes, notes and footnotes. Container bodies remain owned by their source DocID; descendant records are not concatenated into parents or duplicated. Identical wording under distinct genuine source IDs is preserved. An image-only source body becomes `[IMAGE]`, retains its source ID/heading and remains a record. Original raw API source bytes retain provenance; normalized HTML has no active image tags or image fetches. Image omission metadata remains distinct from required nonimage attachment failures.

Coverage separately reports inventory/reconciliation, owned body counts, justified exclusions, missing/extra/duplicate IDs, parse errors, container ownership, references/assets, start/end consistency, publication text completeness, attachment completeness and jurisdiction completeness. Start/end signatures are recomputed from retained metadata/TOC bytes rather than trusting success booleans. Completion requires every selected publication to reconcile with stable source metadata, all required nonimage attachments acquired and all encountered images replaced by placeholders, no active limit and a finished run. An incomplete or failed collection exits 2; a scoped complete collection exits 0.

Read-only offline verification recomputes raw hashes, identities, edition bindings, ownership, asset coverage and normalized outputs in a temporary directory. No browser, network or Node is needed for offline verification; install the pinned Python requirements when PDFs are present:

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

The synthetic complete fixture is explicitly labeled synthetic, uses a nonexistent fixture jurisdiction and proves mechanics only. The retained fee-table fixture is one actual source-backed provision and proves parser/table behavior only. Neither is live full-publication evidence. Current large live evidence stays outside Git under `outputs/collection-readiness-2026-10-17/municode`. Previous `full-publication-validation-2026-10-17` evidence is immutable historical proof and is not silently reused as a new readiness run.

The current tested runtime is CPython 3.12.14 at `/tmp/full-publication-review-venv/bin/python`, pypdf 6.21.1, Node 24.19.0, Playwright 1.62.1 and Google Chrome 155.0.8059.84 on macOS arm64. A normal installation uses Python 3.12, `pip install -r collectors/municode/requirements.txt`, Node 20+, `npm ci` in this component and installed Chrome. The absolute development executable locations are recorded for reproducibility; the scripts accept normal installed runtimes through the environment described above. Offline verification needs Python and the pinned PDF dependency, without Node or browser access.

Current live progress is a checkpoint rather than a final seal. `validation-summary.json` records the observed batch phase, every configured publication status, counts, source identity, original child implementation hashes and whether every retained executed-source snapshot matches its hash. Different child revisions are explicit: a later verifier does not rewrite the original acquisition revision. Rebuild a progress snapshot without changing the batch or evidence:

```sh
python collectors/municode/checkpoint_report.py \
  --batch /absolute/collection-readiness-2026-10-17/municode/batch-005 \
  --evidence-root /absolute/collection-readiness-2026-10-17 \
  --out /absolute/SEPARATE/progress.json
```

The active queue is publication-wide and has no item limit. Per-publication completeness remains independent of the queue's completion. Empty operative bodies, unknown types and unexplained ownership prevent a complete claim even when every source ID was retrieved. Source-backed gaps are retained for review and later explicit retry, and do not disappear because a bulk endpoint returned HTTP 200. Source Notes are recursively sanitized with image omission source-field locators and a source hash. Note-owned nonimage hyperlinks enter the same required-attachment ledger; note prose is retained. Unexplained empty bodies do not suppress closing edition metadata. `--allow-incomplete` accepts retained evidence with those explicitly reported empty-body defects only, while refusing identity, unknown-type and ownership errors; it never promotes them to complete.

Current incomplete source cases include the San Antonio Unified Development Code's empty bodies and Nashville Charter's three empty Article labels. An independently acquired same-job Charter PDF corroborates those exact Article labels followed immediately by separately owned Chapter/Section text, but the existing Charter attempt remains incomplete pending explicit source-bound handling and closing consistency checks. No generic Article/Chapter waiver is used.

For a separately qualified native export, run:

```sh
python collectors/municode/export.py \
  --reference-run /absolute/source-bound/publication-run \
  --product-id PRODUCTID --out /absolute/FRESH/native-export
```

This follows observed ClientContent download eligibility and the publisher's PublicationPdfDownload route, pins the live latest job to the reference run, downloads the complete native file through the same browser gate and invokes the real strict PDF parser. Page text layers and explicit image-resource placeholders are retained without image extraction. Native-file integrity is distinct from segmented publication text, end-of-run edition consistency, source-to-PDF body parity and jurisdiction completeness; the export receipt keeps those unproved claims false. The fresh Nashville Charter native file is a 230-page complete native PDF. The fresh San Antonio Unified Development Code native file is 44.8 MB and 2,028 pages. Both passed strict pypdf integrity; neither promotes its incomplete structured publication run. The UDC PDF identifies Supplement 24 (March 2026), while current API job 495185 identifies Supplement 25 Update 1. That edition mismatch is explicit: latest-job metadata and the download URL did not establish native-file edition alignment. It cannot justify current API empty-body exemptions.

For optional table QA, `node collectors/municode/table_qa.cjs /absolute/run/publications/PRODUCTID/sections.jsonl /absolute/SEPARATE/table-qa.json` checks normalized HTML versus serialized table metadata with all network blocked. That is serialization consistency. The independent root QA helper `collectors/qa/municode_raw_tables.cjs RUN FRESH_REPORT` binds the original committed API Docs.Content bytes to product/job/node/hash and compares source DOM cells with normalized tables. A source with no tables is explicitly not applicable rather than a table-fidelity pass. Current source-table reports live separately under `outputs/collection-readiness-2026-10-17/qa/tables`.

Normalized image omission/reference metadata never duplicates a full inline `data:image` payload. It records MIME, source-string SHA-256, character count and source locator; only original raw source may retain the original URI. Regression tests inspect the complete normalized record/coverage JSON for inline picture/srcset/CSS payload leakage, and check that background-image placeholders remain inside their owning table cells, including nested cells. The transport regression executes the actual browser module with a synthetic transport and verifies zero known-image requests, HEAD-only extensionless-image detection, normal nonimage HEAD/GET, external-host stop separation and preserved security resources.

Network-free auxiliary checks are also runnable directly:

```sh
python collectors/municode/test_batch.py
python collectors/municode/test_gate.py
```

`qa-results.json` records current executed commands and hashes. `MANIFEST.json` covers this component's checkpoint files, excluding itself, runtime caches and local dependencies. External active run files are not sealed by that component manifest. The overall goal remains active until all configured publications have explicit final evidence and outstanding source/attachment gaps are resolved or candidly blocked.
