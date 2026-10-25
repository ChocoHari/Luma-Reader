# Phase 1 decision: Luma Community licensing and distribution

Date: 17 October 2026. Status: first-party licence selected; binary release clearance remains a packaging gate.

## First-party work

Luma Community source, original Book & wave logo/vector assets, and first-party documentation use **AGPL-3.0-or-later**. LICENSE contains the complete AGPL text. NOTICE explains the scope. This does not grant new rights to imported models, speaker identities, datasets, or user content. Preserve individual third-party notices and licence terms.

This selection follows the approved open-source direction and the application's current direct use of PyMuPDF's AGPL option and Piper's GPLv3-or-later code. The application is not being represented as MIT/Apache software and is not being reclassified as proprietary simply because a future official build is paid.

## Corresponding source and paid offerings

Each released binary must identify its source revision and make corresponding source available in accordance with the applicable licences, including build scripts and modifications needed for that release. A GitHub link alone is not a substitute for actually retaining and providing the matching source.

Charging for official builds, support or updates is compatible with the open-source direction, but recipients' applicable modification/redistribution rights remain. The initial paid-edition research will therefore evaluate paid official builds, support/workflow convenience, and separately licensed original voice assets. There is no promise of exclusive, closed-source premium features under the current dependency architecture.

A future proprietary edition needs a separate review: first-party contributor rights, Piper integration, the PDF engine and all other dependencies. Moving code into a plugin or another process does not automatically remove obligations. Do not offer dual-licensing rights to upstream code Luma does not own.

## Dependency approach

- Preserve Piper/eSpeak notices and arrange matching source for their distributed binary components.
- Use only required Qt modules. The development environment's WebEngine and Qt PDF packages are not automatically release requirements. Avoid shipping them if unused.
- Retain Qt's required notices and relevant source/relinking arrangements. An isolated metadata field naming only a commercial licence file is not evidence that the installed libraries are commercially licensed.
- Inspect the actual Qt multimedia/FFmpeg DLL build, licence configuration and corresponding-source requirements before a public binary. Do not infer exact FFmpeg obligations from Python package metadata alone.
- Attribute RapidOCR and PaddleOCR, and trace the exact bundled OCR model artifacts. Apache project licences are evidence, not proof that every artifact is covered without further provenance checks.
- Copy required permissive notices for ONNX Runtime, OpenCV and transitive libraries, including their bundled native libraries.

`dependency-inventory.json` records the current Python environment. It is not a final shipped SBOM. `native-components.json` and `release-gates.json` record binary/model checks to complete against an actual packaged build.

## Voice policy

Local voices remain available to their owner. The public source tree and installer must not copy the entire local voice directory. A release voice must be explicitly included by a manifest with verified hashes, original attribution and redistribution evidence. Non-commercial or unresolved voices are excluded.

See VOICE_REVIEW.md and voice-manifest.json. The exact Cori high model/configuration pair is approved for bundling after matching upstream model SHA-256 and configuration Git object metadata. The author labels that model public domain and says it was trained from scratch. CORI_CLEARANCE.md records the evidence; builds enforce both file hashes and retain credit/model-card files. Other voices remain excluded.

## Phase boundaries

Phase 1 is complete when inventory, decisions, default exclusions, licensing files and audit tooling are in place. It is not a claim that a binary is ready to publish. Phase 5 must close artifact-specific release gates; Phase 6 must validate the actual clean package and matching source. No accounts, public uploads, purchases or speaker contacts are performed by this decision.

## Primary references

- https://github.com/pymupdf/PyMuPDF#license-and-copyright
- https://github.com/OHF-Voice/piper1-gpl
- https://doc.qt.io/qtforpython-6/licenses.html
- https://www.gnu.org/licenses/gpl-faq.en.html
- https://www.gnu.org/philosophy/selling.html
- https://github.com/RapidAI/RapidOCR/tree/v1.4.4
- https://brycebeattie.com/files/tts/
