from pathlib import Path
import sys
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from model_inventory import verify_model_allowlist


def test_model_inventory_rejects_extra_weights_even_with_approved_basename(tmp_path):
    approved=tmp_path/'voices/reviewed.onnx'
    approved.parent.mkdir();approved.write_bytes(b'reviewed')
    assert verify_model_allowlist(tmp_path,{'voices/reviewed.onnx'})==['voices/reviewed.onnx']
    extra=tmp_path/'optional/reviewed.ONNX'
    extra.parent.mkdir();extra.write_bytes(b'unreviewed')
    with pytest.raises(RuntimeError,match='unexpected='):
        verify_model_allowlist(tmp_path,{'voices/reviewed.onnx'})


def test_model_inventory_requires_every_reviewed_model(tmp_path):
    with pytest.raises(RuntimeError,match='missing='):
        verify_model_allowlist(tmp_path,{'voices/reviewed.onnx'})
