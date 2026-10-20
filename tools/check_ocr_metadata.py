"""Fetch upstream model metadata; do not download or replace model weights."""
import hashlib
import json
from datetime import datetime,timezone
from pathlib import Path
import sys
import urllib.request

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from ocr_backend import verified_models


def main():
    base='https://huggingface.co/api/models/SWHL/RapidOCR'
    with urllib.request.urlopen(base,timeout=35) as response:repo=json.load(response)
    revision=repo['sha']
    evidence={'repository':base,'revision':revision,'retrieved':datetime.now(timezone.utc).isoformat(),'license':repo.get('cardData',{}).get('license'),'files':[]}
    for directory in ('PP-OCRv4','PP-OCRv2','PP-OCRv1'):
        url=f'{base}/tree/{revision}/{directory}?expand=true'
        with urllib.request.urlopen(url,timeout=35) as response:items=json.load(response)
        evidence['files'].extend(items)
    rows=[]
    for file in sorted(verified_models().values()):
        sha=hashlib.sha256(file.read_bytes()).hexdigest()
        matches=[v for v in evidence['files'] if Path(v['path']).name==file.name and v.get('lfs',{}).get('oid')==sha]
        if not matches:raise ValueError('No matching upstream OCR identity: '+file.name)
        rows.append({'file':file.name,'sha256':sha,'bytes':file.stat().st_size,'upstream_matches':[v['path'] for v in matches]})
    evidence['local_comparison']=rows
    (ROOT/'release/evidence/ocr-upstream-metadata.json').write_text(json.dumps(evidence,indent=2),encoding='utf-8')
    print(json.dumps({'license':evidence['license'],'revision':revision,'models':rows},indent=2))


if __name__=='__main__':main()
