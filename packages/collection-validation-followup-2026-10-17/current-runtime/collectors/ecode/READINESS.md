# eCode360 / municipal.codes operator readiness

The live families remain stopped: eCode360 returned HTTP 403 on Albany's first required PDF HEAD, and municipal.codes returned HTTP 429 during Phoenix Charter traversal. This package does not clear stops, retry them, import cookies, accept credentials, or change publisher routes to evade access controls. The readiness evidence is separate from the immutable earlier validation evidence.

Python 3.12+ on POSIX, Beautiful Soup, Playwright, requests and pypdf are required. The exact tested versions are in `requirements-tested.txt`. Live collection additionally requires installed ordinary Google Chrome and a graphical session. Offline tools do not open Chrome or request URLs. Windows has not been qualified; the shared gate uses POSIX `fcntl`.

```sh
python -m venv .venv
.venv/bin/python -m pip install -r collectors/ecode/requirements-tested.txt
.venv/bin/python -m collectors.ecode.cli doctor --url https://ecode360.com/AL0934
```

`doctor` returns 0 only when the requested readiness scope passes and 2 when blocked. With `--source OUT`, the URL must equal the retained configured or resolved publication URL. It checks raw/source snapshot hashes, exact runtime revision, retained errors and read-only status as well as the shared gate. A retained stopped/read-only source cannot become ready merely because a temporary gate file is absent. `transport_gate_clear` is distinct from source resume readiness. An administrator should preserve both existing stop receipts in durable production state before changing gate configuration or restarting a machine; creating a fresh gate is not recovery.

The complete package must include `collectors/registry/access-advisories.json`. Raw collection checks its known workflow stops before importing/starting Chrome, creating output or consulting a fresh temporary gate. `doctor` reports the shipped advisory separately from the physical gate and remains blocked when temporary/home state is absent. Missing or malformed advisory metadata fails closed. Offline replay, verification, file inspection and import do not consult acquisition advisories. There is no CLI reset or override.

The final actual raw proofs and five compact fixtures retain the approved executed parser revision `d83f1c0d…`. The current revision adds the acquisition preflight above and fixes typed opaque image-object metadata. A hash-verified scan found no object/embed tags in any of the 401 Albany or 16 Phoenix artifacts; every other parser/import/verification function is unchanged. See `readiness-advisory-delta.json` and its exact patch. The final 53-case current suite includes the new MIME and startup-tripwire checks.

For these approved historical proofs, `python -m collectors.ecode.tests.verify_frozen --out RUN` validates the shipped approved source hashes, copies only that exact verifier into a temporary package, and disables socket/process operations in the verification child. It exposes verification only. It never runs historical collection or silently upgrades evidence. Ordinary current `cli verify` remains strict about exact source revision; current-source imports/replays use that verifier as usual.

## Legitimate export recovery

