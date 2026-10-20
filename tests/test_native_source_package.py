import hashlib
import json
from pathlib import Path
import sys
import zipfile
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from package_native_sources import package_sources


def fixture(root,name='source.tar.gz'):
    folder=root/'release/local-audit/upstream-sources';folder.mkdir(parents=True)
    payload=b'Original upstream source archive bytes'
    (folder/'source.tar.gz').write_bytes(payload)
    (folder/'manifest.json').write_text(json.dumps({'archives':[{
        'file':name,'sha256':hashlib.sha256(payload).hexdigest(),'bytes':len(payload)}]}))
    (root/'release/NATIVE_SOURCE_REVIEW.md').write_text('Review remains pending.')
    (root/'private.txt').write_text('Private document')
    return folder


def test_source_review_bundle_excludes_private_files_and_retains_status(tmp_path):
    fixture(tmp_path)
    result=package_sources(tmp_path,{'source.tar.gz'})
    assert not result['publication_approved']
    with zipfile.ZipFile(tmp_path/'dist'/result['archive']) as archive:
        assert 'upstream/source.tar.gz' in archive.namelist()
        assert all('private.txt' not in name for name in archive.namelist())
        assert json.loads(archive.read('REVIEW_STATUS.json'))['completeness_verified'] is False


def test_source_review_rejects_path_traversal(tmp_path):
    fixture(tmp_path,'../private.txt')
    with pytest.raises(ValueError,match='Unsafe'):
        package_sources(tmp_path,{'../private.txt'})


def test_source_review_rejects_changed_archive_preserving_existing_bundle(tmp_path):
    folder=fixture(tmp_path)
    package_sources(tmp_path,{'source.tar.gz'})
    output=tmp_path/'dist/Luma-upstream-source-review.zip';before=output.read_bytes()
    (folder/'source.tar.gz').write_bytes(b'Changed source')
    with pytest.raises(ValueError,match='changed'):
        package_sources(tmp_path,{'source.tar.gz'})
    assert output.read_bytes()==before


def test_source_review_requires_complete_explicit_archive_set(tmp_path):
    fixture(tmp_path)
    with pytest.raises(ValueError,match='required archives'):
        package_sources(tmp_path,{'source.tar.gz','missing.tar.gz'})
