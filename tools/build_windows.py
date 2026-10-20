"""Build a local verification binary; no publication or blanket voice copying."""
import json
import os
import subprocess
import sys
import importlib.metadata as metadata
import shutil
import ssl
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def main():
    if '--inventory-only' not in sys.argv:
        from source_package import write_source_package,snapshot_sources
        snapshot=write_source_package(ROOT)
        environment=os.environ.copy()
        windows=Path(environment.get('SystemRoot','C:/Windows'))
        environment['PATH']=os.pathsep.join(str(p) for p in (
            Path(sys.executable).parent,Path(sys.base_prefix),Path(sys.base_prefix)/'DLLs',
            windows/'System32',windows))
        subprocess.run([sys.executable,'-m','PyInstaller','--clean','--noconfirm',str(ROOT/'Luma.spec')],cwd=ROOT,env=environment,check=True)
        if snapshot_sources(ROOT)[0]['source_fingerprint']!=snapshot['source_fingerprint']:
            raise RuntimeError('Source changed during compilation; rebuild required')
    from audit_release import digest,approved_voices
    output=ROOT/'dist'/'Luma'
    ocr_evidence=json.loads((ROOT/'release/evidence/ocr-upstream-metadata.json').read_text())
    for model in ocr_evidence['local_comparison']:
        path=output/'_internal/ocr_models'/model['file']
        if not model['upstream_matches'] or digest(path)!=model['sha256']:
            raise RuntimeError('OCR model does not match reviewed upstream artifact')
    model_notices=output/'third-party-notices/OCR-models'
    model_notices.mkdir(parents=True,exist_ok=True)
    for source in ('release/OCR_MODELS.md','release/evidence/PaddleOCR-Apache-2.0.txt','release/evidence/ocr-upstream-metadata.json'):
        shutil.copy2(ROOT/source,model_notices/Path(source).name)
    manifest=json.loads((ROOT/'release/voice-manifest.json').read_text(encoding='utf-8'))
    allowed_names={v['file'] for v in approved_voices(manifest)}
    for existing in (output/'_internal/voices').glob('*.onnx'):
        if existing.name not in allowed_names:raise RuntimeError('Unapproved voice remains in build; clean rebuild required')
    for voice in approved_voices(manifest):
        evidence=(ROOT/voice['review_evidence']).resolve()
        if not evidence.is_relative_to(ROOT) or not evidence.is_file():raise RuntimeError('Missing voice review evidence')
        model=(ROOT/'Piper Voices'/voice['file']).resolve()
        if model.parent!=(ROOT/'Piper Voices').resolve():raise RuntimeError('Invalid voice path')
        config=Path(str(model)+'.json')
        if digest(model)!=voice['sha256'] or digest(config)!=voice['config_sha256']:
            raise RuntimeError('Approved voice files changed; review required')
        destination=output/'_internal'/'voices'
        destination.mkdir(exist_ok=True)
        shutil.copy2(model,destination/model.name)
        shutil.copy2(config,destination/config.name)
        shutil.copy2(evidence,destination/'VOICE_CREDIT.md')
        shutil.copy2(ROOT/'release/evidence/piper-cori-MODEL_CARD.txt',destination/'MODEL_CARD.txt')
    shutil.copy2(ROOT/'installer'/'Launch Portable.cmd',output/'Launch Portable.cmd')
    from model_inventory import verify_model_allowlist
    notices=output/'third-party-notices'
    from runtime_notices import copy_python_notice
    notice_index=[copy_python_notice(output)]
    from native_notices import copy_native_notices
    notice_index+=copy_native_notices(ROOT,output)
    for dist in metadata.distributions():
        name=dist.metadata.get('Name','unknown')
        for item in dist.files or []:
            source=Path(dist.locate_file(item)).resolve()
            if not source.is_file() or not source.is_relative_to(Path(sys.prefix).resolve()):continue
            if not any(word in source.name.lower() for word in ('license','licence','copying','notice')):continue
            # Preserve the original relative hierarchy, avoiding basename collisions.
            relative=Path(*[part for part in item.parts if part not in ('..','.')])
            target=notices/name/relative
            target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(source,target)
            notice_index.append({'package':name,'version':dist.version,'file':target.relative_to(output).as_posix()})
    notices.mkdir(exist_ok=True)
    (notices/'INDEX.json').write_text(json.dumps({'scope':'Available development-environment notices; not complete corresponding source or binary clearance','notices':notice_index},indent=2),encoding='utf-8')
    verify_model_allowlist(output,
        {f"_internal/ocr_models/{model['file']}" for model in ocr_evidence['local_comparison']} |
        {f"_internal/voices/{name}" for name in allowed_names})
    from native_policy import verify_native_policy
    native_policy=verify_native_policy(output)
    files=[]
    for path in sorted(output.rglob('*')):
        if path.is_file():
            relative=path.relative_to(output).as_posix()
            parts=path.relative_to(output).parts
            app_parts=parts[1:] if parts[0]=='_internal' else parts
            if app_parts[0].lower() in {'data','recovery','verification','piper voices'}:
                raise RuntimeError(f'Private directory in build: {relative}')
            if parts[0]!='third-party-notices' and ('webengine' in relative.lower() or 'qtpdf' in relative.lower() or path.name.lower() in {'qt6pdf.dll','qpdf.dll','icuuc.dll'}):
                raise RuntimeError(f'Unused Qt module in build: {relative}')
            files.append({'path':relative,'bytes':path.stat().st_size,'sha256':digest(path)})
    report={'public_binary_approved':False,'purpose':'local verification only',
            'runtime':{'python':sys.version.split()[0],'openssl':ssl.OPENSSL_VERSION},
            'native_policy':native_policy,'files':files}
    target=ROOT/'release'/'local-audit'/'binary-inventory.json'
    target.parent.mkdir(exist_ok=True)
    target.write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(f'Built {len(files)} files. Public redistribution remains gated.')


if __name__=='__main__':main()
