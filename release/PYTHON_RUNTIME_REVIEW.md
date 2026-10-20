# Python runtime refresh review

Status: required before public binary release. Reviewed 20 October 2026.

The verified local candidate uses CPython 3.11.3 and includes the corresponding older OpenSSL runtime files. Its functional checks remain valid for that candidate, but they are not a runtime security or maintenance review. Do not promote it as the final public binary without refreshing and checking its runtime.

Python's official [3.11.17 release page](https://www.python.org/downloads/release/python-31117/) identifies the 3.11 branch as security-fixes only and confirms that official binary installers ended with 3.11.9. Merely taking the latest available 3.11 installer would therefore miss subsequent security releases.

The official [3.13.16 release](https://www.python.org/downloads/release/python-31316/) provides a current Windows maintenance release, including updated bundled OpenSSL and Expat. It is a candidate for an isolated compatibility/build trial; support is not established until Luma's pinned native dependencies and frozen app pass. A newer maintained feature series may be evaluated if the dependency matrix requires it.

Required work:

- Obtain an official x64 standard-GIL runtime and verify its published digest/signature. Keep the development host's existing Python installation intact.
- Create a separate build/test environment and resolve every locked dependency as a compatible binary wheel, recording changes rather than silently relaxing pins.
- Run source tests, real OCR/Piper/PDF/editor diagnostics and an isolated-path frozen build. Recheck runtime versions, native notices and corresponding-source records.
- Produce a new paired installer, portable archive, exact source snapshot and checksums, then repeat upgrade/uninstall and clean-Windows tests against that candidate.
- Update CI and supported build documentation only after compatibility evidence is available.

A project-local Python 3.13.16 NuGet build runtime was subsequently downloaded, matched to the official catalogue SHA-512 and unpacked safely. Its python.exe and python313.dll have valid Python Software Foundation signatures. Runtime launch reports Python 3.13.16 and OpenSSL 3.5.9. A separate compatibility environment was created; the pinned binary-only dependency trial stopped because rapidocr-onnxruntime 1.4.4 requires Python below 3.13. Its restriction was not bypassed. Maintained RapidOCR 3.10.0 is under separate review for an adapter using the existing reviewed models, with no application dependency adoption yet. The host Python installation, registry/PATH and existing candidate are unchanged. Source and frozen compatibility checks remain pending; the clean-package release gate remains pending.


## Verified source migration

The maintained RapidOCR 3.10.0 engine was integrated using explicit paths to the original three reviewed models. The independent offline probe recovered every reference word from the original scan fixture with network and downloader rejection enabled. The refreshed .venv313 environment passed all 102 tests, including actual OCR, two-column reading order and Piper checks; the real OCR tests reject package downloader calls. Setup and launchers now prefer the separate 3.13 environment. Bundled RapidOCR default ONNX weights are excluded from packaging, and the model allowlist uses only ocr_models/ plus the approved voice. CI targets Python 3.13.16. A new frozen candidate is being built; frozen/upgrade/clean-Windows evidence remains pending. The old package set was copied and its hashes rechecked before rebuilding.
