# Native source review

This record tracks retained upstream archives, not completed binary redistribution clearance. Archives were downloaded over verified TLS from Qt's official download service or FFmpeg's official GitHub mirror. Recorded SHA-256 values identify the downloaded bytes; they are not a claim of an independently verified upstream signature. No source archive was compiled or executed.

## Retained archives

| Archive | Bytes | SHA-256 |
|---|---:|---|
| pyside-setup-everywhere-src-6.12.0.tar.xz | 18211772 | `099c1a597cf33c1b000e11cf68a0b82d216fb802bf81726efc720394f10c7751` |
| ffmpeg-n9.0.1-github.tar.gz | 17306989 | `195d54bebe1a27f84d77f4b989d193466f305b355da92292766a69f16880b18a` |
| qtbase-everywhere-src-6.12.0.tar.xz | 51220268 | `a951bd163c7b80fc6b8c88d7668fb56abf91c152373e13c10666763238131307` |
| qtdeclarative-everywhere-src-6.12.0.tar.xz | 39221652 | `311f3a2603e1973bb59baef9dfa740a376de713157d4782ee043681e889c9260` |
| qtmultimedia-everywhere-src-6.12.0.tar.xz | 10544184 | `3143f53b64257ba2a0685c940f5dce476c75871ff86b516de45cfd54ea93a62d` |
| qtsvg-everywhere-src-6.12.0.tar.xz | 2341876 | `e4ab39534ec97987b1b9b60ef7f4d3253d5912a69f8c713a01753174a4029331` |
| qtvirtualkeyboard-everywhere-src-6.12.0.tar.xz | 3281984 | `2aae3628f4648f86959d7853e7e1f50ee96a7f1bb5497afb62b7deff6c350170` |

Exact source URLs, member counts and licence-file inventories are retained locally in release/local-audit/upstream-sources/manifest.json. This directory is excluded from the first-party source ZIP. A public corresponding-source package and destination remain to be prepared.

## Qt module coverage

- qtbase: shipped Core, Gui, Widgets, Network and OpenGL libraries.
- qtdeclarative: shipped Qml, QmlMeta, QmlModels, QmlWorkerScript and Quick libraries.
- qtmultimedia: shipped Multimedia and MultimediaWidgets libraries and multimedia backends.
- qtsvg: shipped Svg library and related image support.
- qtvirtualkeyboard: shipped VirtualKeyboard library and its input plugin.
- pyside-setup: Python bindings and Shiboken sources, separate from Qt framework sources.

All retained Qt archives are version 6.12.0, matching the installed Qt/PySide package version. Version correspondence alone does not prove the exact build configuration, downstream patches or bundled third-party component source correspondence. Review those before clearing the native gate. FFmpeg n9.0.1 has its actual packaged configuration recorded separately in release/evidence/ffmpeg-build-config.json.

## Remaining source and deployment review

Trace the exact shipped Piper/eSpeak, PyMuPDF/MuPDF and other native dependency builds to applicable source, patch and build records. Review dependencies embedded inside wheels, including codecs, cryptography, font/rendering and numerical libraries. Preserve their required notices. Check Microsoft runtime distribution terms separately; an installed signed DLL is insufficient permission evidence. Python's full runtime licence is now preserved automatically by the builder.

The native and corresponding-source release gates remain pending. No public release or upload is authorized by this review record.

## Piper and PyMuPDF source distributions

The exact Piper 1.8.0 and PyMuPDF 1.28.2 PyPI source distributions were retained and matched their SHA-256 values published by PyPI. Neither archive contains all native engine source: Piper lacks its native bridge/eSpeak build sources, and the PyMuPDF distribution does not embed MuPDF source. Their upstream repository/build dependency records still need to be retained. Do not clear the corresponding-source gate based on these source distributions alone.

The Piper source archive also exposed optional Hebrew/Arabic text-processing ONNX weights that the broad data collector copied into prior development candidates. They are outside the approved voice/OCR set. The spec now excludes Piper package ONNX data, and packaging checks require exactly the reviewed voice and three OCR paths, rejecting extras or missing files. These optional language-processing models are not bundled; voices requiring them need separate support/provenance review. Source archives remain evidence archives and are not executed or shipped as runtime data.
