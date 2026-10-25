"""Fetch identified public licensing evidence. No models, accounts, or user data are sent."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
from urllib.request import Request,urlopen

ROOT=Path(__file__).resolve().parents[1]
OUTPUT=ROOT/'release'/'evidence'
SOURCES={
 'AGPL-3.0-or-later.txt':'https://raw.githubusercontent.com/spdx/license-list-data/main/text/AGPL-3.0-or-later.txt',
 'piper-aru-MODEL_CARD.txt':'https://huggingface.co/rhasspy/piper-voices/raw/main/en/en_GB/aru/medium/MODEL_CARD',
 'piper-cori-MODEL_CARD.txt':'https://huggingface.co/rhasspy/piper-voices/raw/main/en/en_GB/cori/high/MODEL_CARD',
 'piper-jenny-MODEL_CARD.txt':'https://huggingface.co/rhasspy/piper-voices/raw/main/en/en_GB/jenny_dioco/medium/MODEL_CARD',
 'piper-northern-MODEL_CARD.txt':'https://huggingface.co/rhasspy/piper-voices/raw/main/en/en_GB/northern_english_male/medium/MODEL_CARD',
 'piper-semaine-MODEL_CARD.txt':'https://huggingface.co/rhasspy/piper-voices/raw/main/en/en_GB/semaine/medium/MODEL_CARD',
 'jenny-dataset-README.txt':'https://raw.githubusercontent.com/dioco-group/jenny-tts-dataset/main/README.md',
 'cori-author-page.html':'https://brycebeattie.com/files/tts/',
 'RapidOCR-Apache-2.0.txt':'https://raw.githubusercontent.com/RapidAI/RapidOCR/v1.4.4/LICENSE',
 'PaddleOCR-Apache-2.0.txt':'https://raw.githubusercontent.com/PaddlePaddle/PaddleOCR/release/2.7/LICENSE',
 'Qt-LGPL-3.0.txt':'https://raw.githubusercontent.com/qt/qtbase/v6.8.3/LICENSES/LGPL-3.0-only.txt',
 'GPL-3.0.txt':'https://raw.githubusercontent.com/spdx/license-list-data/main/text/GPL-3.0-only.txt',
 'LGPL-2.1.txt':'https://raw.githubusercontent.com/spdx/license-list-data/main/text/LGPL-2.1-or-later.txt',
}

def main():
    OUTPUT.mkdir(parents=True,exist_ok=True)
    manifest=[]
    for name,url in SOURCES.items():
        record={'file':name,'url':url,'retrieved_date':'2026-10-17'}
        try:
            data=urlopen(Request(url,headers={'User-Agent':'Luma-release-audit/0.1'}),timeout=35).read()
            if not data:raise ValueError('Empty evidence response')
            (OUTPUT/name).write_bytes(data)
            record.update(status='retrieved',sha256=hashlib.sha256(data).hexdigest(),bytes=len(data))
        except Exception as error:
            record.update(status='unavailable',error=str(error))
        manifest.append(record)
        print(name,record['status'],flush=True)
    (OUTPUT/'sources.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    agpl=OUTPUT/'AGPL-3.0-or-later.txt'
    if not agpl.exists() or agpl.stat().st_size<30000:
        raise SystemExit('Complete AGPL licence text not obtained; do not create a partial LICENSE.')
    (ROOT/'LICENSE').write_bytes(agpl.read_bytes())

if __name__=='__main__':main()
