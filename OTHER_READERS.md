# Using Piper with other Windows readers

## Available now: copied-text reading

Run Luma Reader, select text in another app, copy it with Ctrl+C, then press Ctrl+Alt+R. Piper speaks through Luma. This works independently of the other app's voice menu and is the initial integration supplied with this build. Scanned pages still need OCR to become copyable, or can be opened directly in Luma for offline OCR.

## Native Windows voice registration: separate integration

Installing the Python Piper package does not register SAPI5/OneCore voices. A local HTTP server also does not register a Windows voice. This build does not change Windows speech registration or other apps' default settings.

A candidate bridge is [Lej77/windows-text-to-speech](https://github.com/Lej77/windows-text-to-speech). Its documentation describes an installer, a Piper DLL, matching `.onnx`/`.onnx.json` files in `piper_models`, Visual C++ runtime, and eSpeak NG data. Release availability, architecture, and model compatibility must be checked before installation. Do not assume a Windows x64 bridge can serve a 32-bit reader. A native integration is not yet installed or tested on this computer.

## Compatibility checklist

| Application | Native integration outlook | Current reliable path in this build |
|---|---|---|
| NaturalReader 16 | Test desktop Windows voice enumeration and process architecture; its FAQ refers to Windows speech settings but does not establish Piper compatibility. | Copy text → Ctrl+Alt+R |
| Adobe Acrobat | Read Out Loud documents support for installed SAPI4/5 voices. A compatible Piper SAPI bridge is a reasonable target for testing. | Open PDF in Luma, or copy text |
| Foxit Reader / Editor | Windows speech settings expose a voice selector; older official desktop documentation explicitly mentions SAPI5. Verify the installed version. | Open PDF in Luma, or copy text |
| Word / Office | Speak and Read Aloud are distinct features. Read Aloud voice availability varies by service/platform. Test Speak/default Windows voice separately; do not assume a custom SAPI voice appears in every Office voice menu. | Copy text → Ctrl+Alt+R, or open DOCX in Luma |
| Microsoft Edge | A custom SAPI bridge is not guaranteed to appear in Edge's built-in Read Aloud. Browser speech voices are not interchangeable with every desktop speech interface. | Copy selectable text → Ctrl+Alt+R |
| ONLYOFFICE Desktop Editors | Speech is a plugin-based feature; which voices appear depends on the installed plugin/runtime. No automatic custom SAPI compatibility is established. | Copy text → Ctrl+Alt+R, or open DOCX in Luma |
| SumatraPDF | Official current docs place Read Aloud in pre-release 3.7+, including SAPI and OneCore voices. Older releases can lack this feature. | Copy text → Ctrl+Alt+R, or open PDF in Luma |

## Proposed native integration test order

1. Obtain and inspect a supported bridge build and all runtime dependencies.
2. Verify 32/64-bit architecture of the reader(s) to be tested.
3. Register one Piper voice without changing the system default.
4. Test Windows SAPI enumeration and WAV synthesis first.
5. Restart NaturalReader 16 and inspect/test its voice list.
6. Test Acrobat and Foxit Read Out Loud, then Office Speak.
7. Test a SumatraPDF version that actually includes Read Aloud.
8. Record which combinations work, and provide a matching uninstall path.

## Primary documentation checked

- [NaturalReader desktop software FAQ](https://www.naturalreaders.com/softwarefaq.html)
- [Acrobat Read Out Loud](https://helpx.adobe.com/acrobat/using/reading-pdfs-reflow-accessibility-features.html)
- [Foxit Windows speech settings](https://www.foxit.com/resource-hub/user-guide/foxit-pdf-editor-for-windows/speech/)
- [Microsoft: Listen to your Word documents](https://support.microsoft.com/en-us/word/listen-to-your-word-documents)
- [ONLYOFFICE Speech plugin](https://helpcenter.onlyoffice.com/docs/userguides/plugins/Speech.aspx)
- [SumatraPDF Read Aloud](https://www.sumatrapdfreader.org/docs/Read-Aloud)

Documentation is evidence for a test plan; it is not proof that a Piper bridge works in the installed app. Native integration remains a separate outstanding step.
