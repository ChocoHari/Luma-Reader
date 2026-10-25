"""Preserve indexed upstream notice bytes without executing source archives."""
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import tarfile
import tempfile
import zipfile


def sha(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def collect_notices(root,required_archives):
    root=Path(root);folder=root/'release/local-audit/upstream-sources'
    manifest=json.loads((folder/'manifest.json').read_text())
    rows=manifest['archives'];names=[r['file'] for r in rows]
    if len(names)!=len(set(names)) or set(names)!=set(required_archives):raise ValueError('Unexpected notice source set')
    payloads={};records=[]
    for number,row in enumerate(sorted(rows,key=lambda r:r['file'])):
        name=row['file']
        if not name or name in ('.','..') or any(c in name for c in '/\\:'):raise ValueError('Unsafe notice source path')
        source=folder/name
        if source.is_symlink() or sha(source)!=row['sha256']:raise ValueError('Notice source hash mismatch')
        with tarfile.open(source) as archive:
            for member in sorted(archive.getmembers(),key=lambda m:m.name):
                path=PurePosixPath(member.name);base=path.name.upper()
                chosen=(bool(re.match(r'^(LICENSES?|LICENCES?|COPYING|NOTICES?|AUTHORS?|COPYRIGHTS?)([._-]|$)',base))
                        or bool(re.match(r'^(FTL|GPL(V?[0-9])?|LGPL(V?[0-9])?|APACHE|BSD|MIT|UNICODE|LEGAL)([._-]|$)',base))
                        or '-LICENSE' in base or '-LICENCE' in base
                        or 'LICENSES' in [p.upper() for p in path.parts]
                        or len(path.parts)==2 and base.startswith('README'))
                if path.suffix.lower() in {'.png','.jpg','.jpeg','.gif','.bmp','.svg','.ico','.woff','.ttf','.otf','.cpp','.c','.h','.qml','.py','.ui'}:
                    chosen=False
                if not member.isfile() or not chosen:continue
                if member.size>4*1024*1024:raise ValueError('Notice requires manual size review')
                data=archive.extractfile(member).read()
                safe=re.sub(r'[^A-Za-z0-9._-]','_',path.name)[:64]
                target=f'{number:02d}-{name.split("-")[0]}/{len(records):04d}-{safe}'
                payloads[target]=data
                records.append({'file':target,'source_archive':name,'source_member':member.name,
                                'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)})
    evidence=root/'release/evidence';evidence.mkdir(parents=True,exist_ok=True)
    output=evidence/'native-source-notices.zip'
    with tempfile.NamedTemporaryFile(dir=evidence,suffix='.zip.partial',delete=False) as stream:partial=Path(stream.name)
    try:
        with zipfile.ZipFile(partial,'w',compression=zipfile.ZIP_DEFLATED) as archive:
            payloads['INDEX.json']=json.dumps({'scope':'Notices retained from release-pinned source archives; binary mapping review remains pending','notices':records},indent=2).encode()
            for name,data in sorted(payloads.items()):
                info=zipfile.ZipInfo(name,(2026,1,1,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED
                archive.writestr(info,data)
        partial.replace(output)
    finally:partial.unlink(missing_ok=True)
    result={'schema_version':1,'file':'release/evidence/native-source-notices.zip','sha256':sha(output),
            'notice_count':len(records),'source_archive_count':len(rows),'binary_clearance':False}
    (root/'release/native-notice-manifest.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    return result


def copy_native_notices(root,output):
    root,output=Path(root),Path(output)
    spec=json.loads((root/'release/native-notice-manifest.json').read_text())
    source=root/spec['file']
    if not source.resolve().is_relative_to(root.resolve()) or sha(source)!=spec['sha256']:
        raise ValueError('Native notice bundle hash mismatch')
    prepared=[]
    with zipfile.ZipFile(source) as archive:
        records=json.loads(archive.read('INDEX.json'))['notices']
        if len(records)!=spec['notice_count']:raise ValueError('Native notice count mismatch')
        names=[r['file'] for r in records]
        if len(names)!=len(set(n.casefold() for n in names)) or sorted(archive.namelist())!=sorted(names+['INDEX.json']):
            raise ValueError('Unexpected native notice entries')
        for row in records:
            name=row['file'];path=PurePosixPath(name)
            if not name or path.as_posix()!=name or path.name in ('.','..') or path.is_absolute() or '..' in path.parts or any(c in name for c in '\\:'):
                raise ValueError('Unsafe native notice path')
            data=archive.read(name)
            if len(data)!=row['bytes'] or hashlib.sha256(data).hexdigest()!=row['sha256']:
                raise ValueError('Native notice bytes changed')
            target=output/'third-party-notices/native-sources'/name
            if not target.resolve().is_relative_to(output.resolve()):raise ValueError('Unsafe native notice destination')
            prepared.append((target,data,row))
    result=[]
    for target,data,row in prepared:
        target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
        result.append({'package':'Native source notices','version':'release-pinned',
                       **row,'file':target.relative_to(output).as_posix()})
    index=output/'third-party-notices/native-sources/INDEX.json'
    index.parent.mkdir(parents=True,exist_ok=True)
    index.write_text(json.dumps({'scope':'Original source notices; binary mapping review remains pending','notices':result},indent=2),encoding='utf-8')
    return result


if __name__=='__main__':
    from fetch_native_sources import ROOT,SOURCES
    print(json.dumps(collect_notices(ROOT,{r[0] for r in SOURCES})))
