# Third-party components

Luma's first-party source is licensed under AGPL-3.0-or-later; see `LICENSE` and `NOTICE`. Third-party code and model assets retain their own terms. The current development installation is not yet an approved public binary. See `release/LICENSING_DECISION.md` and `release/release-gates.json` for the remaining packaging requirements.

| Component | Purpose | Upstream |
|---|---|---|
| Piper (GPL-3.0-or-later) | Speech synthesis | https://github.com/OHF-Voice/piper1-gpl |
| eSpeak NG (included through Piper) | Phonemization | https://github.com/espeak-ng/espeak-ng |
| PySide6 / Qt (LGPL/GPL/commercial options) | Interface and multimedia | https://doc.qt.io/qtforpython-6/licenses.html |
| PyMuPDF (AGPL/commercial options) | PDF extraction/rendering | https://pymupdf.readthedocs.io/ |
| python-docx (MIT) | Word document extraction | https://github.com/python-openxml/python-docx |
| RapidOCR ONNX runtime package | OCR pipeline and bundled OCR models | https://github.com/RapidAI/RapidOCR |
| ONNX Runtime (MIT) | Local model inference | https://github.com/microsoft/onnxruntime |
| Inno Setup | Windows installer builder/runtime; copyright Jordan Russell and Martijn Laan | https://jrsoftware.org/files/is/license.txt |

Transitive dependencies and exact versions are recorded in `requirements-lock.txt`. Voice licenses are separate from the Piper engine license. The original files in `Piper Voices` are preserved.

Run `python tools/audit_release.py` in the project environment to inventory installed distributions, their available notice-file hashes, native libraries and OCR models. Its environment report is kept locally in `release/local-audit/environment.json`; it is not the final shipped component bill of materials. Installed development and unused Qt modules must not automatically be bundled. Actual binary packaging must collect complete notices and any required corresponding source for the selected components, including Qt/FFmpeg and other native libraries.

`release/voice-manifest.json` records local model/configuration hashes. Its default is to exclude every voice from redistribution until an explicit review clears that exact artifact. `release/VOICE_REVIEW.md` records the differing dataset, attribution and model-provenance evidence. The generic repository licence does not replace individual voice terms.

Public licence texts and model-card evidence are retained under `release/evidence`, with source URLs and hashes in `sources.json`. Evidence snapshots do not replace verification of the components actually shipped. OCR model provenance and native-component source correspondence remain release gates.

Release-pinned native source notices are also retained in `release/evidence/native-source-notices.zip`, with a checked digest/count in `release/native-notice-manifest.json`. The builder validates this bundle and copies the original notice bytes into `third-party-notices/native-sources`, including an index of original archive/member paths. This reference collection includes upstream copyright context and alternative licence texts; it does not select a commercial licence or establish that every source component is present in a binary. See `release/REPLACING_NATIVE_LIBRARIES.md` for the package layout and local replacement checks.
