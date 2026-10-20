# Installer and upgrade verification

These are isolated development-host checks. They do not prove clean-Windows compatibility, audible output from every physical device, interrupted-install recovery or visible wizard behavior.

## Current procedure

`python tools/build_installer.py` builds the installer. `python tools/verify_installer.py --candidate` derives its filename from the default version in `installer/Luma.iss`, refuses any pre-existing registered Luma installation, installs into a fresh workspace folder, checks the installed diagnostic, reinstalls and uninstalls. User data remains in a separate test folder. Without `--candidate`, a separate verification identity is compiled. The old 0.3.0 installer is retained only as a version-upgrade fixture.

The verifier compares every audited package file by SHA-256 and rejects additional DLL/PYD/ONNX files inside the package-owned `_internal` folder. Checking only the executable or a successful diagnostic is insufficient: obsolete optional models/libraries can otherwise remain unnoticed after upgrade. User folders such as LumaData and AppData are outside this runtime scan.

`python tools/verify_upgrade.py` installs the retained 0.3.0 fixture, upgrades to 0.3.1 and checks registered versions, executable replacement, the complete audited payload and installed diagnostics. It also seeds harmless old-runtime sentinels at the former Hebrew model and Qt Quick paths, verifying that the installer removes them. A portable user-voice sentinel in LumaData must survive both upgrade and uninstall, as must the separate note/settings files. Sentinels are never executed as libraries or loaded as models.

## Obsolete package files

`installer/obsolete-runtime.iss` contains exact former package-owned file paths. The installer removes only these listed files; there are no directory deletion rules or recursive wildcards. The list covers the old ICU shadow copies, Qt PDF and VirtualKeyboard/QML/Quick group, the old OpenCV video helper and optional Hebrew/Arabic Piper models. Imported voices and notes are not listed. Unit checks reject broad/unsafe cleanup patterns. The runtime inventory comparison detects additional stale libraries requiring separate review instead of deleting them automatically.

## Evidence and status

The previous privacy candidate (source fingerprint 803286b442b52efc038d22ac95cf0ff16b0282cb8785395beb0aaa0ea3bd7e1d) passed install, installed diagnostic, reinstall and uninstall with a retained note in trial installer-trial-d0cabe5d. That five-check test predates the complete installed-payload comparison and does not prove obsolete-file cleanup.

An earlier minimal candidate passed the original eight upgrade checks in upgrade-trial-2062888d. Its executable/notes checks do not establish that removed runtime files were absent after upgrading. The stricter upgrade check must pass before claiming that behavior.

The first stricter trial (upgrade-trial-01bd2e8b) found 46 additional legacy DLLs left from the original development package. All current audited bytes matched, old Qt/model sentinels were removed and user data survived, but the full installed-payload check correctly failed. The installer now lists those 46 observed former package paths explicitly as well. A repeat stricter trial is required before claiming upgrade cleanup complete. Current trial results are recorded in RELEASE_CHECKLIST.txt, with raw private reports under verification/installer-lifecycle.json and verification/upgrade-result.json. These reports and local test paths are excluded from public source packages.

## Still required

- A clean Windows guest/computer without development packages, using the original private sample kit.
- Visible wizard inspection and cancellation before installation.
- Interrupted installation/recovery in a disposable guest snapshot.
- Physical audible playback and relevant audio/display devices.

No passing development-host report clears native redistribution/source obligations or authorizes a public binary release. Package hashes are in dist/SHA256SUMS.txt.
