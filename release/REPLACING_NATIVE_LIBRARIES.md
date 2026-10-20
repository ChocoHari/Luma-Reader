# Replacing native libraries in a development build

Luma's first-party source and build tools are available in the repository. Native components retain their own licences. Their source references and retained notice records are described in NATIVE_SOURCE_REVIEW.md and native-notice-manifest.json.

The standalone package keeps native libraries as ordinary files under `_internal`. Luma does not enforce native-library hashes at normal startup or require a signing key to load a modified library. Hash checks in the build/archive tools validate release inputs; they do not prevent a user from running a modified local copy.

Use a separate copy of the complete application directory when testing replacements. Close that copy before changing a loaded DLL. Keep compatible library names, architecture, compiler ABI and dependent libraries together. A different major Qt or Python ABI generally requires rebuilding the corresponding bindings and application package.

| Component | Current package location |
|---|---|
| Qt libraries and plugins | `_internal/PySide6/` |
| FFmpeg shared libraries | `_internal/PySide6/avcodec-63.dll`, `avformat-63.dll`, `avutil-61.dll`, `swresample-7.dll`, `swscale-10.dll` |
| Piper's eSpeak bridge | `_internal/piper/espeakbridge.pyd` |
| MuPDF shared library and Python bindings | `_internal/pymupdf/` |

For a modified component, use its upstream build instructions in the retained source archive. Piper's release CMake definition records the pinned eSpeak dependency and build flags. The packaged FFmpeg configuration is recorded in evidence/ffmpeg-build-config.json. Qt and MuPDF build correspondence remains part of the release review; version agreement alone is not a guarantee of binary compatibility.

After replacing a compatible library, run the copied `Luma.exe --self-test <absolute-report-path.json>`. Set `LUMA_DATA_DIR` to a separate test folder so this check does not reuse normal settings. To include synthesis, set `LUMA_TEST_VOICE` to the copied package's `_internal/voices/en_GB-cori-high.onnx`. The diagnostic writes a JSON report and a test WAV; playback is muted. Inspect both the exit code and the report's checks. A successful diagnostic is a smoke test, not a complete compatibility assessment.

To rebuild Luma itself, install the locked development dependencies and follow BUILD_WINDOWS.md. The PyInstaller build uses the selected Python environment, explicit app assets and model/notice policies. No account or online activation is needed to run the resulting local application.
