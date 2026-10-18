"""Retain official versioned source archives; no compilation or licence clearance implied."""
import hashlib
import json
from pathlib import Path
import tarfile
import urllib.request

ROOT=Path(__file__).resolve().parents[1]
SOURCES=[
 ('pyside-setup-everywhere-src-6.12.0.tar.xz','https://download.qt.io/official_releases/QtForPython/pyside6/PySide6-6.12.0-src/pyside-setup-everywhere-src-6.12.0.tar.xz'),
 ('ffmpeg-n9.0.1-github.tar.gz','https://codeload.github.com/FFmpeg/FFmpeg/tar.gz/refs/tags/n9.0.1')]
for module in ('qtbase','qtdeclarative','qtmultimedia','qtsvg','qtvirtualkeyboard'):
    name=f'{module}-everywhere-src-6.12.0.tar.xz'
    SOURCES.append((name,'https://download.qt.io/official_releases/qt/6.12/6.12.0/submodules/'+name))
SOURCES += [
 ('piper_tts-1.8.0.tar.gz','https://files.pythonhosted.org/packages/02/cc/95b18b58d9c235d8e0bcece7321b7a7347873c14f9fea2c734b31ef04ff2/piper_tts-1.8.0.tar.gz',
  '830588aded347df579c91a32703e0fc2a3685d84f1e3533b14f2de69135d4904'),
 ('pymupdf-1.28.2.tar.gz','https://files.pythonhosted.org/packages/a3/fb/b6761fa2d5266f2cdb24c3b91f4023070ab7848381417678e7a289a1d52a/pymupdf-1.28.2.tar.gz',
  '5e0be7908a715aa20333caddd73f1d6f01e4cd0c26e869fa2dd0b7f344da2249')]


def verify_hash(path, expected):
    value=hashlib.sha256(Path(path).read_bytes()).hexdigest()
    if expected and value!=expected:
        raise RuntimeError(f'Source archive hash mismatch: {Path(path).name}')
    return value


def main():
    folder=ROOT/'release/local-audit/upstream-sources';folder.mkdir(parents=True,exist_ok=True)
    records=[]
    for name,url,*hashes in SOURCES:
        expected=hashes[0] if hashes else None
        target=folder/name
        if not target.exists():
            partial=target.with_suffix(target.suffix+'.partial')
            try:
                with urllib.request.urlopen(url,timeout=60) as response,partial.open('wb') as output:
                    while chunk:=response.read(1024*1024):output.write(chunk)
                verify_hash(partial,expected)
                partial.replace(target)
            finally:partial.unlink(missing_ok=True)
        value=verify_hash(target,expected)
        with tarfile.open(target,'r:*') as archive:
            members=archive.getnames()
            notices=[m.name for m in archive.getmembers() if m.isfile() and
                     (Path(m.name).name.upper().startswith(('LICENSE','LICENCE','COPYING')) or
                      any(part.upper()=='LICENSES' for part in Path(m.name).parts))]
        row={'file':name,'source':url,'bytes':target.stat().st_size,'sha256':value,
             'expected_sha256':expected,'expected_hash_matched':True if expected else None,
             'archive_members':len(members),'licence_entries':notices,
             'status':'retained official versioned archive; binary patches/build correspondence not fully verified'}
        records.append(row)
        (folder/'manifest.json').write_text(json.dumps({'retrieved':'2026-10-18','archives':records,'native_gate_passed':False},indent=2))
        print(json.dumps({k:row[k] for k in ('file','bytes','sha256','archive_members')}),flush=True)
    (folder/'manifest.json').write_text(json.dumps({'retrieved':'2026-10-18','archives':records,'native_gate_passed':False},indent=2))


if __name__=='__main__':main()