The [publisher municipal guide](https://www.generalcode.com/wp-content/uploads/eCode_UserGuide_Municipal_20.pdf) describes selecting chapters or sections and using Download, then PDF or Word. Its [login page](https://www.icccodesolutions.org/request-login/) describes municipal eligibility verification and a public subscription option. Albany's retained page has PDF/Word login flags, but the HTTP 403 does **not** establish missing credentials. A genuine bounded PDF previously succeeded from that same Code. No subscription purchase or account creation has been established as necessary, and neither is performed by this package.

The minimal next action is to obtain restored authorised access from the publisher, or obtain genuine files through the user's authorised publisher UI or independent official publisher delivery. Preserve the original bytes, actual source URLs, acquisition times, selected scope and edition witnesses. Do not save a complete webpage with downloaded image directories; use original publisher downloads or HTML-only source. The script never downloads separate images. Original native files may inherently contain images.

Generate an exact missing-node/document request without network:

```sh
python -m collectors.ecode.cli export-plan --source ./stopped-run --out ./fresh/export-plan
```

This creates a current-source, network-prohibited `retained-proof`, an `export-plan.json` with missing nodes and required document URLs/owners, and `bundle-template.json`. A successful plan is not an acquisition. Do not edit the copied proof or original bytes. Copy the template to a local bundle directory and fill its `files` entries:

```json
{
  "schema": "icc-operator-bundle-1",
  "identity": {"COPY": "the entire exact identity object from the generated template"},
  "genuine_publisher_downloads": true,
  "acquisition_method": "Describe the actual authorised publisher UI or official delivery",
  "files": [
    {
      "path": "downloads/source.html",
      "sha256": "SHA256 of the exact original file",
      "role": "content",
      "source_url": "Exact source URL from the observed inventory",
      "retrieved_at": "2026-10-17T20:30:00+00:00",
      "media_type": "text/html"
    }
  ]
}
```

The example is illustrative, not a completed acquisition or reusable attestation. Use real timestamps with a timezone. Future timestamps, changed editions, unsafe paths, hash mismatches, duplicate role/URL entries and separate images are rejected before import. Supported roles are `content`, municipal `native` HTML for the selected root, required `asset`, `root-end`, and municipal `contents-end`. Save the original root and independent complete contents closing HTML **after all supplied content and documents**. Closing identity and inventory must reconcile with the opening source. An eCode customer alias or explicit municipal root cannot silently migrate to a different Code/UDO during live collection or retained replay.

```sh
python -m collectors.ecode.cli import-bundle \
  --source ./stopped-run --manifest ./bundle/bundle.json --out ./fresh/imported
python -m collectors.ecode.cli verify --out ./fresh/imported
```

For a genuinely supplied structured source bundle with no earlier checkpoint, omit `--source`. Add `config` to the manifest with `url`, `jurisdiction`, `state`, and optional `publication` (plus `family` if desired). Whole eCode source uses the observed customer alias root, for example `https://ecode360.com/AL0934`; a chapter URL cannot stand in for the whole Code. Supply one `root-start` HTML file at the selected root. Municipal.codes additionally requires a separate `contents-start` HTML file at `<selected-root>/contents`. An absolute publication selector must remain on the configured publisher host/family. Opening source must predate all substantive acquisition and establishes identity, edition and inventory; the same content, document and later closing requirements apply. The input attestation is retained verbatim separately from the normalized identity-bound manifest.

```sh
python -m collectors.ecode.cli import-bundle \
  --manifest ./genuine-bundle/bundle.json --out ./fresh/standalone-import
```

This path was qualified with explicitly synthetic complete bundles for both families. It has not been presented as a real full-publication acquisition.

Import is entirely offline. It retains original acquisition snapshots, raw hashes, historical failures and operator manifest provenance, and sets `network_prohibited`. It never clears the shared gate. An actually complete supplied source bundle can return 0 as `operator_supplied_download_bundle`; this is a separately labeled offline proof, not successful live acquisition. Missing nodes, unknown text, conflicting bodies, missing/early closing evidence, limits and required documents keep completeness false. Invalid evidence returns 1; verified incomplete evidence returns 2. A read-only derivative cannot be resumed as a live collection. Exact-version live resume and explicit `--adopt-from` into a fresh folder remain distinct operations.

Imported PDFs need source-backed `identity_terms` describing their document/section scope. Publication identity is automatically added. Both must occur in readable PDF text and retained source context. Format checks require a strict nonempty, unencrypted PDF with pages and closing EOF. Identity is re-extracted during verification. Image-only/scanned or unmatched documents remain unqualified; no OCR or rendering is attempted. Other operator document formats are explicitly unsupported until an appropriate identity adapter is qualified. Existing automatic transport retains separate supported media checks and exact observed source references.

## Inspect an original native file

```sh
python -m collectors.ecode.cli inspect-download \
  --file collectors/ecode/fixtures/readiness-native/albany/publisher-export-0.pdf \
  --witness collectors/ecode/fixtures/readiness-native/albany/source.html \
  --source-url https://ecode360.com/7678220 --identity-term 'When effective' \
  --out ./fresh/albany-native

python -m collectors.ecode.cli inspect-download \
  --file collectors/ecode/fixtures/readiness-native/eugene/publisher-export-0.html \
  --witness collectors/ecode/fixtures/readiness-native/eugene/source.html \
  --source-url https://eugene.municipal.codes/EC/1 --publication EC \
  --out ./fresh/eugene-native
```

Exit 0 means the supplied native file passed inspection; its report still explicitly says `complete=false`. The Albany fixture is one section's one-page publisher PDF, selected from a parent chapter witness. The selected ID must occur in that witness's independent node inventory. The Eugene fixture is Chapter 1 HTML: eight own bodies match the retained page. HTML retains tables and notes and normalizes images to `[IMAGE]`. Only the publisher's observed generated accessibility-name targets and exact history-click UI attributes are ignored for duplicate comparison; legal IDs, text, links, tables/spans and history text remain compared. Original markup and witnesses remain retained.

A whole PDF alone currently does not substitute for the structured HTML inventory/own-node reconciliation. PDF inspection establishes native format and source-backed phrase identity, not provision-level normalization, complete appendices or current edition closure. No complete genuine full-publication native export has been supplied to close that validation gap.

## Offline checks and honest scope

```sh
python -m unittest collectors.ecode.tests.test_faults collectors.ecode.tests.test_operator collectors.ecode.tests.test_native_fixtures collectors.ecode.tests.test_access_advisories -q
python -m collectors.ecode.tests.verify_frozen --out collectors/ecode/fixtures/readiness-synthetic-ecode
python -m collectors.ecode.tests.verify_frozen --out collectors/ecode/fixtures/readiness-synthetic-municipal
python -m collectors.ecode.tests.verify_frozen --out collectors/ecode/fixtures/readiness-operator-ecode
python -m collectors.ecode.tests.verify_frozen --out collectors/ecode/fixtures/readiness-standalone-ecode/proof
python -m collectors.ecode.tests.verify_frozen --out collectors/ecode/fixtures/readiness-standalone-municipal/proof
python -m collectors.ecode.tests.verify_live_fixture --fixture collectors/ecode/fixtures/phoenix-charter-stopped.tar.gz
```

The first five complete fixtures are explicitly synthetic. The standalone fixture directories also include original synthetic `bundle.json` and source files for exercising `import-bundle --manifest FIXTURE/bundle.json --out FRESH` without `--source`. Their fictional laws and synthetic provenance are never real publisher acquisition evidence. The last wrapper explicitly migrates the immutable historical fixture into a temporary current-source offline derivative and expects verified **incomplete** coverage. It does not relabel the stopped acquisition. The 53-test suite includes actual retained native files, malformed/empty/zero-page documents, scope/edition/root mismatches, corruption, duplicate/lost evidence, interruptions, no image fetches, full two-family synthetic imports and historical stop preservation.

The readiness matrix covers local preflight for 30 primary configurations (11 expansion and 19 original-backlog targets) plus 10 secondaries. It is not live full validation of those 40 publications. Current retained Albany source resolves all 3,253 HTML nodes/3,006 records, but six required assets and closing consistency remain unqualified. Phoenix Charter resolves 81 of 279 nodes/73 records, with 198 missing. Both actual publication claims remain incomplete. See `readiness-summary.json` for exact tested revisions, commands, receipts, blockers and required next evidence.

The hyperlink boundary is explicit: retained-source-witnessed `municipal.codes` NY statute namespaces and AZ/ARS, federal USC/CFR/Constitution paths, and the source-witnessed Phoenix same-host `/AZ/ARS/` forwarding links are external statutory references. Their text is outside selected-publication certification. Unknown hosts/namespaces and ambiguous extensionless document links still block attachment completeness. This closes the 10 Albany and 14 Phoenix statutory-reference classifications using retained source, without fetching those references.
