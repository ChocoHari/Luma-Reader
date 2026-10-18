import importlib.util
from pathlib import Path
import pytest
import zipfile

spec=importlib.util.spec_from_file_location('archive_build',Path(__file__).resolve().parents[1]/'tools/archive_build.py')
archive=importlib.util.module_from_spec(spec);spec.loader.exec_module(archive)


def test_archive_matches_audit_and_is_repeatable(tmp_path):
    folder=tmp_path/'app';folder.mkdir()
    file=folder/'Luma.exe';file.write_bytes(b'original fixture')
    inventory={'files':[{'path':'Luma.exe','sha256':archive.digest(file)}]}
    a=tmp_path/'a.zip';b=tmp_path/'b.zip'
    assert archive.archive_build(folder,inventory,a)==archive.archive_build(folder,inventory,b)
    with zipfile.ZipFile(a) as package:assert package.read('Luma/Luma.exe')==b'original fixture'
    file.write_bytes(b'changed')
    with pytest.raises(ValueError,match='changed'):archive.archive_build(folder,inventory,a)


def test_archive_rejects_unreviewed_file(tmp_path):
    folder=tmp_path/'app';folder.mkdir();(folder/'private.txt').write_text('private')
    with pytest.raises(ValueError,match='contents changed'):
        archive.archive_build(folder,{'files':[]},tmp_path/'output.zip')
