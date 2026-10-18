"""Fetch only the explicitly reviewed build voice, checking both file hashes."""
import hashlib
import json
import os
from pathlib import Path
import tempfile
import urllib.request

ROOT=Path(__file__).resolve().parents[1]
BASE='https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_GB/cori/high/'


def fetch_verified(url,destination,expected):
    destination=Path(destination)
    if destination.exists():
        if hashlib.sha256(destination.read_bytes()).hexdigest()!=expected:
            raise ValueError(f'Existing file differs; refusing to overwrite {destination.name}')
        return
    destination.parent.mkdir(parents=True,exist_ok=True)
    fd,temp=tempfile.mkstemp(dir=destination.parent,suffix='.download')
    h=hashlib.sha256()
    try:
        with os.fdopen(fd,'wb') as output,urllib.request.urlopen(url,timeout=60) as response:
            while chunk:=response.read(1024*1024):h.update(chunk);output.write(chunk)
        if h.hexdigest()!=expected:raise ValueError(f'Upstream hash mismatch: {destination.name}')
        os.replace(temp,destination)
    finally:Path(temp).unlink(missing_ok=True)


def main():
    manifest=json.loads((ROOT/'release/voice-manifest.json').read_text(encoding='utf-8'))
    for voice in manifest['voices']:
        if voice.get('redistribution_approved') is not True:continue
        if voice['file']!='en_GB-cori-high.onnx':raise ValueError('No reviewed download route for this voice')
        for name,sha in ((voice['file'],voice['sha256']),(voice['file']+'.json',voice['config_sha256'])):
            fetch_verified(BASE+name,ROOT/'Piper Voices'/name,sha)
            print(f'Verified {name}')


if __name__=='__main__':main()
