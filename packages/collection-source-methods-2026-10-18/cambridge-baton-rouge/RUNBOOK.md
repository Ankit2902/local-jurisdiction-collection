This isolated source-specific packet covers three observed official routes. It contains no production or registry changes and no database work.

The Baton Rouge UDC configuration selects exactly the visible Chapters and Appendices widgets: nineteen chapters and eleven appendices, including the two Reserved appendices. It does not treat PDFs as legal sections. Seven unlinked document identifiers in widget metadata remain unresolved: four in Chapters, two in Appendices and one in the section visibly titled “Draft Ordinances (none).” No URL has been invented for those identifiers. The selected thirty-file scope does not establish all applicable law, edition completeness or the legal meaning of detected tables.

Cambridge's base ordinance has 23 observed article routes and an entire-ordinance/supplement PDF ZIP archive on Municode. The official site also lists17 map PDFs, five adopted-but-not-yet-codified amendment rows and121 codified rows, with476 distinct PDF links in supporting records. The source says the print ordinance and subsequent amendments control, not all ordinances are electronically available, and its petition-document lists are incomplete. The five current final ordinance routes go to the stopped publisher. Neither the archive nor any publisher link was requested. No map or supporting-record bulk acquisition was attempted.

Baton Rouge's general Code of Ordinances page points to the literal legacy URL http://library.municode.com/index.aspx?clientId=10107. That destination was not requested. Its source expressly says many ordinances and resolutions are outside the code. The observed locator is retained verbatim; its query parameter is not reinterpreted as an API identity.

The durable Municode workflow stop remains active. It is not evidence that every individual publisher route is unavailable. There is no retry, reset, alternate transport or bypass in these scripts.

Use Python3.12.14 and the exact tested dependency versions recorded in runtime-environment.json. The supplied runtime/ is a byte-for-byte copy of the reviewed official family modules. A new owned virtual environment can install the pinned dependencies in requirements-standalone.txt; no browser or Codex/CUA integration is needed for these HTTP/PDF routes.

The actual staged workflow is:
1. scripts/discover.py acquired the three official HTML pages once through the existing shared host gate. scripts/linked_discovery.py acquired only the two observed official Cambridge context pages and header-only native-size metadata.
2. scripts/source_inventory.py and scripts/cambridge_routes.py derive the inventories offline. scripts/test_discovery.py runs the actual-source refusal/selector tests without requesting any links.
3. scripts/size_inventory.py performs one HEAD per selected native PDF, reusing the recorded first header receipt without another request. It reads no response body and stops on a refusal.
4. scripts/capture_native.py obtains the thirty original PDFs using the unchanged reviewed collect.fetch_raw and the existing shared gate. It checks PDF magic and counts pages via native page-tree metadata only; no text/table parse or image access occurs in that stage. Its checkpoint is explicitly capture-only, not a collector completion or common job.
5. scripts/run_collection.py invokes the unchanged standard collect.collect with --from-cache semantics, which imports only successful source-bound raw receipts, obtains fresh discovery, parses all selected pages, and obtains actual later source/file responses. This is not an artificial interrupted/resumed job.
6. Prepared, NOT EXECUTED at the user-requested stopping point: scripts/verify_guarded.py runs the standard family reconcile with network and pixel API tripwires and complete before/after evidence and runtime hashes.

All scripts suppress bytecode before local imports. The live helper refuses cross-host redirects before a follow-up request. The reviewed transport normalizes image MIME before reading bodies. Native PDFs may intrinsically contain images; no separate image is downloaded and no image bytes are extracted, decoded, rendered or OCRed. Normalized images are exact [IMAGE], retaining available source text and metadata.

Discovery/capture files are durable evidence. These scripts intentionally refuse overwriting an existing attempt rather than automatically retrying it. To run a separately authorized new collection from this configuration in an empty directory, the unchanged family CLI is:
    /path/to/python3.12 -B runtime/collect.py --config configs/brla-udc-current-visible-documents.json --out /absolute/NEW-EMPTY-OUTPUT

The standard family verification command for that new directory is:
    /path/to/python3.12 -B runtime/verify.py /absolute/NEW-EMPTY-OUTPUT

A successful requested file_pages result is a source file/page result. Legal-semantic, table/order, dependency, edition, all-county-law and jurisdiction qualifications remain separate. Read the actual final coverage and verification receipts; no current common-launcher pass or sixteen-field corpus export is asserted here.

Stopping-point status: the standard producer terminated0 at2026-10-18T04:43:54.282207+00:00 after its own cached reconcile. No separate guarded read-only verifier or common launcher run was started. User instructed no further jobs/acquisition. The normalized-image audit already passed all606 records and its exact record hash remains the final hash. Capture-only binary audit passed64files; a final run-wide signature/MIME audit was not started. Remaining validation is listed in STOPPING-STATUS.json. No work remains live.
