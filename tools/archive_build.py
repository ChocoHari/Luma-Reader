"""Archive only the audited build, rejecting post-audit additions or changes."""
import hashlib
import json
from pathlib import Path,PurePosixPath
import zipfile


def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()


def archive_build(folder,inventory,output):
    folder=Path(folder).resolve();output=Path(output)
    names={record['path'] for record in inventory['files']}
    actual={p.relative_to(folder).as_posix() for p in folder.rglob('*') if p.is_file()}
    if names!=actual:raise ValueError('Build contents changed after audit')
    for record in inventory['files']:
        name=PurePosixPath(record['path'])
        path=(folder/str(name)).resolve()
        if name.is_absolute() or '..' in name.parts or ':' in str(name) or not path.is_relative_to(folder):
            raise ValueError('Unsafe archive path')
        if digest(path)!=record['sha256']:raise ValueError(f'Build file changed: {name}')
    with zipfile.ZipFile(output,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=5) as archive:
        for name in sorted(names):
            info=zipfile.ZipInfo('Luma/'+name,date_time=(2026,1,1,0,0,0))
            info.compress_type=zipfile.ZIP_DEFLATED
            archive.writestr(info,(folder/name).read_bytes(),compresslevel=5)
    with zipfile.ZipFile(output) as archive:
        if archive.testzip() is not None:raise ValueError('Archive integrity check failed')
    return digest(output)


if __name__=='__main__':
    root=Path(__file__).resolve().parents[1]
    report=json.loads((root/'release/local-audit/binary-inventory.json').read_text())
    target=root/'dist/Luma-development-portable.zip'
    value=archive_build(root/'dist/Luma',report,target)
    (root/'dist/SHA256SUMS.txt').write_text(f'{value}  {target.name}\n',encoding='utf-8')
    print(json.dumps({'archive':target.name,'bytes':target.stat().st_size,'sha256':value,'integrity':'passed'}))
