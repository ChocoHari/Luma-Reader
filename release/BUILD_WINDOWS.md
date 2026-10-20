# Windows build and local verification

Install `requirements-lock.txt` and `requirements-build.txt` in a Python 3.13.16 x64 development environment. Run `python tools/fetch_ocr_models.py` and `python tools/fetch_build_voice.py` for the explicitly reviewed assets, then run `python tools/build_windows.py` from the project directory. This produces `dist/Luma/Luma.exe` with its `_internal` runtime directory. Keep the directory together. End users do not invoke Python to run this executable.

The build uses `Luma.spec` with explicit first-party assets. It excludes local voices, documents, personal state, verification screenshots and unused Qt WebEngine/PDF modules. Qt's unused PDF image plugin is removed. Unintended ICU binaries from the developer PATH must not shadow the Windows ICU API; the build filters them and audits the result. This target requires a supported Windows version providing that API; the tested host is Windows build 26200.

The builder copies available installed dependency notice files, preserving package paths, and writes a SHA-256 inventory in `release/local-audit/binary-inventory.json`. These notices are a starting point, not proof that corresponding-source obligations or all native-library licences have been fulfilled.

For local diagnostics, set `LUMA_DATA_DIR` to an isolated writable folder and run `Luma.exe --self-test <absolute-report-path.json>`. The report exercises the packaged Qt runtime, assets, PDF extraction/rendering, DOCX handling, actual OCR inference, Reader/Markdown rendering, Piper speech synthesis, muted audio decoding/playback and user storage. The report also checks that inference telemetry was disabled before engine imports. A successful host test does not establish clean-machine operation or physical speaker audibility.

`Launch Portable.cmd` selects writable data beside the executable. Normal launch uses per-user AppData. `installer/Luma.iss` is a per-user Inno Setup 6 configuration, preserving user data on uninstall. Installation, reinstallation, version upgrade and uninstall have passed isolated development-host verification. No file associations or privileged system changes are enabled implicitly.

Build artifacts remain local verification candidates until every applicable gate in `release/release-gates.json` is cleared. Do not publish the current output. Voice clearance and exact OCR model provenance passed. Complete native source/notices review, covered corresponding source and clean-machine testing remain pending.

## Current local result

The latest completed minimal candidate passed the isolated Windows diagnostic, including actual OCR inference and Reader/Markdown rendering. Version 0.3.0-dev to 0.3.1-dev upgrade, installed diagnostics and uninstall passed all eight checks while retaining notes/settings. Current identifiers and verification status are in RELEASE_CHECKLIST.txt; older private reports are retained under verification/. Later source changes need a fresh build and matching-source validation before being described as packaged. These remain development-host results.

After a successful inventory, run `python tools/archive_build.py` to produce the portable ZIP and SHA256SUMS.txt. It rejects additions or changed file hashes after audit and verifies ZIP integrity. It uses fixed member timestamps and sorted paths; identical input files yield identical archive bytes. This does not establish reproducible compiler output.

An initial executable failure was traced to `icuuc.dll` collected from a Poppler runtime on the developer PATH. Filtering that incompatible DLL restored Qt imports. The final build applies the filter directly; no manual post-build deletion is needed. The unused `qpdf.dll` image plugin and `Qt6Pdf.dll` are also filtered. Notice filenames mentioning WebEngine do not indicate that its binaries are bundled.

Installer follow-up: `python tools/build_installer.py` compiles with the portable Inno compiler under `tmp/installer-tools/compiler`. `python tools/verify_installer.py --candidate` tests the actual installer after refusing any pre-existing Luma install. It installs into an isolated workspace directory, tests the installed executable, reinstalls and uninstalls while checking user-note preservation. This passed on the development host; see INSTALLER_VERIFICATION.md for limits. The packaged multimedia diagnostic also passed muted decode-to-EndOfMedia checks. Version-to-version upgrade passed; clean-machine tests remain pending.

## Restricted native-library search path

The builder now passes only the virtual environment scripts, base Python/DLLs and Windows system directories in PATH to PyInstaller. Package hooks may add their own installed library directories. The spec rejects binary origins outside the virtual environment, base Python installation and Windows directory. This prevents harvesting DLLs from unrelated applications such as Poppler or libheif.

The full Python installation LICENSE.txt is preserved and indexed in third-party-notices/Python. Unused Qt VirtualKeyboard/QML/Quick libraries and the OpenCV video-FFmpeg helper are excluded. Post-copy PE import inspection rejects dependencies on excluded libraries. A valid Microsoft DLL signature alone does not establish redistribution permission.

Microsoft runtime follow-up: official deployment guidance says redistribution of Visual C++ runtime packages or individual binaries is subject to the applicable Visual Studio licence and distributable-code list. A valid signature or a DLL being installed on this host is insufficient permission evidence. Verify the applicable toolchain/distribution terms or choose a documented runtime prerequisite strategy before clearing the native gate. Reference: https://learn.microsoft.com/en-us/cpp/windows/redistributing-visual-cpp-files?view=msvc-170 .

The active Python environment is used for native origins and notice collection; its folder name is not fixed. Development setup now creates .venv313 without replacing an existing .venv. Source launchers prefer .venv313. The maintained RapidOCR engine uses only hash-verified files in ocr_models/; its bundled default ONNX models are excluded. The diagnostic and package inventory record actual Python/OpenSSL versions. The earlier verified 3.11.3 candidate remains historical evidence, not proof of the refreshed frozen build.
