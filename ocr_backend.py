"""Offline OCR using explicitly reviewed local models and a maintained engine."""
import hashlib
from pathlib import Path

from runtime_paths import ASSET_ROOT
from runtime_privacy import prepare_inference_runtime

MODEL_HASHES={
    'ch_PP-OCRv4_det_infer.onnx':'d2a7720d45a54257208b1e13e36a8479894cb74155a5efe29462512d42f49da9',
    'ch_PP-OCRv4_rec_infer.onnx':'48fc40f24f6d2a207a2b1091d3437eb3cc3eb6b676dc3ef9c37384005483683b',
    'ch_ppocr_mobile_v2.0_cls_infer.onnx':'e47acedf663230f8863ff1ab0e64dd2d82b838fceb5957146dab185a89d6215c',
}


def verified_models(folder=None):
    folder=Path(folder) if folder is not None else ASSET_ROOT/'ocr_models'
    paths={}
    for name,expected in MODEL_HASHES.items():
        path=folder/name
        if not path.is_file():
            raise RuntimeError(f'Local OCR model missing: {name}. Reinstall Luma or rerun development setup.')
        with path.open('rb') as stream:actual=hashlib.file_digest(stream,'sha256').hexdigest()
        if actual!=expected:
            raise RuntimeError(f'Local OCR model failed its integrity check: {name}. Reinstall Luma.')
        paths[name]=path
    return paths


class Engine:
    """Retain the reader's line/score interface across the upstream API change."""
    def __init__(self,backend):
        self.backend=backend

    def __call__(self,image):
        result=self.backend(image)
        if result.boxes is None or result.txts is None or result.scores is None:
            return [],getattr(result,'elapse_list',None)
        rows=[(box.tolist() if hasattr(box,'tolist') else box,str(text),float(score))
              for box,text,score in zip(result.boxes,result.txts,result.scores)]
        return rows,getattr(result,'elapse_list',None)


def create_engine(folder=None):
    paths=verified_models(folder)
    prepare_inference_runtime()
    from rapidocr import RapidOCR,OCRVersion,ModelType,EngineType
    params={
        'Global.log_level':'warning',
        'Global.model_root_dir':str(next(iter(paths.values())).parent),
        'EngineConfig.onnxruntime.intra_op_num_threads':2,
        'EngineConfig.onnxruntime.inter_op_num_threads':2,
    }
    for stage,name in [('Det','ch_PP-OCRv4_det_infer.onnx'),
                       ('Cls','ch_ppocr_mobile_v2.0_cls_infer.onnx'),
                       ('Rec','ch_PP-OCRv4_rec_infer.onnx')]:
        params[stage+'.model_path']=str(paths[name])
        params[stage+'.engine_type']=EngineType.ONNXRUNTIME
        params[stage+'.ocr_version']=OCRVersion.PPOCRV4
        params[stage+'.model_type']=ModelType.MOBILE
    return Engine(RapidOCR(params=params))
