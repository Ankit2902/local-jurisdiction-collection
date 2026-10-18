This unpromoted candidate fixes a reproduced native-PDF repeatability failure. The original Arlington TX run captured all61files and closing checks, then failed strict reconciliation. Exact captured8341verification reproduces seven differences only in generated inline-image source_name fields on Charter physical pages52,57,63. Historical failed output remains unchanged. See the sibling arlington-tx-exact-readonly-v2.json and arlington-inline-image-source-cause.json.

PDFMiner creates inline-image names from str(id(stream)). These process-local addresses are not PDF resource names. image_source_name() returns null for an image stream without a real PDF object ID. Existing page/ordinal image IDs and geometry bind these source occurrences. A real named indirect resource, including a numeric source name, remains unchanged. No source-name regex heuristic or cache-comparison waiver is used.

The80-test suite passed. Four separate processes each parsed the same complete71-page native Arlington Charter with sourceSHA b2cf3f57150581560328494e4a59b2bf6bac1ceb05ba87e7940f0f27f4f14360. Baseline A/B differ in seven source_name fields. Candidate A/B JSONL bytes are identical. Baseline-to-candidate changes are exactly the same seven source-proven unnamed-inline references; all legal text, tables, qualifications, geometry, ordering, citations and30[IMAGE] placeholders are unchanged. Source metadata shows each affected stream has no PDF objid; named Im0 references remain intact. Three detected tables retain their original qualifications.

All four actual runs blocked image-stream get_data, bitmap/extract/render, PIL image opening, network and external subprocess APIs. Zero forbidden calls occurred. No image bytes were decoded, extracted, rendered or OCRed. The native original PDF is retained, as authorized; it is not an extracted image. Literal[IMAGE] positions and all available text labels are preserved.

From any working directory, using the existing pinned Python environment:

    python -B /absolute/path/to/study/run_actual_repeatability.py
    python -B /absolute/path/to/study/compare_actual_repeatability.py

The run driver requires fresh baseline-a/b and candidate-a/b output directories. To retain this frozen proof, copy the study to a new directory and remove those four derived directories and process-progress.json only in that new copy before rerunning. The original native PDF, item/config and exact runtime snapshots are included. The runtime needs the unchanged official requirements: beautifulsoup4==4.15.0, pypdf==6.21.1, pypdfium2==5.14.0, pdfplumber==0.11.8. Installed transitive PDFMiner version is in the sibling cause receipt.

Only pdf_structure.py and test_inline_image_identity.py are proposed for production after parent review. The candidate baseline is current f68; earlier qualified whole-word/annotation changes relative to old8341 are not attributed to this new metadata fix. Whole61-file current replay is still required before claiming that Arlington publication is verified. The historical failed run is not repaired or relabeled. Production source is unchanged.
