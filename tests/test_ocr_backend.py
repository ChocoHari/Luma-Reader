import json
from pathlib import Path
from types import SimpleNamespace
import pytest
from ocr_backend import MODEL_HASHES,Engine,create_engine


def test_runtime_model_policy_matches_reviewed_upstream_evidence():
    root=Path(__file__).resolve().parents[1]
    evidence=json.loads((root/'release/evidence/ocr-upstream-metadata.json').read_text())
    assert MODEL_HASHES=={r['file']:r['sha256'] for r in evidence['local_comparison']}


def test_missing_or_changed_models_fail_before_engine_import(tmp_path,monkeypatch):
    import builtins
    original=builtins.__import__
    def guarded_import(name,*args,**kwargs):
        if name=='rapidocr':raise AssertionError('OCR engine imported before model validation')
        return original(name,*args,**kwargs)
    monkeypatch.setattr(builtins,'__import__',guarded_import)
    with pytest.raises(RuntimeError,match='model missing'):
        create_engine(tmp_path)
    first=next(iter(MODEL_HASHES))
    (tmp_path/first).write_bytes(b'changed model')
    with pytest.raises(RuntimeError,match='integrity check'):
        create_engine(tmp_path)


def test_output_adapter_preserves_line_coordinates_text_and_score():
    box=[[1,2],[8,2],[8,9],[1,9]]
    result=SimpleNamespace(boxes=[box],txts=('A line',),scores=(0.95,),elapse_list=[1,2,3])
    rows,timings=Engine(lambda image:result)(object())
    assert rows==[(box,'A line',0.95)]
    assert timings==[1,2,3]
    assert Engine(lambda image:SimpleNamespace(boxes=None,txts=None,scores=None))(object())==([],None)
