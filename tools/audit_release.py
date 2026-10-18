"""Inventory the local environment; never grants permission to ship a binary."""
from __future__ import annotations

import hashlib
import importlib.metadata as metadata
import json
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def validate_sources(root: Path, spec: dict) -> list[str]:
    errors = []
    excluded = {name.casefold() for name in spec['excluded_directories']}
    for name in spec['files']:
        path = PurePosixPath(name)
        target = (root / name).resolve()
        if (path.is_absolute() or '..' in path.parts or ':' in name
                or any(part.casefold() in excluded for part in path.parts)
                or not target.is_relative_to(root.resolve())):
            errors.append(f'Unsafe source path: {name}')
        elif not target.is_file():
            errors.append(f'Missing source file: {name}')
    return errors


def approved_voices(manifest: dict) -> list[dict]:
    return [v for v in manifest['voices']
            if v.get('redistribution_approved') is True
            and v.get('sha256') and v.get('review_evidence')]


def main() -> int:
    release = ROOT / 'release'
    local = release / 'local-audit'
    local.mkdir(exist_ok=True)
    packages = []
    native = []
    for dist in metadata.distributions():
        name = dist.metadata.get('Name', 'unknown')
        notices = []
        for item in dist.files or []:
            lowered = str(item).lower()
            path = Path(dist.locate_file(item)).resolve()
            if not path.is_relative_to((ROOT / '.venv').resolve()) or not path.is_file():
                continue
            if any(token in path.name.lower() for token in ('license', 'licence', 'copying', 'notice')):
                notices.append({'path': str(item).replace('\\', '/'), 'sha256': digest(path)})
            if lowered.endswith(('.dll', '.onnx')):
                native.append({'package': name, 'path': str(item).replace('\\', '/'),
                               'sha256': digest(path)})
        packages.append({'name': name, 'version': dist.version,
                         'declared_license': dist.metadata.get('License-Expression') or dist.metadata.get('License'),
                         'notice_files': notices})
    voices = []
    previous_path=release/'voice-manifest.json'
    previous=json.loads(previous_path.read_text(encoding='utf-8')) if previous_path.exists() else {'voices':[]}
    for path in sorted((ROOT / 'Piper Voices').glob('*.onnx')):
        config = Path(str(path) + '.json')
        voices.append({'file': path.name, 'bytes': path.stat().st_size,
                       'sha256': digest(path), 'config_present': config.is_file(),
                       'config_sha256': digest(config) if config.is_file() else None,
                       'redistribution_approved': False, 'review_evidence': None,
                       'review_status': 'See VOICE_REVIEW.md; local availability is not distribution clearance.'})
        prior=next((v for v in previous['voices'] if v['file']==path.name),{})
        current=voices[-1]
        if prior.get('sha256')==current['sha256'] and prior.get('config_sha256')==current['config_sha256']:
            for key in ('redistribution_approved','review_evidence','review_status'):
                if key in prior:current[key]=prior[key]
    manifest = {'schema_version': 1, 'default_policy': 'exclude', 'voices': voices}
    (release / 'voice-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    spec = json.loads((release / 'source-allowlist.json').read_text(encoding='utf-8'))
    errors = validate_sources(ROOT, spec)
    report = {'scope': 'Development environment inventory, not shipped SBOM or legal clearance',
              'dependencies': sorted(packages, key=lambda p: p['name'].lower()),
              'native_components_and_models': native, 'source_errors': errors,
              'public_binary_approved': False}
    (local / 'environment.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(f'Inventoried {len(packages)} packages, {len(native)} native/model files, {len(voices)} voices.')
    print(f'Source allowlist errors: {len(errors)}. Binary release remains gated.')
    for error in errors:
        print(error)
    return bool(errors)


if __name__ == '__main__':
    raise SystemExit(main())
