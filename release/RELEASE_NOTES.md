# Luma 0.3 development candidate

This candidate adds a Markdown-first workspace, local recovery drafts and original-page PDF selection to the offline reader. The Windows build includes a reviewed Cori high voice and can run its own local diagnostic. Public release is still pending the checklist and distribution gates.

## Changes

- Markdown source, preview and split views; formatting/insertion controls, live headings and focus mode.
- Preserved HTML note editing and conversion prompts.
- Direct PDF word-range selection, copy/read commands and cross-page Shift-click extension.
- Rotated-page coordinates and automatic rebuilding of legacy OCR caches without coordinate fields.
- Native Windows frame integration and a standard-title-bar fallback.
- Per-user writable storage, one-time legacy migration and portable storage mode.
- Standalone runtime, portable archive and per-user installer preparation.
- Exact voice/OCR hashes, attribution files, source snapshots and executable source identity.

## Validation and limits

The prior full local functional run passed 53 tests. Packaged diagnostics passed PDF, DOCX, OCR model construction, Piper synthesis and muted playback. Same-version installer reinstallation/uninstallation preserved a test note. See KNOWN_ISSUES.md and the detailed verification documents for scope. A newer test result should replace this count when the candidate changes.

The current source/portable snapshot and an older installer can have different source identities. Publish only a verified matching artifact set; do not combine them into a release because their filenames share a version string. Checksums establish file identity, not completion of the release gates.
