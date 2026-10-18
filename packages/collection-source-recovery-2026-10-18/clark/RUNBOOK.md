# Clark County full Title 30 bundle

This standalone configuration has completed a live full-file collection, all-page normalization, later live closing checks and a separate read-only source verification. It covers the current official Title 30 group: one 352-page code PDF and 29 associated one-page map PDFs. It excludes the separate historical group and does not cover all county law. No Codex/browser runtime is required.

Use the repository's configured Python 3.12 runtime. From the repository root:

```sh
CLARK_PACKET="$PWD/packages/collection-source-recovery-2026-10-18/clark/full30"
COLLECTION_PYTHON="$PWD/.collection-runtime/venv/bin/python"

# Verify delivered bytes and recorded proofs without network or PDF parsing.
"$COLLECTION_PYTHON" -B -S "$CLARK_PACKET/verify_packet.py"

# Run the full standalone collector into a new output directory.
"$COLLECTION_PYTHON" -B "$CLARK_PACKET/runtime/collect.py" \
  --config "$CLARK_PACKET/config.json" --out /data/clark-title30-new

# Reconstruct and verify the new run offline after collection finishes.
"$COLLECTION_PYTHON" -B "$CLARK_PACKET/runtime/verify.py" /data/clark-title30-new
```

Install the shared environment using the [main setup guide](../../../collectors/ops/README.md) before these commands. The package records the exact executed source and installed dependency versions. The live validation used capture-first staging followed by the standard collector's authentic `--from-cache` route; the direct command above uses the same collector and may interleave download and parsing. No bounded limit is supplied. Keep normal publisher gates: a refusal or changed source identity stops the operation and must remain visible.

Exit 0 means the requested `file_pages` level. The tested run has 381 page records and 229 exact `[IMAGE]` markers, all 30 later PDFs matching initial hashes, and an identical later index. It still has 196 detected-cell disagreements, 43 pages with review conditions and unqualified private-use characters on core pages 225 and 226. The 27 source-proven no-text-glyph pages remain image omissions, not transcribed text. Whole legal reading order, table semantics, dependency closure, edition applicability and jurisdiction completeness remain unqualified. Inspect coverage and gap ledgers before using page output as a legal corpus.

The original immutable author README records historical workspace locations. The commands here address the delivered repository paths. The guarded retained-run verifier is `full30/verify_guarded.py`; it reparses the retained `full30/run` and prints its result, so run it with `-B` and redirect output outside the sealed folder. The fast proof command above does not reparse PDFs. Never rerun the historical capture-first driver in the evidence folder.
