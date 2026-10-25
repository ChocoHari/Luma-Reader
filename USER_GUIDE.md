# Luma Reader user guide

An offline document reader and note editor with Piper voices, scanned-page OCR, a custom window frame, and eight colour themes.

## Launch and window controls

For an installed build, open Luma from the Start menu or its installed executable. For a portable build, extract the complete archive and use **Launch Portable.cmd**; keep Luma.exe and its _internal folder together. Standalone builds include Python and the runtime. Development source launchers require the project's Python environment. Current development builds are for local verification until the release gates are cleared.

The custom title bar contains the Book & wave logo and minimize, maximize/restore, and close buttons. Drag the title area to move the window; double-click it to maximize/restore. Drag an edge or corner to resize. Alt+F4 closes with the usual unsaved-note check. On the tested Windows 11 host, hovering over maximize displays Windows Snap Layouts. Layout selection and other display configurations remain under verification. Settings offers a standard Windows title bar after restarting Luma.

## Appearance

Choose **Baby blue, Coral, Lavender, or Soft brown**, then **Light, Dark, or Windows**. Windows follows the operating system's light/dark preference. The colour and appearance choices are remembered. **Menu** collapses or restores the sidebar.

PDF pages retain their original colours. **Dim page** softens bright pages without changing the file. Help → Design and logo gallery shows the colour families and the preserved alternative logo concepts.

## Open and read

Open or drop a PDF, DOCX, TXT, Markdown, or HTML note. Recent files, document outline, and saved bookmarks appear in the sidebar; double-click an item to open or navigate.

PDFs open in **PDF view**, with the original page as the main surface. Choose **Split** to show extracted text on the right, or **Text** to read just the extracted text. The chosen PDF view is remembered. DOCX opens as extracted reading text; original Word layout is not rendered.

- Page arrows and number entry navigate PDF pages.
- Zoom offers fit width, fit page, and 75–200 percent.
- **Page → Read this page / Ctrl+Shift+P** reads the displayed page only.
- **Page → Read from this page onward** continues through later pages.
- **Read selection / Ctrl+Shift+R** uses the selection in the extracted-text or note editor. In the original PDF view, drag to select a word range, then right-click for Copy selection, Read selection or Read from here. Ctrl+C copies the page selection. To extend across pages, select the beginning, change pages, then Shift-click the ending text. OCR selection uses detected lines rather than individual letters.
- **Read from cursor / Ctrl+R** reads from the text cursor.
- **Play / F5** starts or pauses; **Stop / F6** stops and clears buffered audio.
- Previous/Next restart at an adjacent sentence in the active reading scope.

Choose a Piper voice and, where supported, a speaker in the bottom bar. Speed/speaker changes restart the current sentence. Volume changes immediately. **Test** speaks a short voice sample.

## Highlighting and PDF following

Spoken sentences are highlighted in text. PDF playback follows the current page and overlays matching words in gold when source-to-page alignment is sufficiently confident. Complex layouts or unusual PDF encodings can prevent a reliable match; in that case the overlay is omitted and text highlighting remains available.

OCR results retain line coordinates for scanned-page overlays. Legacy caches without coordinates rebuild automatically when opened with OCR enabled; Selectable text only leaves caches untouched. Weak native-text alignment falls back to the extracted-text pane. Highlighting follows sentences/lines rather than providing word-timed karaoke.

Clear two-column native and OCR prose is read down the left column before the right, with full-width lines separating sections. Detection is conservative; short columns, complex tables and nested layouts may still need correction in an editable copy. Existing OCR coordinate caches can be reordered without rerunning recognition.

## Speech preparation

Open **Settings** to choose a profile and edit pronunciation replacements:

| Profile | Behaviour |
|---|---|
| Natural | Expands common titles, skips decorative separators, turns arrows into short punctuation pauses, and speaks supported mathematical operators. |
| Study | Speaks arrows and supported notation, with extra pauses. Rich-note headings receive longer pauses. |
| Literal | Retains more punctuation/symbols and does not omit detected PDF margins. This is not an exhaustive character-by-character spelling engine. |

Examples: Mr./Mrs./Dr. stay with the name rather than creating a false sentence break; 3.14 remains a number; U.S. is treated as an initialism. The rules are deterministic and English-oriented. Ambiguous abbreviations, dates, tables, and mathematical notation can still need a replacement or an edited draft.

The replacement dictionary matches whole terms case-insensitively. Use **Read → Preview spoken text / Ctrl+Shift+T** to see exactly what is sent to Piper. A text selection limits the preview; otherwise it covers the document. The original document is never rewritten by speech cleanup.

An optional repeated-margin filter omits short repeated first/last lines and standalone page numbers on PDFs. It is deliberately conservative and can be disabled. Live playback and WAV export use the same preparation rules.

## Write and format notes

