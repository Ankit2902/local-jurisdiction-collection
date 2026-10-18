# Extraction package contract

This is the proposed delivery contract for the technical team. The 16-column corpus shape is existing project convention; the source-node and provenance sidecars below make full-source reconciliation explicit without changing that legacy interface.

## Directory and artifact requirements

Deliver one directory per jurisdiction, with one subdirectory per publication family. Keep original source snapshots immutable and separate from parsed outputs.

```text
jurisdiction/
  run-manifest.json
  publications.json
  source-nodes.jsonl
  node-dispositions.jsonl
  record-provenance.jsonl
  validation-report.json
  exceptions.jsonl
  raw/
  publications/<publication-id>/
    toc.json
    toc.csv
    fulltext.json
    fulltext.csv
  aggregate-toc.json
  aggregate-toc.csv
  aggregate-fulltext.json
  aggregate-fulltext.csv
```

`publications.json` records every discovered family with official title, root, stable identity, scope decision/evidence and publication currency. A newly discovered Charter or handbook must receive an explicit disposition. Existing exclusions for another jurisdiction do not transfer automatically. Non-code references and uncodified ordinances may be inventoried without entering codified full text.

`run-manifest.json` records jurisdiction, adapter/version or code commit, configuration hash, start/end retrieval times, official routing evidence, publication versions, artifact hashes, record counts, retry/failure counts, inventory counts and completion status. Paths should be relative to the delivered package. Preserve raw publisher currency text separately from normalized date and precision. Retrieval time, commit date and last-updated labels must not be silently treated as legal current-through dates.

## Existing corpus output fields

Use these fields in this order in the CSV and in each `provisions` object of the JSON envelope:

```text
jurisdiction, code_name, division, title, subtitle, chapter, subchapter,
article, part, subpart, section_number, section_name, citation, full_text,
source_url, scrape_date
```

JSON uses `{"metadata": {...}, "provisions": [...]}`. CSV is UTF-8 with BOM and proper quoting for embedded line breaks/quotes. Validate row-for-row CSV/JSON equality. The compatibility TOC files retain the same record identities/order with blank `full_text`. That derived TOC is distinct from the independent source inventory and cannot prove that nothing was missed.

Preserve the publisher's displayed citation/heading in `citation` at the extraction stage, with source-backed locators. Do not fabricate Bluebook normalization, renumber repeated designations or treat blank numbering on an unnumbered operative body as grounds to discard it. Carry normalization and special identity decisions in sidecars for the downstream team.

## Source inventory and disposition

Recommended source-node fields:

```json
{
  "jurisdiction_slug": "example-ca",
  "publication_id": "municipal-code",
  "source_version": "publisher-version-or-manifest-reference",
  "node_id": "observed-publisher-node-id",
  "parent_node_id": "observed-parent-id",
  "source_order": 17,
  "node_kind": "section",
  "display_number": "1.01.010",
  "display_heading": "Adoption.",
  "source_url": "https://publisher.example/observed-node",
  "raw_artifact_path": "raw/observed-artifact.html",
  "raw_sha256": "computed-sha256",
  "locator": {"kind": "html-id", "value": "observed-id"}
}
```

These values are illustrative, not runnable source identifiers. Use a stable publisher node ID when supplied. Otherwise use the retained document identity plus a source-backed anchor/XML path/PDF page-and-heading locator; document any locally assigned identifier. Do not infer uniqueness from printed section numbers.

Every source node receives exactly one disposition record, with emitted record IDs where relevant:

- `included`: substantive content represented in one or more output records.
- `structural`: navigation/heading with no independent operative body; retain descendant relationships.
- `reserved_or_repealed`: source-backed status; retain status text or explicit disposition as appropriate.
- `editorial_reference`: nonoperative index/preface/reference; classification supported by source inspection.
- `excluded_by_scope`: explicit applicable scope decision and evidence.
- `unresolved`: failed acquisition, uncertain identity, missing body or unresolved parsing issue.

A node can contain its own operative text as well as children. Classifying it as a container is not sufficient to exclude that text. A duplicate fetch of one node is distinct from two source nodes carrying the same printed designation.

`record-provenance.jsonl` maps each output record ID to its publication/node IDs, acquisition artifact hash, source locator, extraction version and any recovery/normalization evidence. Preserve ordering and origin for composite recoveries. Separate versions or supplemental sources require record-level bindings.

## Content fidelity

Retain structured source HTML/XML and render legal text into the established corpus-compatible representation, preserving paragraph/list/table structure. Maintain table headers, cell order, row/column spans, nested enumeration, footnotes, superscript/subscript and cross-reference text. Use ordered `[IMAGE]` placeholders under current project convention; a placeholder does not replace the readable text of a diagram or scanned legal page. Preserve visible semantic labels and record illegible transcription as unresolved/reviewed evidence where appropriate.

For PDFs, retain page count, page boundaries, text coordinates and OCR metadata as applicable. A continuous legal paragraph split over pages must remain one logical section. Running page headers and revision dates must not become legal section identities. Verify visual reading order for multicolumn pages and tables.

## Completion criteria

A jurisdiction is ready for downstream use only when:

1. Every discovered publication has an evidenced scope disposition, and every in-scope source node has a disposition.
2. No unresolved substantive text, source version or identity issue remains. Reserved/editorial/scope exclusions are explicit, not missing data hidden by successful row counts.
3. The node inventory independently reconciles to included records and dispositions. Counts of downloaded pages, parsed rows and legal sections are reported as different units.
4. There are no unexplained navigation/error/verification pages in output, no unexpected character-decoding defects, and no unexplained truncated sections.
5. Source-sensitive examples pass: long sections, tables, nested lists, images, amendments/history, unnumbered parent bodies, appendices, repeated printed locators and any source-specific numbering variants.
6. CSV/JSON/TOC representations agree, hashes verify, publication families remain separate, and source URLs/locators resolve within retained evidence.
7. A clean replay and interrupted/resumed replay from the same source snapshot produce equivalent ordered records and dispositions, excluding explicitly volatile run metadata. Repeated collection does not duplicate records.
8. The validation report distinguishes automated checks from human source comparisons, records their coverage and includes any accepted exceptions with evidence.

A successful HTTP response, zero blank exported rows, or the historic collector readiness report is not a substitute for these criteria. A document/page that yields zero records requires an explicit source-based disposition before completion.
