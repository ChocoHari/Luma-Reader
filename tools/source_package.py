"""Deterministic source snapshot from the reviewed explicit allowlist."""
import hashlib
import json
from pathlib import Path
import zipfile
from audit_release import validate_sources


def snapshot_sources(root):
    root=Path(root)
    spec=json.loads((root/'release/source-allowlist.json').read_text(encoding='utf-8'))
    errors=validate_sources(root,spec)
    if len(spec['files'])!=len(set(spec['files'])):errors.append('Duplicate source paths')
    if errors:raise ValueError('\n'.join(errors))
    payloads={name:(root/name).read_bytes() for name in sorted(spec['files'])}
    records=[{'path':name,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()} for name,data in payloads.items()]
    fingerprint=hashlib.sha256(json.dumps(records,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    return {'schema_version':1,'source_fingerprint':fingerprint,'files':records},payloads


def write_source_package(root):
    root=Path(root)
    manifest,payloads=snapshot_sources(root)
    serialized=json.dumps(manifest,indent=2).encode('utf-8')
    destination=root/'release/local-audit/SOURCE_MANIFEST.json'
    destination.parent.mkdir(parents=True,exist_ok=True);destination.write_bytes(serialized)
    output=root/'dist/Luma-development-source.zip';output.parent.mkdir(exist_ok=True)
    payloads['SOURCE_MANIFEST.json']=serialized
    with zipfile.ZipFile(output,'w',compression=zipfile.ZIP_DEFLATED) as archive:
        for name,data in sorted(payloads.items()):
            info=zipfile.ZipInfo('Luma-source/'+name,(2026,1,1,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED
            archive.writestr(info,data)
    return manifest


if __name__=='__main__':
    result=write_source_package(Path(__file__).resolve().parents[1])
    print(json.dumps({'source_files':len(result['files']),'source_fingerprint':result['source_fingerprint']}))
