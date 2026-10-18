# Windows build and local verification

Install `requirements-lock.txt` and `requirements-build.txt` in a Python 3.11 x64 development environment. Run `python tools/build_windows.py` from the project directory. This produces `dist/Luma/Luma.exe` with its `_internal` runtime directory. Keep the directory together. End users do not invoke Python to run this executable.

The build uses `Luma.spec` with explicit first-party assets. It excludes local voices, documents, personal state, verification screenshots and unused Qt WebEngine/PDF modules. Qt's unused PDF image plugin is removed. Unintended ICU binaries from the developer PATH must not shadow the Windows ICU API; the build filters them and audits the result. This target requires a supported Windows version providing that API; the tested host is Windows build 26200.

The builder copies available installed dependency notice files, preserving package paths, and writes a SHA-256 inventory in `release/local-audit/binary-inventory.json`. These notices are a starting point, not proof that corresponding-source obligations or all native-library licences have been fulfilled.

For local diagnostics, set `LUMA_DATA_DIR` to an isolated writable folder and run `Luma.exe --self-test <absolute-report-path.json>`. The report exercises the packaged Qt runtime, assets, PDF extraction/rendering, DOCX handling, OCR model loading, Piper and user storage. A successful host test is not a clean-machine or voice synthesis/playback test.

`Launch Portable.cmd` selects writable data beside the executable. Normal launch uses per-user AppData. `installer/Luma.iss` is a per-user Inno Setup 6 configuration, preserving user data on uninstall. Installation, reinstallation, version upgrade and uninstall have passed isolated development-host verification. No file associations or privileged system changes are enabled implicitly.

Build artifacts remain local verification candidates until every applicable gate in `release/release-gates.json` is cleared. Do not publish the current output. Voice clearance and exact OCR model provenance passed. Complete native source/notices review, covered corresponding source and clean-machine testing remain pending.

## Current local result

18 October 2026: a clean build produced the standalone executable. Its diagnostic reported `frozen: true` and passed the Windows Qt platform, assets, PDF extraction/rendering, DOCX, OCR model construction, Piper imports, eSpeak phonemization and isolated writable storage. The updated build contains the reviewed Cori high voice and credit/model-card files (844 inventoried files). A second frozen diagnostic synthesized a 3.92-second, 22050 Hz WAV using the bundled voice. The diagnostic ran on the development computer; this does not prove operation on a machine without Python installed or full audio-device playback.

After a successful inventory, run `python tools/archive_build.py` to produce the portable ZIP and SHA256SUMS.txt. It rejects additions or changed file hashes after audit and verifies ZIP integrity. It uses fixed member timestamps and sorted paths; identical input files yield identical archive bytes. This does not establish reproducible compiler output.

An initial executable failure was traced to `icuuc.dll` collected from a Poppler runtime on the developer PATH. Filtering that incompatible DLL restored Qt imports. The final build applies the filter directly; no manual post-build deletion is needed. The unused `qpdf.dll` image plugin and `Qt6Pdf.dll` are also filtered. Notice filenames mentioning WebEngine do not indicate that its binaries are bundled.

Installer follow-up: `python tools/build_installer.py` compiles with the portable Inno compiler under `tmp/installer-tools/compiler`. `python tools/verify_installer.py --candidate` tests the actual installer after refusing any pre-existing Luma install. It installs into an isolated workspace directory, tests the installed executable, reinstalls and uninstalls while checking user-note preservation. This passed on the development host; see INSTALLER_VERIFICATION.md for limits. The packaged multimedia diagnostic also passed muted decode-to-EndOfMedia checks. Version-to-version upgrade passed; clean-machine tests remain pending.

## Restricted native-library search path

The builder now passes only the virtual environment scripts, base Python/DLLs and Windows system directories in PATH to PyInstaller. Package hooks may add their own installed library directories. The spec rejects binary origins outside the virtual environment, base Python installation and Windows directory. This prevents harvesting DLLs from unrelated applications such as Poppler or libheif.

The 18 October rebuild contains 803 audited files and 137 native/model files, reduced from 848/183. Of these, 112 match installed distributions and 23 match base Python runtime files by hash. The two remaining inventory entries are the separately reviewed Cori voice and msvcp140.dll from Windows System32. The latter has a valid Microsoft Windows Authenticode signature; signature validity does not by itself establish redistribution permission. The full Python installation LICENSE.txt is now preserved and indexed in third-party-notices/Python.

The rebuilt diagnostic passed all checks, including 4.24-second speech synthesis and muted decode-to-EndOfMedia. Source fingerprint: `4b4a5d1caf6159af974e8ca46bcc453ac9921897c8b167f764dcabbfebf285ac`. Tests: 59 passed. Portable archive integrity passed. These remain development-host results.

Microsoft runtime follow-up: official deployment guidance says redistribution of Visual C++ runtime packages or individual binaries is subject to the applicable Visual Studio licence and distributable-code list. A valid signature or a DLL being installed on this host is insufficient permission evidence. Verify the applicable toolchain/distribution terms or choose a documented runtime prerequisite strategy before clearing the native gate. Reference: https://learn.microsoft.com/en-us/cpp/windows/redistributing-visual-cpp-files?view=msvc-170 .
