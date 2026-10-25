import hashlib
from pathlib import Path
import sys
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from fetch_build_voice import fetch_verified
from check_release import REQUIRED,public_blockers


def test_release_policy_rejects_missing_or_pending_gate_even_with_approval():
    assert public_blockers({'public_binary_approved':True,'gates':[]})
    gates=[{'id':name,'status':'passed'} for name in REQUIRED]
    assert not public_blockers({'public_binary_approved':True,'gates':gates})
    gates[0]['status']='pending'
    assert public_blockers({'public_binary_approved':True,'gates':gates})
    assert public_blockers({'public_binary_approved':False,'gates':gates})


def test_build_voice_hash_failure_does_not_replace_local_files(tmp_path):
    upstream=tmp_path/'upstream';upstream.write_bytes(b'example reviewed bytes')
    target=tmp_path/'voice.onnx'
    expected=hashlib.sha256(upstream.read_bytes()).hexdigest()
    fetch_verified(upstream.as_uri(),target,expected)
    assert target.read_bytes()==upstream.read_bytes()
    upstream.write_bytes(b'changed upstream')
    fetch_verified(upstream.as_uri(),target,expected)
    assert target.read_bytes()==b'example reviewed bytes'
    target.write_bytes(b'user model')
    with pytest.raises(ValueError,match='refusing to overwrite'):
        fetch_verified(upstream.as_uri(),target,expected)
    target.unlink()
    with pytest.raises(ValueError,match='hash mismatch'):
        fetch_verified(upstream.as_uri(),target,expected)
    assert not target.exists()
    assert not list(tmp_path.glob('*.download'))


def test_microsoft_runtime_clearance_cannot_be_omitted_or_left_pending():
    gates=[{'id':name,'status':'passed'} for name in REQUIRED if name!='microsoft-runtime']
    config={'public_binary_approved':True,'gates':gates}
    assert 'Missing gate: microsoft-runtime' in public_blockers(config)
    gates.append({'id':'microsoft-runtime','status':'pending'})
    assert 'Pending gate: microsoft-runtime' in public_blockers(config)
