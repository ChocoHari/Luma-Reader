# Contributing to Luma Reader

Luma Community is developed under AGPL-3.0-or-later. Contributions to first-party code are accepted under that licence; contributors retain their copyright. Do not submit code or assets you lack permission to distribute. No contributor licence assignment or private relicensing permission is implied.

Use Python 3.11 on Windows. Create a local virtual environment, install requirements-lock.txt and run `python -m pytest`. Source changes should keep reading, note saving, Piper speech, OCR and offline operation usable. Add meaningful regression coverage for changed behaviour.

For a clean checkout, run `python tools/fetch_build_voice.py` before engine tests. It fetches only the reviewed Cori pair and enforces both hashes; it will not overwrite an existing different file. Engine tests exercise discovered voices instead of assuming the maintainer's private five-voice folder. Install requirements-build.txt for packaging. `python tools/verify_source_checkout.py` exercises an isolated allowlisted source tree with only approved voices while reusing your development dependencies; it is not a clean-machine test.

The prepared Windows CI workflow uses read-only repository permissions and does not publish releases or upload artifacts. It has not yet run in a public repository. `python tools/check_release.py` reports pending public-binary gates and intentionally exits unsuccessfully while they remain open. A green test/build does not override that policy or licence obligations.

Do not submit personal books, private notes, settings, OCR text caches, credentials, voice recordings, or screenshots showing someone else's private reading list. Use original synthetic test content. Voice contributions require a model card, upstream sources, relevant licences, speaker permissions and a reviewed redistribution manifest; never assume the application licence covers a model.

Please describe the concrete problem, resulting behaviour and relevant validation in a change proposal. Avoid promising universal PDF/OCR accuracy or untested platform support.

Until a public repository and support destination are selected, prepare reports locally. A future security/contact policy must use a real maintainer-controlled destination; no address is invented here.
