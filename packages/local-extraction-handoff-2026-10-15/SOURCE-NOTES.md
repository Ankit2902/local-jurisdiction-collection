# Source notes

Prepared October 15, 2026. The 30 routes and samples come from the reviewed municipal-code-batch registries and collector manifests, generally dated August 28, 2026. Discovery URLs are starting points to reconfirm, not asserted current publication snapshots.

Live spot checks on October 15 confirmed that [San Mateo](https://law.cityofsanmateo.org/) directs users to its official bulk HTML/XML repositories, [Rockland](https://www.rocklandmaine.gov/288/Charter-Code-Ordinances) lists 20 chapters plus a Charter, and [King County](https://kingcounty.gov/en/dept/council/governance-leadership/county-legislation-codes/king-county-code) exposes first-party HTML with PDF/Word alternatives and a separate Charter. No full code was collected for this handoff.

`reference-code/` is a dated snapshot of existing project code for review. The Python parsers require the dependencies in its requirements file; network/browser orchestration also depends on the original project layout and the shared legal-code-batch transport. That transport and the complete existing fixture tree are not bundled. Run the original regression suite in a full checkout; the standalone probes in this handoff use synthetic fixtures and do not require that checkout. Some reference modules concern jurisdictions already completed and are included only to preserve internal imports. Only the 30 entries in routes.json are the extraction scope.

The production 16-column format and existing scope policy come from citizens-static-corpus-execution. Preserve publication-specific exclusions only where a recorded decision actually applies. Existing exclusions for other jurisdictions do not automatically apply to these 30.

No database work or ordinance-update collection is part of this handoff.
