# Solid-waste dependency discovery and exact retained-source binding

This packet identifies both legal dependencies named in the exact six-page Overland Park administrative document. It changes no production/shared runtime/registry/Git files, creates no AL/enCodePlus publisher requests, and does not promote the prior source-specific logical profile to whole-publication acceptance.

## Chapter 7.36: existing acquired corpus can be reused

The fresh retained source is `outputs/collection-readiness-next-2026-10-17/encodeplus/post-91f6c59/overland-primary-unified-v1`, captured 2026-10-18 UTC. It has 6,279 normalized records. The relevant owned chapter consists of **40 units**: container ID **1578** plus **39** operative/descriptive child units. The exact unit IDs, headings, original record rows, raw/body hashes, source URLs, and owned text are retained in `retained-chapter-binding/`.

The raw source is Title 7 request `doc-view.aspx?secid=1296&ajax=0`. Its start and end source SHA-256 both equal `86a82081a96d048cf3a3ebb28ff67322fe61942b80bd53302fa7dbe7d8683999`. Membership is explicitly represented by publisher body class ancestry `_007-010` across sibling sections. It is not inferred from physical nested DOM or citation prefix alone. The similarly numbered owner **1567** belongs to a different source parent and is excluded.

Two exact reciprocal witnesses establish the connection to the six-page document:

- **1586**, 7.36.100.105, defines Administrative Regulations and directly links UUID `68642c1d-ce7d-4ab0-a9e3-cf56d6def79a`.
- **1612**, 7.36.105, describes adoption/administration and incorporates those regulations; its links use the same UUID.

The fresh capture's actual linked native asset has SHA-256 `1af70bb8170cf2701cfb9e7ede2b274bf848309ca6fcaa3b7a7eeba9cd426c39`, exactly the source used by the full-six-page logical candidate. The source bytes and original asset receipt are copied here for offline binding.

This supports reuse of the retained **publisher-linked snapshot graph**, without re-requesting the chapter or substituting a different file. It does **not** establish that the 2026 chapter text is the version applicable to the printed-2011 administrative source. Seven chapter units contain amendment histories after 2011, including 2021/2023. The publisher edition identifier is null; its version pin is an observed snapshot of source hashes. `reusable_as_2011_edition_equivalent` remains false.

## County identity and genuine official bytes

Owned section **1593**, 7.36.100.155, explicitly names **Johnson County, Kansas** and the **Johnson County Code of Regulations for Solid Waste Management, 2010 Edition**, as amended. Its source history identifies Ord. SW-2927 §7, 2011. Thus neither the county identity nor the named publication is guessed from geography.

The official county [Solid Waste Management Plan landing page](https://www.jocogov.org/department/environment/solid-waste/solid-waste-management-plan) provides a separately named code link under Solid Waste Management Code. The link was followed exactly as observed, to the [official county PDF](https://www.jocogov.org/sites/default/files/files/2021-09/dhe-solid-waste-code-as-adopted-by-BOCC-10-7-10-revised-by-BOCC-12-11-14.pdf). These were **two serial direct public GETs through the existing official host gate**, both HTTP 200. The captured PDF is **1,593,746 bytes / 43 pages**, SHA-256 `17a96ce506109a96f8a2c432fe97f9b7c78443bc15a433861da9456b73000193`. Raw bytes and request/response metadata are in `raw/`; `official-link-binding.json` preserves the actual anchor and resolved URL.

The cover identifies the Environmental Department and an official copy incorporated by Resolution **068-10**, **amended by Resolution 074-14**. It is a real named-publication candidate, but explicitly contains a later amendment. No unamended 2010/2011 equivalence is claimed. The PDF's metadata includes a 2015 creation date and 2021 Paper Capture producer/modification metadata; these are retained as source metadata, not represented as adoption dates. Existing source text was inspected on the cover. No new OCR, rasterization, image extraction, or image decoding was performed. Whole-43-page legal text, tables, and reading order are **not qualified** by this discovery packet.

Before direct requests, the exact `www.jocogov.org`, `jocogov.org`, `www.opkansas.org`, and `opkansas.org` official/enCodePlus host-state locations were inspected. No matching existing stop was present; the official-source owner also reported no known exact-host refusal. Unrelated persisted stops were left untouched. `host-state-before.json` records the preflight. The web-tool discovery files are labelled discovery only; the later direct raw receipts are the acquisition evidence.

## Next source-supported strategy

1. Reuse the exact existing Chapter 1578 subtree and the recorded reciprocal UUID/native SHA as a versioned dependency edge. Preserve the original corpus identity, source hashes, per-owner body hashes, snapshot date, and the observed edition-ID limitation. Do not flatten the whole chapter into the six-page document's body or duplicate its text into that profile.
2. Add the newly acquired county PDF as a separately identified **2010 edition amended 2014** candidate with the official landing/anchor/cover witnesses. Qualify its full native text/structure independently before setting semantic completeness. A StructTreeRoot exists, but that fact alone does not qualify its semantics.
3. To establish the historically applicable county text, obtain the official adopting Resolution 068-10 and its original Exhibit A, then compare the original version with amendment Resolution 074-14 and any intervening enactments relevant to the required date. This packet has no observed official URL for the unamended exhibit, so no path or substitute is invented. County/City official-copy records may be required; no messages have been sent to any person.
4. Establish the administrative document's actual adoption/currentness separately. Its literal 2011 date and blank proposed date remain unchanged. Current HTML's continuing link to the same PDF proves publisher linkage; it does not by itself resolve historical or current legal edition equivalence.

The complete legal-dependency closure remains false. This packet materially resolves target identity, current retained-corpus reuse, and actual native-file discovery/acquisition; it does not waive version, legal-structure, or transitive-dependency gaps.

## Offline commands and provenance

From this packet directory:

```sh
python source/verify.py
python source/test_discovery.py
```

The verifier recomputes chapter ownership membership, raw start/end hashes, reciprocal native bytes, county cover identity and source receipt/link integrity. The eight tests also reject a historical-edition waiver, false county semantic pass, wrong file hash, missing middle owner, wrong native identity, and HTTP failure promoted as success. Socket, image-opening, and image-stream decoding tripwires remain untouched.

`source/bind_retained.py --retained ORIGINAL_RUN --out FRESH_DIR` recomputes the retained chapter binding without network. Its earlier physical-DOM-only and body-hash-field assumptions failed safely; those trials are retained. The final binding uses the actual publisher class ancestry and the record's documented owned-HTML hash.

`source/acquire_county.py` is a recorded narrow acquisition helper, not the offline verification command. It refuses an existing capture before any network or gate operation. The exact version that executed the two live requests is retained in `executed-acquisition-source/` and bound by `county-acquisition.json`; the only later helper change added the early existing-output refusal. `acquisition-source-lineage.json` makes that difference explicit. No fresh acquisition is attributed to the later guard-only revision.

Tested Python 3.12.14 on macOS 26.6.2 arm64; beautifulsoup4 4.15.0 and pypdf 6.21.1. The test tripwires use installed Pillow 11.3.0. No browser or image binaries are required. Original source PDF/HTML may contain embedded imagery; the scripts never separately request, extract, decode, render, or OCR it. Normalized images remain governed by the literal `[IMAGE]` policy.
