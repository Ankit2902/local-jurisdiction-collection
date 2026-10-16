# eCode360 standalone acquisition results

All 14 previously unqualified primary-code routes passed a bounded fresh headed acquisition and CSV/JSON export. Thirteen also produced an actual selected-section publisher PDF without login. Santa Clara had no available Download control in the tested anonymous publication session.

These are method qualifications, not completed corpora. The PDF samples overlap the 134 DOM provisions; do not count them as additional unique provisions. PDF semantic/layout results are separate in [the download review](publisher-downloads/DOWNLOAD-VALIDATION.json).

| Jurisdiction | Fresh DOM → CSV/JSON | Records | Actual publisher PDF | Publisher edition marker |
|---|---|---:|---|---|
| [Burlingame](https://ecode360.com/44507298) | [Passed](ecode360/publisher-method-exports/burlingame-ca/e2e-result.json) | 1 | [Downloaded](ecode360/headed-live/export-qualification-r4/burlingame-ca/publisher-download-0.pdf) | 2026-04-20 |
| [Emeryville](https://ecode360.com/46989352) | [Passed](ecode360/publisher-method-exports/emeryville-ca/e2e-result.json) | 7 | [Downloaded](ecode360/headed-live/export-qualification-r4/emeryville-ca/publisher-download-0.pdf) | 2026-06-02 |
| [Half Moon Bay](https://ecode360.com/47025425) | [Passed](ecode360/publisher-method-exports/half-moon-bay-ca/e2e-result.json) | 10 | [Downloaded](ecode360/headed-live/export-qualification-r4/half-moon-bay-ca/publisher-download-0.pdf) | 2026-05-05 |
| [Malibu](https://ecode360.com/44331146) | [Passed](ecode360/publisher-method-exports/malibu-ca/e2e-result.json) | 28 | [Downloaded](ecode360/headed-live/export-qualification-r4/malibu-ca/publisher-download-0.pdf) | 2026-06-22 |
| [San Leandro](https://ecode360.com/44065748) | [Passed](ecode360/publisher-method-exports/san-leandro-ca/e2e-result.json) | 1 | [Downloaded](ecode360/headed-live/export-qualification-r4/san-leandro-ca/publisher-download-0.pdf); map review required | 2026-07-20 |
| [Santa Clara](https://ecode360.com/47543489) | [Passed](ecode360/publisher-method-exports/santa-clara-ca/e2e-result.json) | 4 | Download control unavailable | 2026-01-27 |
| [Santa Monica](https://ecode360.com/42718485) | [Passed](ecode360/publisher-method-exports/santa-monica-ca/e2e-result.json) | 9 | [Downloaded](ecode360/headed-live/export-qualification-r4/santa-monica-ca/publisher-download-0.pdf) | 2026-07-28 |
| [Santa Rosa](https://ecode360.com/42952196) | [Passed](ecode360/publisher-method-exports/santa-rosa-ca/e2e-result.json) | 13 | [Downloaded](ecode360/headed-live/export-qualification-r4/santa-rosa-ca/publisher-download-0.pdf) | 2026-09-15 |
| [South San Francisco](https://ecode360.com/43423522) | [Passed](ecode360/headed-exports/south-san-francisco-ca/e2e-result.json) | 8 | [Downloaded](ecode360/headed-live/serial-r4/south-san-francisco-ca/publisher-download-0.pdf) | 2026-09-09 |
| [Sunnyvale](https://ecode360.com/42709867) | [Passed](ecode360/headed-exports/sunnyvale-ca/e2e-result.json) | 8 | [Downloaded](ecode360/headed-live/serial-r4-rest/sunnyvale-ca/publisher-download-0.pdf) | 2026-08-11 |
| [West Hollywood](https://ecode360.com/43902463) | [Passed](ecode360/headed-exports/west-hollywood-ca/e2e-result.json) | 10 | [Downloaded](ecode360/headed-live/serial-r4-rest/west-hollywood-ca/publisher-download-0.pdf) | 2026-06-29 |
| [Tukwila](https://ecode360.com/47209490) | [Passed](ecode360/headed-exports/tukwila-wa/e2e-result.json) | 16 | [Downloaded](ecode360/headed-live/serial-r4-rest/tukwila-wa/publisher-download-0.pdf) | 2026-05-18 |
| [Foster City](https://ecode360.com/51404426) | [Passed](ecode360/publisher-method-exports/foster-city-ca/e2e-result.json) | 7 | [Downloaded](ecode360/headed-live/export-qualification-r4/foster-city-ca/publisher-download-0.pdf) | 2026-01-26 |
| [SeaTac](https://ecode360.com/51196398) | [Passed](ecode360/headed-exports/seatac-wa/e2e-result.json) | 12 | [Downloaded](ecode360/headed-live/serial-r4-rest/seatac-wa/publisher-download-0.pdf) | 2026-09-30 |

The edition column is the publisher’s code-date marker, not a guarantee that every uncodified amendment is included. Customer, code ID and date are retained together in the JSON matrix and receipts. Official city-to-publisher discovery is inherited from the reviewed earlier inventory; this pass did not recrawl every city portal.

## Technical handoff

- [Primary acquisition, parser and export runbook](ecode360/README.md)
- [Actual PDF download, local intake and selected-section parsing](publisher-downloads/README.md)
- [Independent 14-source / 134-provision semantic review](independent-review/REVIEW.json)
- [Runtime and rate-limit guard review](runtime-review/RUNTIME-REVIEW.json)
- [Machine-readable per-city matrix](SOURCE-MATRIX.json)

A full collection still needs publication-wide enumeration, coverage/disposition reconciliation, attachment handling and full-run edition checks. Headless and direct HTTP paths were not requalified.
