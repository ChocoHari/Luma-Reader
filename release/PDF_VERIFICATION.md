# PDF interaction evidence

Offline sampling of the user's accounting book used private one-page copies of PDF pages 101, 201 and 501. Native extraction produced 1,822 / 2,814 / 3,682 characters with 196 / 472 / 515 aligned regions respectively. Page 101 OCR produced 1,334 characters in 69 detected regions in 11.16 seconds. Network socket connections were disabled during the check. Originals were unchanged.

Rendered page 101 screenshots were inspected for both native and OCR highlight placement. The page includes prose, tables, figures and captions. Highlights overlay the corresponding visible heading/table regions. This verifies coordinate placement on the sampled content, not semantic understanding of diagrams or perfect table reading order. OCR recovered fewer characters than native extraction on this page; preserve native extraction where it is useful.

Private evidence: `verification/pdf-selection-book.json`, `pdf-native-101.png`, `pdf-ocr-101.png`, and additional page screenshots. These files are excluded from public source and marketing packages. Public demonstrations must use original content.

Automated checks cover ordinary/rotated pages at 75% and 150%, copy/read source ranges, multiline and cross-page extension, OCR coordinate migration and cache reuse. Complex-column reading order, diagram descriptions, letter-level OCR selection, continuous edge-drag page turning and full-book accuracy are not verified. The subsequent native/OCR column checks below complete representative layout verification for Phase 4. General complex-layout accuracy remains a documented limitation.

## Two-column native prose

18 October: the prior geometric extraction interleaved left/right lines in an original two-column sample. Native extraction now detects substantial multiline prose on both sides of a central gutter and reads each column downwards, preserving full-width blocks as section boundaries. Short table cells do not trigger this rule. The same ordered words feed speech highlighting and direct selection alignment. Page labels identify detected two-column text. Detection uses unrotated page coordinates and is tested after a 90-degree rotation.

Original-sample tests verify reversed PDF object creation order, headings between column sections, complete word alignment and separate left/right speech rectangles. Rendered verification/two-column-sample.png was visually inspected. Accounting-book pages 101, 201 and 501 retained their existing Page order classification; no private text was added to public samples. Local evidence: verification/reading-order-result.json. This is conservative two-column prose support, not general layout understanding. OCR columns, tables with long prose cells, nested columns and captions overlapping body text remain limitations.

## OCR columns and Phase 4 acceptance

The OCR path now conservatively orders columns when both sides contain at least four substantial prose lines with overlapping vertical ranges. Full-width lines separate sections. It rebuilds offsets while preserving line rectangles and all recognized non-whitespace content. Incomplete/overlapping mappings are left unchanged. Existing caches with complete coordinates can be upgraded without inference, and stable caches are not rewritten. OCR-off continues to ignore caches.

Actual RapidOCR inference on an original image-only two-column PDF, with network connections forbidden, recognized all 11 lines and ordered the five left lines before the five right lines. Tests verified every left/right rectangle against its resulting label. The original raster was visually inspected. Local evidence: verification/ocr-columns-result.json and ocr-columns-original.png. Focused end-to-end OCR integration passed.

Phase 4 representative acceptance checks are complete: native/scanned/rotated/two-column documents, direct selection/copy/read, zoom mapping, multiline and Shift-click cross-page ranges, source-aligned speech highlights and safe fallbacks. This does not establish full-book accuracy, diagram descriptions, arbitrary tables/nested columns, character-level OCR selection or continuous edge-drag navigation.
