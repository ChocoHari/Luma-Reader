# Original Luma voice — proposed pilot only

No training, recording session, model download or paid compute is authorised by this document. The existing Cori voice remains third-party. Pilot approval must identify the speaker, language/accent, rights, available hardware, budget and release terms.

## Recommended first experiment

Start with one consenting adult speaker and Piper, keeping the consumer reader's small offline runtime. Use original short scripts. Begin with a 20–30 minute recording-quality pilot, not a promise that this amount will produce a release-quality voice. Listen for room echo, background noise, clipping, consistent distance, transcript accuracy and vocal fatigue before expanding the corpus. If the pilot is usable, propose the next recording batch with a measured workload.

Capture lossless unprocessed originals and retain a separate cleaned copy. Keep filenames, exact transcripts and provenance in a dataset manifest. Use separate training/validation/test utterances; evaluate long passages and unseen names/numbers rather than memorised training sentences. Speaker records belong in protected storage, not the public repository.

## Rights and consent gate

The speaker must knowingly agree to the intended synthesis, public voice-model redistribution, commercial/premium use if applicable, attribution, compensation, permitted uses, retention and a withdrawal process before recording. Explain that already distributed open weights cannot be reliably recalled. Obtain a reviewed written agreement; this proposal is not one. Do not use celebrities, classmates, lecturers or downloaded recordings without appropriate permission. Script text and recordings need their own clear rights.

Review every starting checkpoint independently. A code licence does not clear a checkpoint's training data or a speaker's likeness. Prefer training from scratch or a reviewed checkpoint whose provenance and redistribution terms are adequate. The current approved Cori ONNX inference artifact is not automatically a training checkpoint or an endorsement for derivative branding.

## Training experiment and measurements

Piper's official training guide describes paired audio/transcript metadata, optional checkpoint-based training and ONNX/config export. Use a separate training environment; do not add training libraries to the reader installer. Pin the exact repository revision and record configuration, seeds, dataset hashes and checkpoint lineage. Stop at the agreed experiment limit.

Measure intelligibility, pronunciation errors, repetitions/skipped words, first-audio delay, real-time factor, peak RAM/VRAM, model size and sustained reading stability on an ordinary target computer. Use blind preference comparisons with the existing Cori baseline where practical. Record results as observations, not a universal naturalness score. The pilot succeeds only if the speaker approves the representation and the measured runtime/quality meet a pre-agreed threshold.

## Qwen comparison — later, optional

Official Qwen3-TTS documentation describes 0.6B/1.7B model variants and base-model fine-tuning. Treat Qwen as a separate optional engine experiment. Verify exact code, model and tokenizer terms again; assess dependencies, download size, GPU/CPU latency and long-form stability before offering it to users. Do not equate a permissive model licence with permission to imitate a person. Do not advertise a synthetic voice-design output as an original consented human recording dataset.

No cost or hardware guarantee is made here. First inventory the available machine, run a bounded benchmark only after approval, then price any paid compute. Do not rent hardware, buy microphones, collect recordings or launch training until scope and budget are agreed.

## Deliverables after an approved pilot

Recording-quality report, dataset/consent provenance checklist, exact training configuration, held-out evaluation report, speaker approval, redistribution-ready model card, intended licence/credits and a costed go/no-go recommendation. A usable sample is not a release-ready model.

Primary references checked 18 October 2026:

- https://github.com/OHF-Voice/piper1-gpl/blob/main/docs/TRAINING.md
- https://github.com/OHF-Voice/piper1-gpl/blob/main/docs/VOICES.md
- https://github.com/QwenLM/Qwen3-TTS
- https://huggingface.co/Qwen/Qwen3-TTS-12Hz-0.6B-Base
