# Image handling policy

The user reaffirmed the existing corpus convention on October 17, 2026: **do not collect image assets; replace all images with the exact literal `[IMAGE]`**. This instruction governs the final collectors and overrides the earlier implementation-stage requirement to download images.

The original [output contract](../packages/local-extraction-handoff-2026-10-15/OUTPUT-CONTRACT.md#content-fidelity) already specifies ordered `[IMAGE]` placeholders. The current instruction makes the acquisition exclusion explicit.

- Do not request, download, extract, render, OCR, or save separate image binaries as collection output. Ordinary browser image resources are blocked where the browser workflow supports that without changing access/challenge controls.
- Replace source images in normalized text and HTML with `[IMAGE]` in source order. Handle ordinary images, picture/source alternatives, inline SVG, image-only provisions and CSS image references. Preserve surrounding text, captions and labels already available as text.
- Retain each provision's source ID, heading, hierarchy and provenance. An image-only body becomes `[IMAGE]`; it must not be discarded or treated as an unexplained empty section.
- Keep image reference/omission metadata, including the source locator where available. Do not leave active image tags, image data URIs or CSS image fetches in normalized HTML. The same image-byte exclusion applies recursively to normalized JSON and metadata, including legal notes, captions and source attributes. If an attribute embeds image bytes, retain an omission marker and a hash of the original attribute instead of copying its payload.
- Intentionally omitted images are policy exclusions, not failed required attachments. Completeness checks must verify placeholder coverage instead of image-byte acquisition. This does not claim that image contents have been transcribed.
- Nonimage legal documents, PDF publications and required document attachments retain their separate collection and coverage rules. Original publisher HTML, PDFs or bulk archives may inherently contain embedded images; retaining an original source file is distinct from extracting or downloading separate image assets. Normalized output follows the placeholder rule.
- PDF page output inserts placeholders for detected image objects without saving their pixels; source-family runbooks state detection and ordering limits. Image-only/scanned pages must not be represented as successfully extracted legal text merely because a placeholder exists.

Regression tests must cover image-only source nodes, image placeholders in text and HTML, SVG/CSS/picture cases, preserved source identity, no image-acquisition calls and completeness unaffected by intentional image omission. Nonimage attachment failures must continue to be reported.

Earlier sealed validation evidence is immutable. Some exploratory runs predate this clarification and contain acquired images; they do not define the behavior of the final collectors. Final validation reports distinguish those historical runs from the current image policy.
