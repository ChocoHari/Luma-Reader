# Source snapshot and binary identity

`python tools/source_package.py` creates a source ZIP from the explicit source allowlist. It contains a SHA-256 file manifest and a fingerprint of that manifest. Private directories are rejected, and files outside the allowlist are not included. Member timestamps and paths are deterministic. This provides a source snapshot, not a claim that compiler output is byte-reproducible.

The Windows builder creates the snapshot before compilation, bundles SOURCE_MANIFEST.json with the executable, then checks the source fingerprint again after compilation. If source changed while compiling, the build is rejected. The frozen diagnostic reports its bundled source fingerprint so it can be compared to the source ZIP.

The application source archive is not the entire corresponding-source obligation for all third-party binary libraries. Exact covered third-party sources, patches/build information, native notices and a user-selected distribution destination remain required before public binary release. A separately regenerated source ZIP must not be presented as matching an older executable unless their fingerprints match.

Native inspection has extracted the actual packaged FFmpeg codec configuration and licence string into release/evidence/ffmpeg-build-config.json. It reports LGPL 2.1-or-later and an FFmpeg n9.0.1 build path, with shared linking and no GPL/nonfree enable flag in that reported configuration. This does not prove that every native DLL's source and notice requirements have been met. The Qt/native gate stays pending.
