# Existing Piper voice review

Reviewed 17 October 2026; Cori artifact verification added 18 October. This distinguishes dataset claims, model claims and release clearance. A repository-wide MIT tag does not erase per-voice conditions. Models are excluded by default; only the exact Cori pair reviewed in CORI_CLEARANCE.md is approved for bundling.

| Local model | Evidence found | Distribution decision |
|---|---|---|
| Aru medium | Model card cites CC BY 4.0 dataset; 12 speakers; fine-tuned from Lessac | Hold pending exact model/checkpoint provenance and required attribution. |
| Cori high | Model card and author identify public-domain material and a model trained from scratch; local model SHA-256 and config Git object match upstream | Exact pair approved with preserved author credit and model card; see CORI_CLEARANCE.md. |
| Jenny Dioco medium | Dataset README permits commercial use with the name Jenny, preferably Jenny (Dioco), visible in interfaces; local card says Lessac fine-tune | Hold this exact model until checkpoint lineage is resolved. A different author's from-scratch Jenny model is a different artifact and cannot be silently substituted. |
| Northern English Male medium | Model card cites CC BY-SA 4.0 dataset and Lessac fine-tune | Hold pending share-alike/model/checkpoint review. |
| Semaine medium | Model card cites CC BY-NC-SA 4.0 dataset; 4 speakers; Lessac fine-tune | Exclude from donation/paid product bundles absent a separately verified permission path. |

Several cards refer to a Lessac starting checkpoint. The linked Blizzard 2013 recording licence is research-only and restricts commercial uses of the recordings. This does not by itself establish the legal status of every downstream model weight, but it makes a blanket commercial clearance unjustified. No Lessac-derived model is cleared merely because it can be downloaded.

Cori author source: https://brycebeattie.com/files/tts/
The browser tool could read the author page; the evidence downloader rejected its expired TLS certificate. Certificate verification was not bypassed. The source URL, observations and retrieval issue are recorded rather than fabricating a downloaded snapshot.

Jenny dataset source: https://github.com/dioco-group/jenny-tts-dataset
Lessac dataset terms: https://www.cstr.ed.ac.uk/projects/blizzard/2013/lessac_blizzard2013/license.html
Model cards: release/evidence/piper-*-MODEL_CARD.txt, with source URLs and SHA256 hashes in sources.json.

No voice files have been deleted, modified or uploaded. No recording or generated clip is treated as Luma-owned solely because it is local. Original free/premium voice training remains a separate consent, data-rights and pilot project.
