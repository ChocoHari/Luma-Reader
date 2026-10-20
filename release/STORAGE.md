# Standalone storage layout

Application assets are read from the application directory. Writable settings, OCR caches, recovery drafts, imported voices, locks and logs use `%LOCALAPPDATA%/Luma Reader` by default. Notes and audio export dialogs start in the user's Documents folder when it exists.

At normal startup, known JSON settings, OCR and recovery files from the old adjacent `data` folder are copied once into user storage. Existing destination files are preserved, originals remain, and a completion marker prevents deleted recovery drafts being imported again. Source documents and logs are not migrated. Downloaded voices in the existing project `Piper Voices` folder remain discoverable; newly imported voices go into the writable user voice folder. A packaged cleared voice may be placed in the read-only `voices` asset folder.

For controlled deployments, `LUMA_DATA_DIR` selects an explicit writable data directory. `LUMA_PORTABLE=1` selects `Luma Data` beside the executable. The explicit directory takes precedence. A portable package still needs a launcher or executable setting this option; that packaging step is pending.

These storage changes are the first part of Phase 5. They do not constitute a standalone executable or installer. Build tooling, actual bundled-component review, update/uninstall tests and clean-machine testing remain required.
