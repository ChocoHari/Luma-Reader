import importlib.util
import json
from pathlib import Path
import sys
import zipfile
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from source_package import snapshot_sources,write_source_package,validate_public_notes


def fixture_source(root):
    (root/'release').mkdir()
    (root/'app.py').write_text('print("original public sample")')
    (root/'private.txt').write_text('private data')
    spec={'files':['app.py','release/source-allowlist.json'],'excluded_directories':['data']}
    (root/'release/source-allowlist.json').write_text(json.dumps(spec))


def test_source_snapshot_excludes_private_files_and_tracks_changes(tmp_path):
    fixture_source(tmp_path)
    first=write_source_package(tmp_path)
    with zipfile.ZipFile(tmp_path/'dist/Luma-development-source.zip') as archive:
        assert 'Luma-source/private.txt' not in archive.namelist()
        archived=json.loads(archive.read('Luma-source/SOURCE_MANIFEST.json'))
        assert archived['source_fingerprint']==first['source_fingerprint']
    (tmp_path/'app.py').write_text('print("changed")')
    assert snapshot_sources(tmp_path)[0]['source_fingerprint']!=first['source_fingerprint']


def test_source_snapshot_rejects_forbidden_allowlist_entry(tmp_path):
    fixture_source(tmp_path)
    path=tmp_path/'release/source-allowlist.json'
    spec=json.loads(path.read_text());spec['files'].append('data/settings.json')
    path.write_text(json.dumps(spec))
    with pytest.raises(ValueError,match='Unsafe'):snapshot_sources(tmp_path)


@pytest.mark.parametrize('text',['Free disk: C 11.9 GB, D 110.7 GB',
    '4 physical cores / 8 logical processors','MemoryGB: 19.8',
    'VirtualizationFirmwareEnabled: True'])
def test_public_notes_reject_host_capacity_details(text):
    with pytest.raises(ValueError,match='Private host-capacity'):
        validate_public_notes({'RELEASE_CHECKLIST.txt':text.encode()})


def test_public_notes_allow_generic_test_status_and_documented_storage():
    validate_public_notes({'release/BUILD_WINDOWS.md':
        b'Clean Windows test pending. Store notes in %LOCALAPPDATA%/Luma Reader.'})
