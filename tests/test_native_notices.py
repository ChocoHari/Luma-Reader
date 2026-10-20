import hashlib
import io
import json
from pathlib import Path
import sys
import tarfile
import zipfile
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from native_notices import collect_notices,copy_native_notices


def fixture(root):
    folder=root/'release/local-audit/upstream-sources';folder.mkdir(parents=True)
    path=folder/'engine.tar.gz'
    entries={'engine/COPYING':b'Original licence\r\n\xff',
             'engine/README':b'Copyright and project context',
             'engine/vendor/leptonica-license.txt':b'Additional licence',
             'engine/docs/FTL.TXT':b'FreeType licence terms',
             'engine/docs/licensewizard.png':b'Unrelated example image',
             'engine/data/private.txt':b'Unrelated data must stay excluded'}
    with tarfile.open(path,'w:gz') as archive:
        for name,data in entries.items():
            member=tarfile.TarInfo(name);member.size=len(data)
            archive.addfile(member,io.BytesIO(data))
    (folder/'manifest.json').write_text(json.dumps({'archives':[{
        'file':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}]}))
    return path


def test_original_notice_bytes_and_copyright_context_survive_packaging(tmp_path):
    fixture(tmp_path)
    spec=collect_notices(tmp_path,{'engine.tar.gz'})
    assert spec['notice_count']==4
    assert spec['binary_clearance'] is False
    output=tmp_path/'package'
    rows=copy_native_notices(tmp_path,output)
    copied={r['source_member']:(output/r['file']).read_bytes() for r in rows}
    assert copied['engine/COPYING']==b'Original licence\r\n\xff'
    assert copied['engine/README']==b'Copyright and project context'
    assert copied['engine/docs/FTL.TXT']==b'FreeType licence terms'
    assert 'engine/data/private.txt' not in copied


def test_changed_notice_source_is_rejected(tmp_path):
    path=fixture(tmp_path);path.write_bytes(b'Changed archive')
    with pytest.raises(ValueError,match='source hash mismatch'):
        collect_notices(tmp_path,{'engine.tar.gz'})


def test_changed_notice_bundle_is_rejected(tmp_path):
    fixture(tmp_path);spec=collect_notices(tmp_path,{'engine.tar.gz'})
    (tmp_path/spec['file']).write_bytes(b'Changed bundle')
    with pytest.raises(ValueError,match='bundle hash mismatch'):
        copy_native_notices(tmp_path,tmp_path/'package')


def test_notice_zip_cannot_write_outside_package(tmp_path):
    evidence=tmp_path/'release/evidence';evidence.mkdir(parents=True)
    bundle=evidence/'native-source-notices.zip';data=b'Notice'
    row={'file':'../outside.txt','bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
    with zipfile.ZipFile(bundle,'w') as archive:
        archive.writestr('../outside.txt',data)
        archive.writestr('INDEX.json',json.dumps({'notices':[row]}))
    (tmp_path/'release/native-notice-manifest.json').write_text(json.dumps({
        'file':'release/evidence/native-source-notices.zip','sha256':hashlib.sha256(bundle.read_bytes()).hexdigest(),'notice_count':1}))
    with pytest.raises(ValueError,match='Unsafe'):
        copy_native_notices(tmp_path,tmp_path/'package')
    assert not (tmp_path/'outside.txt').exists()
