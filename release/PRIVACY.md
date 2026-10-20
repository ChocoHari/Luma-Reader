# Luma privacy and local data

Luma's current reader, Markdown editor, OCR and Piper speech run on your computer. The app has no document-upload, cloud voice, account, advertising or analytics workflow. Models must be available locally. Downloading the application or obtaining additional voices involves the service you choose for that download.

Luma sets `ORT_DISABLE_TELEMETRY=1` before importing its inference engines and calls ONNX Runtime's `disable_telemetry_events()` before loading voice or OCR models. Both controls are deliberate: the environment control applies before SDK initialization, while the API covers supported platform telemetry, including older runtime builds. An error applying the API stops model initialization instead of silently proceeding. These controls do not change Windows settings or the behavior of other applications.

This describes the application controls, not a completed network-capture audit. A successful offline test proves the tested features can operate without a network; it cannot by itself prove absence of every attempted connection. External links and the download service's own data practices are separate.

## What stays on disk

- Normal installations store settings, imported voices, reading state, OCR caches and recovery drafts under `%LOCALAPPDATA%/Luma Reader`.
- Portable launch uses `LumaData` beside the application. An explicit `LUMA_DATA_DIR` override selects another folder.
- Reading state can contain document paths, and OCR caches and recovery drafts can contain document or note text. Local files are not encrypted by Luma. Use Windows account permissions and device encryption for protection appropriate to your computer.
- Speech uses temporary local audio files. Exported audio and saved notes remain in the locations you choose. Removing Luma preserves its user-data folder so an uninstall does not erase your work.
- The clipboard shortcut reads the text already on the clipboard when invoked. It does not monitor and submit clipboard contents to a service.

Before sharing a bug report, review it for file paths, document text and personal information. Do not attach private documents, local data folders or unredacted diagnostic files to public issues. Diagnostic audio may contain the test text used for synthesis.

## Control references

[ONNX Runtime privacy documentation](https://github.com/microsoft/onnxruntime/blob/main/docs/Privacy.md) and [Python telemetry API](https://onnxruntime.ai/docs/api/python/api_summary.html#telemetry-events). The implementation is `runtime_privacy.py`; startup-order and failure checks are in `tests/test_runtime_privacy.py`.
