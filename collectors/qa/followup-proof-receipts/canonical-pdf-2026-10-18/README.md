# Canonical PDF export and image verification

The current collector correction makes the independently verified STO physical tables and UPOC printed index units authoritative in JSON and CSV. It retains exact prior detector output under `superseded_detector_diagnostics.original_record_fields` rather than discarding failure evidence. `canonical_structure_selection` identifies the selected source representation and source hashes.

The composed source passed 76 family tests. The independent 636-record consumer audit and five corrupt-output cases passed. Seven selected records change; the other 629 records are unchanged. All 795 original failed-cell payloads remain recoverable, with 318 failed cells remaining in canonical output. This is a retained-record derivative with finite native-page queries, not a fresh full-publication collection.

All 201 source image placeholders retain their positions and ownership. The recursive normalized-image audit reports 402 occurrences across text and structured serializations and zero active image markup or inline image payloads. Original publisher documents remain immutable. No separate images are fetched, extracted, decoded, rendered or OCRed.

Source-specific repairs do not resolve the remaining font, edition, source-reference and whole-publication acceptance gaps. Exact source evidence, validation history, test logs and portable verification are in [the canonical PDF package](../../../../packages/collection-canonical-pdf-2026-10-18/README.md). The final integrated acceptance result is recorded separately in this directory.


The final Appendix B composition adds six source-verified pages and passes 81 family tests. Its separate consumer audit and four corruption cases pass; 13 records differ from the original baseline and 623 remain unchanged. All original 795 failures are recoverable: 751 superseded diagnostic cells and 44 remaining canonical failures. The final 636-record image audit again preserves 201 source markers and finds zero active image markup or inline image payloads. See `appendix-independent-consumer.json`, `appendix-consumer-corruptions.json` and `normalized-images-thirteen.json`.


Final integration: all **37 programs and 198 unittest cases passed**, with source snapshot, active source and runtime unchanged. See `SUMMARY.json` and `integrated-acceptance/report.json`. These are regression and source-fidelity checks; actual live acquisition and whole-publication acceptance remain separately evidenced.
