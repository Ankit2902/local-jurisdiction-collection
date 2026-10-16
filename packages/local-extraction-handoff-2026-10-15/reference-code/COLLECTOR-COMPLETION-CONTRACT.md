# Full-collector completion contract

A jurisdiction is ready for batch wiring only when its provider collector can:

1. Write a TOC CSV and JSON plus a full-text CSV and JSON using the existing
   16-column municipal schema.
2. Preserve each provision's source URL, hierarchy, section number/name, and
   scrape date; retain provider-specific IDs/current-through data in the run
   manifest.
3. Cache source responses and resume an interrupted run without re-fetching
   completed pages.
4. Respect the source's approved access path: direct API, bulk data, official
   PDF, first-party HTML, or browser-rendered transport.
5. Execute a bounded live sample (at least one TOC branch and its leaf text)
   and record output counts, sample URLs, failures, and source currency in
   `collector-completion/<slug>.json`.
6. Pass its parser/fixture tests and a schema check over the produced sample
   outputs.

Validation manifests prove that a source is reachable and parseable; collector
completion manifests prove that an actual TOC/full-text collection path works.
