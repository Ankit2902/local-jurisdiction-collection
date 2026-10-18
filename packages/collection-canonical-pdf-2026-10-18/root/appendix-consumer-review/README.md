# Independent Appendix B consumer check

The auditor compares the actual canonical JSON and CSV against the previous composed 636-record baseline and the delivered source evidence without importing the collector. Run `python3 -B audit.py RECORDS BASELINE CSV NEW_REPORT`, followed by `python3 -B faults.py RECORDS BASELINE CSV NEW_FAULT_REPORT`.

The first report counted all 15 non-table blocks under a field named context_blocks. It passed substantive output checks, but that counter combined nine printed context lines and six printed folios. The final auditor uses the actual source kinds to report those counts separately. The prior script and receipts remain under history; no source or collector output changed.
