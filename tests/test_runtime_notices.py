from pathlib import Path
import sys
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from runtime_notices import copy_python_notice


def test_runtime_notice_preserves_full_interpreter_licence(tmp_path):
    interpreter = tmp_path / 'interpreter'
    interpreter.mkdir()
    payload = b'PSF licence\r\nBundled third-party notices\r\n'
    (interpreter / 'LICENSE.txt').write_bytes(payload)
    output = tmp_path / 'package'
    record = copy_python_notice(output, interpreter, '3.test')
    assert (output / record['file']).read_bytes() == payload
    assert record['version'] == '3.test'
    assert len(record['sha256']) == 64


@pytest.mark.parametrize('payload', [None, b'  \r\n'])
def test_runtime_notice_blocks_missing_or_empty_licence(tmp_path, payload):
    if payload is not None:
        (tmp_path / 'LICENSE.txt').write_bytes(payload)
    with pytest.raises(RuntimeError, match='Python runtime LICENSE.txt'):
        copy_python_notice(tmp_path / 'package', tmp_path)
