# Installer and playback verification

18 October 2026, Windows build 26200, development host.

The normal per-user installer `Luma-0.3.0-dev-Setup.exe` compiled successfully with Inno Setup 6.7.3. Its downloaded compiler package had a valid Pyrsys B.V. Authenticode signature and the SHA-256 recorded in release/evidence/inno-compiler.json. The compiler was deployed in portable mode in temporary workspace tools. No commercial licence purchase was made. Inno's published licence permits commercial use subject to its conditions; preserve its copyright and source identity: https://jrsoftware.org/files/is/license.txt .

The actual installer candidate was tested, not merely the separate verification recipe. The test refused to run if either user/machine registry view contained an existing Luma uninstall record. It then used a fresh owned workspace directory and suppressed shortcut creation. The first sandboxed attempt exited before installation; a permitted host-level run completed.

Verified results:

- Installation created the standalone executable and bundled runtime/voice.
- The installed executable passed its diagnostic.
- Reinstalling the same version preserved a Markdown note in the separate user-data folder.
- The generated uninstaller removed the application executable.
- The user-data note remained intact with an unchanged SHA-256 after uninstall.

This proves same-version reinstallation on this host. Cancellation/interruption, a clean Windows machine and visible installer wizard review remain unverified. Test-user data was deliberately preserved. Raw local evidence is `verification/installer-lifecycle.json` and the isolated trial logs; these are excluded from public packages.

The standalone playback diagnostic synthesized a 4.39-second, 22050 Hz clip, decoded 96,768 frames through Qt Multimedia and reached EndOfMedia without an error. Output was muted. This verifies decoding/playback progression, not audible output from a physical speaker or every audio device. Raw evidence is `verification/frozen-playback-diagnostic.json`.

Commands: `python tools/build_installer.py`; `python tools/verify_installer.py --candidate`. Candidate testing modifies then removes its own per-user uninstall entry and refuses an existing installation. Without `--candidate`, the verifier compiles a separate identity without an uninstall registry entry. Both use an isolated workspace application directory.

## Version-to-version upgrade

18 October 2026: the guarded upgrade trial installed 0.3.0-dev, upgraded to 0.3.1-dev, verified the registered version changed and the executable hash changed to the current candidate, then passed the installed diagnostic. Markdown notes and settings retained their hashes through the upgrade. Uninstall removed the application and preserved user data. All eight checks passed; raw local evidence is `verification/upgrade-result.json`. This was an isolated development-host trial, not a clean-machine test.

The tested 0.3.1 installer corresponds to source fingerprint `8e18721004cd88b38ef62fa2508a04ae58ef7ef0313c5880b4e82ce584cd6f41`. The older 0.3.0 installer is retained as a test fixture.

Restricted-search-path rebuild: upgrade trial `upgrade-trial-58d27ff6` passed all eight checks against the rebuilt 0.3.1-dev installer. Its source fingerprint is `4b4a5d1caf6159af974e8ca46bcc453ac9921897c8b167f764dcabbfebf285ac`, superseding the earlier candidate above. The installed diagnostic also passed speech synthesis and muted playback. The current portable/source/installer hashes are in dist/SHA256SUMS.txt. This remains a development-host trial.

PDF-column/guide rebuild: latest trial upgrade-trial-84f19cc5 passed all eight upgrade checks with source fingerprint c6d37c8cec17b51049018e406b5950c34a17a2820baf01ea585c6d8ef441fec1. The 0.3.1 installer now contains both native/OCR column handling and corrected user documentation. Portable integrity and standalone diagnostic passed; 66 source tests passed. Current checksums: dist/SHA256SUMS.txt. No clean-machine claim.

Strict-model rebuild: upgrade-trial-d4cdd092 passed all eight checks for source fingerprint bfae296d219132fe86cc80b54ece8161e94e0d38bb65cd69dbd37115db0bdebd. The 0.3.1 installer now excludes optional unreviewed Piper ONNX weights. The separate local diagnostic passed with Python/developer search paths removed. Portable 288480914 bytes; installer 234962310 bytes. Existing development-host limits remain. Current SHA-256 values: dist/SHA256SUMS.txt.

Native notice rebuild: upgrade-trial-462e3fe7 passed all eight installer checks for source fingerprint ee049b0c5bcaf4a14fce0e4e3755c335d5f3a64f369733bf4bc5893dc2b72a95. The package contains 356 byte-verified native notices and four reviewed model paths/hashes. Local isolated-path diagnostic, portable integrity and hosted Windows run 39121054728 passed. Current checksums: dist/SHA256SUMS.txt.
