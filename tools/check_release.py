"""Read-only release policy check; passing does not publish anything."""
import json
from pathlib import Path
import sys

REQUIRED={'qt-ffmpeg','microsoft-runtime','ocr-model-provenance','voice-clearance','corresponding-source','clean-package'}


def public_blockers(config):
    gates={g['id']:g for g in config.get('gates',[])}
    errors=[f'Missing gate: {name}' for name in sorted(REQUIRED-gates.keys())]
    errors.extend(f"Pending gate: {name}" for name in sorted(REQUIRED & gates.keys()) if gates[name].get('status')!='passed')
    if config.get('public_binary_approved') is not True:errors.append('Public binary approval is not recorded')
    return errors


if __name__=='__main__':
    root=Path(__file__).resolve().parents[1]
    errors=public_blockers(json.loads((root/'release/release-gates.json').read_text()))
    for error in errors:print(error)
    print('Public policy: '+('BLOCKED' if errors else 'recorded gates passed; verify matching artifacts before publishing'))
    raise SystemExit(bool(errors))