**New note / Ctrl+N** creates a Markdown note. Choose **Source**, **Preview** or **Split** above the document. Split shows editable source beside its live preview. The toolbar inserts headings, bold, italic, underline, strikeout, subscript/superscript and lists. Insert adds tasks, quotes, links, code and simple tables. Underline, subscript and superscript use inline HTML and may render differently in other Markdown readers. The Outline sidebar follows headings outside fenced code blocks.

- Ctrl+B / Ctrl+I / Ctrl+U: bold / italic / underline.
- Ctrl+Shift+V: paste plain text.
- Ctrl+Z / Ctrl+Y: undo / redo.
- Ctrl+F / Ctrl+H: search / replace.
- Ctrl+S / Ctrl+Shift+S: save / Save As.

**Focus** hides the sidebar and formatting toolbar; Exit focus restores them. Existing HTML notes retain rich editing. Edit → Convert note to rich format creates an unsaved rich copy. Rich notes support additional fonts, colours, alignment and spacing, and use HTML to retain formatting. File → New plain text note provides a TXT workflow with formatting disabled.

PDF and DOCX sources remain read-only. **Make editable copy** creates a Markdown draft of their extracted text. It preserves the source file; it does not reproduce Word/PDF page layout, images or tracked changes.

## Saving and conversions

- Save rich notes as `.html`.
- Save Markdown source as `.md` or `.markdown`.
- Save plain text as `.txt`.
- Rich → TXT/Markdown asks before formatting loss. The export does not discard your rich note or mark an unsaved rich note as saved; save an HTML copy to retain all formatting.
- Exporting reading text from a PDF/Word document leaves that source open and unchanged.

Files are saved as UTF-8, using a temporary file and atomic replacement. Unsaved notes prompt before close or replacement. The application remembers settings and reading positions automatically; saved document files change only when you save them. Unsaved editable notes also receive a private recovery snapshot after two seconds without typing. **File → Recover a draft** reopens one as an unsaved note. Save it to a document file. Saving or explicitly discarding removes that recovery copy; Cancel keeps it. Recovery cannot guarantee the last keystrokes before abrupt shutdown and does not replace regular saves.

## Offline OCR

Choose the OCR mode before opening a PDF:

1. **Automatic OCR:** recognize pages with fewer than 30 non-whitespace selectable characters.
2. **OCR every page:** recognize rendered pages even when text already exists. Useful for mixed image/text pages; slower for books.
3. **Selectable text only:** no OCR or cached OCR substitution.

**OCR this page** recognizes the current page at higher resolution. **Read → Restore original PDF page text** removes that page's OCR substitution/cache and restores selectable text. The original PDF is never modified.

Recognition runs locally using packaged RapidOCR ONNX models. Completed pages are cached; cancellation waits for the current recognition step. A document becomes available after import finishes. Large scanned books can take substantial time.

OCR reads words, captions and labels. It does not describe the meaning of diagrams or reliably interpret equations/tables. Add your own descriptions in an editable copy. The bundled recognizer is principally suited to English/Chinese print; other scripts are not guaranteed.

## Audio export

File → Export audio / Ctrl+E exports selected text, or all document text if nothing is selected. It uses the active speech profile, dictionary, voice, speaker, and speed. Output is a mono WAV at the model's sample rate. The playback volume slider does not change exported loudness.

Cancellation leaves an existing destination untouched. Long exports are generated incrementally in a background task.

## Read text from other applications

Leave Luma running, copy text with Ctrl+C, then press **Ctrl+Alt+R**. Luma reads that text using Piper. It does not watch the clipboard or copy automatically. If the shortcut is already in use, use **Read copied text** in Luma.

This does not register native Piper voices in other apps' menus. Native SAPI integration remains separate; see OTHER_READERS.md.

## Local data and troubleshooting

No document uploads, cloud OCR, speech services, or telemetry are used. All core features work offline after installation. Normal launches store settings.json, OCR caches, recovery drafts and imported voices under `%LOCALAPPDATA%/Luma Reader`. Launch Portable.cmd instead uses **Luma Data** beside the executable. Settings include recent paths, positions, bookmarks and preferences; OCR caches contain recognized document text and coordinates. Keep those private like the source documents.

Luma discovers its bundled voices and imported voices in the user-data voices folder. Source installations also discover the existing `Piper Voices` folder. Import another `.onnx` and matching `.onnx.json` from the Voices menu. Existing models are never overwritten by import. Voice licences are separate from the engine licence.

If no sound plays, check Windows' output device and export a short WAV to try in another player. Unexpected application errors are logged in **application.log** in the active user-data folder. Source developers can run `.venv\Scripts\python.exe app.py` to inspect startup errors.

See THIRD_PARTY.md for component licences, OTHER_READERS.md for external-reader compatibility, and release/KNOWN_ISSUES.md for the development candidate's tested limits.
