"""Run tests from an isolated allowlisted checkout with only reviewed voices."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from source_package import snapshot_sources
from fetch_build_voice import fetch_verified

ROOT=Path(__file__).resolve().parents[1]


def main():
    manifest,payloads=snapshot_sources(ROOT)
    checkout=Path(tempfile.mkdtemp(prefix='source-checkout-',dir=ROOT/'verification'))
    for name,data in payloads.items():
        target=checkout/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
    voices=json.loads((ROOT/'release/voice-manifest.json').read_text())['voices']
    for voice in voices:
        if voice.get('redistribution_approved') is not True:continue
        for name,expected in ((voice['file'],voice['sha256']),(voice['file']+'.json',voice['config_sha256'])):
            fetch_verified((ROOT/'Piper Voices'/name).as_uri(),checkout/'Piper Voices'/name,expected)
    log=ROOT/'verification/source-checkout-tests.log'
    with log.open('w') as output:
        result=subprocess.run([sys.executable,'-m','pytest','tests','-q'],cwd=checkout,stdout=output,stderr=subprocess.STDOUT)
    report={'source_fingerprint':manifest['source_fingerprint'],'checkout':checkout.name,
            'scope':'Isolated public source + reviewed voices, existing development dependency environment',
            'passed':result.returncode==0,'test_output':log.read_text()}
    (ROOT/'verification/source-checkout-result.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2));return result.returncode


if __name__=='__main__':raise SystemExit(main())
