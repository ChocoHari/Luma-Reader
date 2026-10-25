"""Compare installed package bytes and runtime contents with the build audit."""
import hashlib
from pathlib import Path, PurePosixPath


def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()


def verify_installed_payload(folder,inventory):
    folder=Path(folder).resolve()
    expected={}
    for record in inventory['files']:
        name=PurePosixPath(record['path'])
        path=(folder/str(name)).resolve()
        if (name.is_absolute() or '..' in name.parts or ':' in str(name)
                or '\\' in str(name) or not path.is_relative_to(folder)):
            raise ValueError('Unsafe inventory path')
        if str(name) in expected:raise ValueError('Duplicate inventory path')
        expected[str(name)]=(path,record['sha256'])
    missing=[];changed=[]
    for name,(path,sha) in expected.items():
        if not path.is_file():missing.append(name)
        elif digest(path)!=sha:changed.append(name)
    # _internal is package-owned. User notes/portable voices in LumaData and
    # AppData are intentionally outside this scan and are never removed here.
    unexpected=[]
    for path in (folder/'_internal').rglob('*'):
        if not path.is_file() or path.suffix.lower() not in {'.dll','.pyd','.onnx'}:continue
        name=path.relative_to(folder).as_posix()
        if name not in expected:unexpected.append(name)
    return {'passed':not (missing or changed or unexpected),
            'audited_files':len(expected),'missing':sorted(missing),
            'changed':sorted(changed),'unexpected_runtime':sorted(unexpected)}
