"""Development/build download only; the installed reader never fetches models."""
import json
from pathlib import Path,PurePosixPath
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from ocr_backend import MODEL_HASHES
from fetch_build_voice import fetch_verified


def main():
    evidence=json.loads((ROOT/'release/evidence/ocr-upstream-metadata.json').read_text())
    base='https://huggingface.co/SWHL/RapidOCR/resolve/'+evidence['revision']+'/'
    rows={row['file']:row for row in evidence['local_comparison']}
    if set(rows)!=set(MODEL_HASHES):raise ValueError('Unexpected reviewed OCR model set')
    for name,expected in MODEL_HASHES.items():
        row=rows[name]
        if row['sha256']!=expected or len(row['upstream_matches'])!=1:
            raise ValueError('OCR provenance does not match runtime policy')
        member=PurePosixPath(row['upstream_matches'][0])
        if member.is_absolute() or '..' in member.parts or ':' in str(member):
            raise ValueError('Unsafe upstream model path')
        fetch_verified(base+str(member),ROOT/'ocr_models'/name,expected)
        print('Verified '+name)


if __name__=='__main__':main()
