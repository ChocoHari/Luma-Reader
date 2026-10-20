import hashlib
from pathlib import Path
import sys
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from installed_payload import verify_installed_payload


def test_old_runtime_cannot_pass_using_only_new_executable(tmp_path):
    (tmp_path/'_internal').mkdir()
    (tmp_path/'Luma.exe').write_bytes(b'new app')
    inventory={'files':[{'path':'Luma.exe','sha256':hashlib.sha256(b'new app').hexdigest()}]}
    assert verify_installed_payload(tmp_path,inventory)['passed']
    (tmp_path/'_internal/old-model.onnx').write_bytes(b'obsolete')
    result=verify_installed_payload(tmp_path,inventory)
    assert not result['passed'] and result['unexpected_runtime']==['_internal/old-model.onnx']
    (tmp_path/'_internal/old-model.onnx').unlink()
    (tmp_path/'Luma.exe').write_bytes(b'wrong app')
    assert verify_installed_payload(tmp_path,inventory)['changed']==['Luma.exe']


def test_user_data_is_preserved_and_not_mistaken_for_packaged_runtime(tmp_path):
    data=tmp_path/'LumaData/voices';data.mkdir(parents=True)
    voice=data/'my-own.onnx';voice.write_bytes(b'user voice')
    assert verify_installed_payload(tmp_path,{'files':[]})['passed']
    assert voice.read_bytes()==b'user voice'


@pytest.mark.parametrize('name',['../private.txt','C:/private.txt','/private.txt',r'..\private.txt'])
def test_unsafe_inventory_fails_before_file_access(tmp_path,name):
    with pytest.raises(ValueError):verify_installed_payload(tmp_path,{'files':[{'path':name,'sha256':'0'*64}]})


def test_installer_cleanup_is_exact_and_confined_to_old_runtime():
    import re
    source=(Path(__file__).resolve().parents[1]/'installer/obsolete-runtime.iss').read_text()
    entries=[line for line in source.splitlines() if line.startswith('Type:')]
    assert entries
    for line in entries:
        assert re.fullmatch(r'Type: files; Name: "\{app\}\\_internal\\[A-Za-z0-9_.\\-]+"',line)
        assert '..' not in line
    assert 'piper\\hebrew\\nakdimon.onnx' in source
    assert 'Qt6Quick.dll' in source
