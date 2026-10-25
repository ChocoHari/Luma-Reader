# Cori high: exact artifact review

Reviewed 18 October 2026 for Luma's bundled default voice. This is a third-party voice, not Luma's planned original voice.

The model author's page identifies Cori high as trained from scratch for 500 epochs on approximately 24 hours of LibriVox recordings and labels the model public domain: https://brycebeattie.com/files/tts/ . The Piper model card identifies the same author, training description and public-domain dataset. The browser retrieved the author statement; the earlier direct TLS downloader issue is preserved in VOICE_REVIEW.md.

The exact local model matches the Hugging Face LFS SHA-256 metadata:

- File: en_GB-cori-high.onnx
- Bytes: 114219352
- SHA-256: 470b4dd634c98f8a4850d7626ffc3dfc90774628eeef6605a6dd8f88f30a5903
- Configuration SHA-256: 9e7fb5b5671612c22f3c81cbe46c1ae87b031a4632bcb509e499dad6f1e2adec
- Configuration Git blob SHA-1: ec08ff84191b2e7fe7dd91928b6068bca12ff81b

Evidence: release/evidence/cori-upstream-tree.json and release/evidence/piper-cori-MODEL_CARD.txt. Metadata endpoint: https://huggingface.co/api/models/rhasspy/piper-voices/tree/main/en/en_GB/cori/high?expand=true . Both model and configuration matched independently. The configuration Git blob hash includes the standard Git blob header.

Decision: allow this exact model/configuration pair in Luma builds, retaining the model card and author credit. Do not apply this decision to other Cori variants or other voices. A hash change requires review again. Author: Bryce Beattie; source recordings: LibriVox contributors. No author endorsement is claimed. The application's remaining binary-release gates still apply.
