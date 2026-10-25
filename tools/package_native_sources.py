"""Create a local review bundle from explicit, hash-checked upstream archives."""
import hashlib
import json
from pathlib import Path
import tempfile
import zipfile


def package_sources(root, required_archives):
    root=Path(root)
    folder=root/'release/local-audit/upstream-sources'
    manifest=json.loads((folder/'manifest.json').read_text(encoding='utf-8'))
    rows=manifest['archives']
    names=[row['file'] for row in rows]
    if len(names)!=len(set(name.casefold() for name in names)):
        raise ValueError('Duplicate upstream archive names')
    if set(names)!=set(required_archives):
        raise ValueError('Upstream source set does not match required archives')
    for row in rows:
        name=row['file']
        if not name or name in ('.','..') or any(c in name for c in '/\\:'):
            raise ValueError('Unsafe upstream archive path')
        source=folder/name
        if source.is_symlink() or not source.resolve().is_relative_to(folder.resolve()):
            raise ValueError('Unsafe upstream archive origin')
        with source.open('rb') as stream:
            value=hashlib.file_digest(stream,'sha256').hexdigest()
        if value!=row['sha256'] or source.stat().st_size!=row['bytes']:
            raise ValueError('Upstream source archive changed: '+name)
    destination=root/'dist';destination.mkdir(exist_ok=True)
    output=destination/'Luma-upstream-source-review.zip'
    with tempfile.NamedTemporaryFile(dir=destination,suffix='.zip.partial',delete=False) as stream:
        partial=Path(stream.name)
    def info(name):
        value=zipfile.ZipInfo(name,(2026,1,1,0,0,0));value.compress_type=zipfile.ZIP_STORED
        return value
    try:
        with zipfile.ZipFile(partial,'w') as archive:
            for row in sorted(rows,key=lambda r:r['file']):
                digest=hashlib.sha256();size=0
                with (folder/row['file']).open('rb') as source,archive.open(info('upstream/'+row['file']),'w') as target:
                    while chunk:=source.read(1024*1024):
                        target.write(chunk);digest.update(chunk);size+=len(chunk)
                if digest.hexdigest()!=row['sha256'] or size!=row['bytes']:
                    raise ValueError('Source changed while bundling: '+row['file'])
            archive.writestr(info('SOURCE_INVENTORY.json'),json.dumps(manifest,indent=2))
            archive.writestr(info('REVIEW_STATUS.json'),json.dumps({
                'publication_approved':False,'completeness_verified':False,
                'archive_count':len(rows),'purpose':'Local source and licence review; not release clearance'},indent=2))
            archive.writestr(info('NATIVE_SOURCE_REVIEW.md'),(root/'release/NATIVE_SOURCE_REVIEW.md').read_bytes())
        with zipfile.ZipFile(partial) as archive:
            if archive.testzip() is not None:raise ValueError('Source review ZIP integrity failure')
        partial.replace(output)
    finally:
        partial.unlink(missing_ok=True)
    with output.open('rb') as stream:
        value=hashlib.file_digest(stream,'sha256').hexdigest()
    output.with_suffix('.sha256').write_text(value+'  '+output.name+'\n',encoding='utf-8')
    return {'archive':output.name,'bytes':output.stat().st_size,'sha256':value,'upstream_archives':len(rows),'publication_approved':False}


if __name__=='__main__':
    from fetch_native_sources import ROOT,SOURCES
    print(json.dumps(package_sources(ROOT,{row[0] for row in SOURCES})))
