# Development candidate: known issues

- Tested on one Windows 11 x64 host (build 26200), 1920×1080 at 100% scaling. Clean-machine compatibility, mixed-scale monitors and a visible taskbar configuration are still unverified.
- The native maximize hit test, maximize/restore and system menu passed checks. Full Snap layout selection still needs desktop verification. Use the standard Windows title-bar setting as a fallback after restart.
- PDF selection follows extracted reading order. Clear two-column native and OCR prose has conservative automatic ordering; short/ambiguous OCR columns, unusual columns, tables, equations and ligatures can still be ambiguous. Use the extracted-text view to inspect or select the intended passage.
- OCR selects detected line regions, may omit or misrecognize text, and does not describe the meaning of figures. Check accounting amounts and formulas against the page. Native text was more complete than OCR on the sampled book page.
- Cross-page selection uses navigation followed by Shift-click; continuous edge-drag page turning is not implemented.
- Underline/subscript/superscript in Markdown use inline HTML. Other Markdown readers may render them differently.
- Recovery saves after a short idle delay and cannot guarantee recovery of the last keystrokes before abrupt shutdown. Keep important notes saved.
- Installed diagnostics and same-version reinstall/uninstall passed on the development host. Version-to-version upgrade also passed. Interrupted installation remains unverified.
- Muted audio decoding and completion passed. Physical speaker audibility and all output devices remain unverified.
- Piper integration with other Windows readers is separate work. Do not claim the bundled voice is a system-wide SAPI voice or works in every reader.
- Native-library corresponding source/notices and a public source distribution destination remain open release gates. Current artifacts are local development candidates.
- CI is prepared but has not run on GitHub. It must pass in the selected repository before being described as verified.
