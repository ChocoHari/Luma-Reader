# Bundled OCR model provenance and attribution

Reviewed 18 October 2026. The three unmodified ONNX artifacts bundled with rapidocr-onnxruntime 1.4.4 match the SWHL/RapidOCR upstream model repository at immutable revision `1cfba2e90fc938db55889873735088de210cc173`. That repository declares Apache-2.0. The model weights originate from Baidu/PaddleOCR; RapidOCR conversion and packaging work belongs to the RapidOCR authors. Luma claims neither ownership nor endorsement.

| Local artifact | Upstream path | SHA-256 |
|---|---|---|
| ch_PP-OCRv4_det_infer.onnx | PP-OCRv4/ch_PP-OCRv4_det_infer.onnx | d2a7720d45a54257208b1e13e36a8479894cb74155a5efe29462512d42f49da9 |
| ch_PP-OCRv4_rec_infer.onnx | PP-OCRv4/ch_PP-OCRv4_rec_infer.onnx | 48fc40f24f6d2a207a2b1091d3437eb3cc3eb6b676dc3ef9c37384005483683b |
| ch_ppocr_mobile_v2.0_cls_infer.onnx | PP-OCRv1/ch_ppocr_mobile_v2.0_cls_infer.onnx | e47acedf663230f8863ff1ab0e64dd2d82b838fceb5957146dab185a89d6215c |

The full Apache-2.0 text is included alongside this notice as PaddleOCR-Apache-2.0.txt. These are upstream converted artifacts, unchanged by Luma. Metadata and byte comparisons are preserved in ocr-upstream-metadata.json. Builds reject mismatched hashes.

Sources:

- https://huggingface.co/SWHL/RapidOCR/tree/1cfba2e90fc938db55889873735088de210cc173
- https://github.com/PaddlePaddle/PaddleOCR
- https://rapidai.github.io/RapidOCRDocs/main/en/model_licenses/

The current RapidOCR model notice explicitly covers the classifier hash and newer PP-OCRv6 models. It is not used as blanket clearance for the older PP-OCRv4 models; those identities and licence declaration were checked against their own upstream repository. Inference libraries and other assets retain their separate terms. This review covers these exact artifacts only.
