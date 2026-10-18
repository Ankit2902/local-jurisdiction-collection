# Finite legacy UPOC font-source diagnosis

This isolated diagnostic is bound only to original172-page PDF SHA877c6e874d4de7873d22dd51443fd5c42169445ad2955db3836841a105a57102 (legacy40thEdition2024). No current42ndEdition text, installed font, alphabet shift, language guess, pixel data, OCR or glyph rendering supplies a character. No PDF or production collector is changed.

The missing-map CID font620 has no ToUnicode/cmap/post. Another embedded original-file Arial-BoldMT instance623 supplies17 finite explicit Unicode cmap witnesses with identical GID, raw glyf bytes and advance/LSB metrics, same font face/version7.0/UPM2048. Italic628→626 supplies13 more. Composite glyphs and non-space empty glyphs are refused. A tempting right-brace candidate is rejected because the target glyph bytes are absent/different.

The30same-glyph mapping witnesses cover3382 actual encoded occurrences. The source operator ledger retains814 original runs and7829 units;4447 units remain unresolved (54 distinct bold CIDs and17 italic CIDs). Every unproven position remains numeric CID plus null Unicode. The102 affected pages are NOT fully decoded or semantically qualified. All795 table-cell disagreements and the40th-vs42nd source conflict remain open.

`decoder_from_original` regenerates the source/font-table proof before returning a diagnostic decoder, then copies validated mappings so caller mutation cannot alter decisions. Ten bounded positive/negative checks pass, including wrongsource/edition, proof/Unicode/glyph mutation, unknown fonts, odd bytes, an unresolved ligature and postvalidation mutation. A separate full operator-ledger check reproduces3382known/4447unknown units.

Only original page content/font resources and embedded font tables were read. All172 page text streams were scanned, with no Form XObjects or ActualText replacements found in these runs. No image stream was decoded, rendered, extracted or passed to OCR; network/image API tripwires remained silent. This is a finite candidate/diagnostic, not a production parser promotion or complete legal transcription.
