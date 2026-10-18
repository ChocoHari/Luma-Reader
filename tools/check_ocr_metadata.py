"""Fetch upstream model metadata; do not download or replace model weights."""
import hashlib
import json
from pathlib import Path
import urllib.request

ROOT=Path(__file__).resolve().parents[1]


def main():
    base='https://huggingface.co/api/models/SWHL/RapidOCR'
    with urllib.request.urlopen(base,timeout=35) as response:repo=json.load(response)
    revision=repo['sha']
    evidence={'repository':base,'revision':revision,'retrieved':'2026-10-18','license':repo.get('cardData',{}).get('license'),'files':[]}
    for directory in ('PP-OCRv4','PP-OCRv2','PP-OCRv1'):
        url=f'{base}/tree/{revision}/{directory}?expand=true'
        with urllib.request.urlopen(url,timeout=35) as response:items=json.load(response)
        evidence['files'].extend(items)
    rows=[]
    for file in sorted((ROOT/'.venv/Lib/site-packages/rapidocr_onnxruntime/models').glob('*.onnx')):
        sha=hashlib.sha256(file.read_bytes()).hexdigest()
        matches=[v for v in evidence['files'] if Path(v['path']).name==file.name and v.get('lfs',{}).get('oid')==sha]
        rows.append({'file':file.name,'sha256':sha,'bytes':file.stat().st_size,'upstream_matches':[v['path'] for v in matches]})
    evidence['local_comparison']=rows
    (ROOT/'release/evidence/ocr-upstream-metadata.json').write_text(json.dumps(evidence,indent=2),encoding='utf-8')
    print(json.dumps({'license':evidence['license'],'revision':revision,'models':rows},indent=2))


if __name__=='__main__':main()
