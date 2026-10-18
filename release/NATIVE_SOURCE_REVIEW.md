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
- qtdeclarative: retained reference source for earlier development candidates; new minimal builds exclude the QML/Quick group.
- qtmultimedia: shipped Multimedia and MultimediaWidgets libraries and multimedia backends.
- qtsvg: shipped Svg library and related image support.
- qtvirtualkeyboard: retained reference source for earlier development candidates; new minimal builds exclude its library and input plugin.
- pyside-setup: Python bindings and Shiboken sources, separate from Qt framework sources.

All retained Qt archives are version 6.12.0, matching the installed Qt/PySide package version. Version correspondence alone does not prove the exact build configuration, downstream patches or bundled third-party component source correspondence. Review those before clearing the native gate. FFmpeg n9.0.1 has its actual packaged configuration recorded separately in release/evidence/ffmpeg-build-config.json.

## Remaining source and deployment review

Trace the exact shipped Piper/eSpeak, PyMuPDF/MuPDF and other native dependency builds to applicable source, patch and build records. Review dependencies embedded inside wheels, including codecs, cryptography, font/rendering and numerical libraries. Preserve their required notices. Check Microsoft runtime distribution terms separately; an installed signed DLL is insufficient permission evidence. Python's full runtime licence is now preserved automatically by the builder.

The native and corresponding-source release gates remain pending. No public release or upload is authorized by this review record.

## Piper and PyMuPDF source distributions

The exact Piper 1.8.0 and PyMuPDF 1.28.2 PyPI source distributions were retained and matched their SHA-256 values published by PyPI. Neither archive contains all native engine source: Piper lacks its native bridge/eSpeak build sources, and the PyMuPDF distribution does not embed MuPDF source. Their upstream repository/build dependency records still need to be retained. Do not clear the corresponding-source gate based on these source distributions alone.

The Piper source archive also exposed optional Hebrew/Arabic text-processing ONNX weights that the broad data collector copied into prior development candidates. They are outside the approved voice/OCR set. The spec now excludes Piper package ONNX data, and packaging checks require exactly the reviewed voice and three OCR paths, rejecting extras or missing files. These optional language-processing models are not bundled; voices requiring them need separate support/provenance review. Source archives remain evidence archives and are not executed or shipped as runtime data.

## Native engine source and nested dependencies

The Piper v1.8.0 release resolves to commit 639388b6317fc4731e91d53da42aea68fd4166ff. Its CMakeLists.txt pins eSpeak to 724808c, resolved to full commit 724808c5a83f9ef95fdd0db886ba7ba537ff224a. Both repository archives are retained; the Piper archive contains its native espeakbridge source and CMake build definition, and the eSpeak archive includes its ucd-tools C sources.

MuPDF 1.28.2 resolves to fe374accd98a43174a328fa7980d7675e06d5b0d. The release-server download failed certificate verification; it was not bypassed. The official Artifex GitHub archive is retained instead. Its .gitmodules and thirdparty Git tree identify 18 pinned repositories, all retained. FreeType has one nested dlg submodule at 395ccad2c1e0daae535c4d20bb0a3f2424648e17, also retained. The other retained component archives and dlg did not expose further .gitmodules files. See mupdf-source-components.json for exact paths, repositories and revisions.

The current collection has 31 archives, totaling 391420834 bytes, with SHA-256 inventories. tools/package_native_sources.py assembles only this explicit set into dist/Luma-upstream-source-review.zip, preserving original archives and review metadata. It rejects missing/extra names, changed hashes and unsafe paths and verifies ZIP integrity. This is a local review artifact; publication_approved and completeness_verified remain false.

These source revisions establish release-reference coverage. Exact wheel/native build provenance, downstream patches, generated build inputs and licence/notice completeness still require review before native or corresponding-source gates can pass. No source download is executed. The first-party application source remains separate from the upstream review archive.

## Packaged native notice preservation

356 original notice/copyright-context files from the 31 source archives are retained in evidence/native-source-notices.zip. The separate native-notice-manifest.json pins its digest and count. The collector includes licences with nonstandard names (for example FreeType FTL.TXT and leptonica-license.txt) and root README copyright context, while excluding example code/images. Packaging checks the entire ZIP and every indexed notice before copying original bytes into third-party-notices/native-sources. The index retains source archive/member paths. Four focused tests cover byte preservation, source/bundle changes and unsafe ZIP paths. This is notice preservation, not completed binary/source mapping or automatic release approval.

## Minimal native-library policy

PE import/delay-import inspection found that the Qt Widgets/Gui/Multimedia libraries do not import the QML/Quick group; its entry point was the optional VirtualKeyboard plugin. New packaging excludes that closed group and the unused OpenCV video-FFmpeg helper. A post-copy PE audit rejects any remaining direct/delay import of excluded libraries. The Windows system ICU import is explicitly retained as a system dependency. The packaged diagnostic now constructs/renders the real Reader window and Markdown editor in an isolated state folder, with global hotkey registration disabled. Validate each resulting build before claiming compatibility; this does not replace physical display/IME testing.

## Microsoft runtime review, 18 October 2026

The owner reports Visual Studio as "Not installed / not sure". Treat the distributor's licence status as unconfirmed. Microsoft's redistribution guidance explicitly limits distribution of the runtime package and individual binaries to licensed Visual Studio users, subject to the relevant terms:
https://learn.microsoft.com/en-us/cpp/windows/redistributing-visual-cpp-files?view=msvc-170

The current official licence link redirects to the Visual C++ V14 Redistributable and Runtime 2026 terms page:
https://visualstudio.microsoft.com/license-terms/vs2026-ga-visualcpp-v14-redist-runtime/

Its linked DOCX returned HTTP 403 during retrieval; no complete terms review is claimed. A signed installed DLL or a successful GitHub-hosted build does not establish this project's redistribution rights. Do not require the owner to install the Visual Studio IDE simply to run Luma. Keep the distribution gate pending until an applicable licence grant and the conditions for the actual runtime binaries have been established. No Visual Studio installation, account change or runtime replacement was performed.
