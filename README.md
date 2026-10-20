# Luma Reader

An offline document reader and Markdown editor for Windows, with local Piper voices, PDF page selection and OCR.

Luma keeps the original PDF page as the main reading view. Select text on the page, listen with a local voice, or open an editable Markdown note beside its preview. Four theme families—baby blue, coral, lavender and soft brown—support light and dark appearances.

## Current status

Luma is a development release candidate. Local standalone builds, a portable ZIP and an installer have been tested on one Windows 11 computer. Public distribution is still gated by native-library source/notice work, clean-machine checks and remaining compatibility review. See [the release checklist](RELEASE_CHECKLIST.txt) and [release gates](release/release-gates.json). No public download, support account or donation address is claimed here.

## Features

- PDF, DOCX, TXT, Markdown and HTML reading.
- PDF-first view, page selection/copy/read, zoom, page-scoped reading and text highlights.
- Cross-page selection by selecting the start, changing pages and Shift-clicking the end.
- Local OCR for scanned text, captions and labels; OCR is not a diagram-description system.
- Markdown Source/Preview/Split editing, formatting controls, heading outline, focus mode and recovery drafts.
- Existing HTML-note editing and safe conversion prompts.
- Piper speech, pronunciation replacements, Natural/Study/Literal reading profiles, bookmarks and WAV export.
- A custom window frame and a standard Windows title-bar fallback.

## Run a local standalone build

Keep the entire extracted `Luma` folder together and open `Luma.exe`. Use `Launch Portable.cmd` if you want writable data beside the executable. Normal launch stores settings, imported voices, caches and recovery drafts in `%LOCALAPPDATA%/Luma Reader`. Notes remain where you save them.

The current candidate bundles the reviewed Cori high voice. Other local voices are not automatically redistributed. No Python installation is needed to invoke the built executable; clean-machine compatibility is still being verified. Read [the user guide](USER_GUIDE.md) for controls and [known issues](release/KNOWN_ISSUES.md) for limits.

## Develop or build

Use Windows x64 and Python 3.13.16. Create `.venv`, install `requirements-lock.txt`, then `requirements-build.txt`. Run `python tools/fetch_ocr_models.py` for the three hash-pinned OCR models, then `python tools/fetch_build_voice.py` to obtain only the reviewed build voice with enforced hashes. Existing matching files are reused; mismatched local files are not overwritten.

Run `python -m pytest tests -q`, then `python tools/build_windows.py`. See [Windows build instructions](release/BUILD_WINDOWS.md), [source snapshots](release/SOURCE_PACKAGING.md) and [contribution guidelines](CONTRIBUTING.md). The repository workflow prepares and checks local build candidates; it does not publish a release automatically.

## Licence and credits

First-party source is AGPL-3.0-or-later. Models and third-party libraries retain their own terms. See [LICENSE](LICENSE), [NOTICE](NOTICE), [third-party components](THIRD_PARTY.md) and the [Cori model review](release/CORI_CLEARANCE.md). Donations or paid builds do not change the rights granted by those licences.

Privacy and local storage details: [Privacy](release/PRIVACY.md).
