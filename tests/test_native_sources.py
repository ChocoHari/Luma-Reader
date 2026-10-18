import hashlib
from pathlib import Path
import sys
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from fetch_native_sources import verify_hash


def test_source_archive_hash_rejects_changed_cached_bytes(tmp_path):
    archive=tmp_path/'source.tar.gz'
    archive.write_bytes(b'expected archive bytes')
    expected=hashlib.sha256(archive.read_bytes()).hexdigest()
    assert verify_hash(archive,expected)==expected
    archive.write_bytes(b'changed archive bytes')
    with pytest.raises(RuntimeError,match='Source archive hash mismatch'):
        verify_hash(archive,expected)
