"""Version-to-version installer check in a fresh owned directory."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import uuid
import winreg
from installed_payload import verify_installed_payload

ROOT=Path(__file__).resolve().parents[1]
KEY=r'Software\Microsoft\Windows\CurrentVersion\Uninstall\{A3658D58-C019-45CB-A0AF-2CBC8871E6B9}_is1'


def refuse_existing():
    for hive in (winreg.HKEY_CURRENT_USER,winreg.HKEY_LOCAL_MACHINE):
        for view in (winreg.KEY_WOW64_32KEY,winreg.KEY_WOW64_64KEY):
            try:handle=winreg.OpenKey(hive,KEY,0,winreg.KEY_READ|view)
            except FileNotFoundError:continue
            else:handle.Close();raise RuntimeError('Existing Luma installation found; refusing upgrade trial')


def installed_version():
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER,KEY,0,winreg.KEY_READ|winreg.KEY_WOW64_64KEY) as key:
        return winreg.QueryValueEx(key,'DisplayVersion')[0]


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def run():
    refuse_existing()
    compiler=ROOT/'tmp/installer-tools/compiler/ISCC.exe'
    with (ROOT/'verification/upgrade-compile.log').open('w') as log:
        subprocess.run([str(compiler),'/Qp','/DAppVersion=0.3.1-dev',str(ROOT/'installer/Luma.iss')],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,check=True)
    old=ROOT/'dist/installer/Luma-0.3.0-dev-Setup.exe'
    new=ROOT/'dist/installer/Luma-0.3.1-dev-Setup.exe'
    trial=ROOT/'verification'/('upgrade-trial-'+uuid.uuid4().hex[:8])
    target=trial/'app';data=trial/'user-data'
    assert target.resolve().is_relative_to((ROOT/'verification').resolve()) and not target.exists()
    data.mkdir(parents=True)
    (data/'notes.md').write_text('# Preserve this note\n',encoding='utf-8')
    (data/'settings.json').write_text(json.dumps({'theme':'Lavender','replacements':{'Luma':'Loo ma'}}))
    originals={name:sha(data/name) for name in ('notes.md','settings.json')}
    report={'from_version':'0.3.0-dev','to_version':'0.3.1-dev','trial':trial.name,'checks':{}}
    def install(path,label):
        subprocess.run([str(path),'/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART','/NOICONS',f'/DIR={target}',f'/LOG={trial / (label+".log")}'],check=True)
    install(old,'old-install')
    old_sha=sha(target/'Luma.exe')
    report['checks']['old_version_registered']=installed_version()=='0.3.0-dev'
    # Harmless sentinels at formerly packaged paths verify cleanup even when a
    # particular retained fixture did not contain that optional component.
    obsolete=['_internal/piper/hebrew/nakdimon.onnx','_internal/PySide6/Qt6Quick.dll']
    for name in obsolete:
        path=target/name;path.parent.mkdir(parents=True,exist_ok=True)
        path.write_bytes(b'Obsolete-package test sentinel; never executed')
    portable_voice=target/'LumaData/voices/own-voice.onnx'
    portable_voice.parent.mkdir(parents=True,exist_ok=True)
    portable_voice.write_bytes(b'User-owned voice preservation sentinel')
    own_voice_sha=sha(portable_voice)
    install(new,'upgrade')
    report['checks']['new_version_registered']=installed_version()=='0.3.1-dev'
    report['checks']['executable_updated']=sha(target/'Luma.exe')!=old_sha
    report['checks']['executable_matches_candidate']=sha(target/'Luma.exe')==sha(ROOT/'dist/Luma/Luma.exe')
    inventory=json.loads((ROOT/'release/local-audit/binary-inventory.json').read_text())
    report['installed_payload']=verify_installed_payload(target,inventory)
    report['checks']['installed_matches_audit']=report['installed_payload']['passed']
    report['checks']['obsolete_runtime_removed']=all(not (target/name).exists() for name in obsolete)
    report['checks']['portable_voice_preserved']=portable_voice.is_file() and sha(portable_voice)==own_voice_sha
    report['checks']['user_data_preserved']=all(sha(data/name)==value for name,value in originals.items())
    env=os.environ.copy();env['LUMA_DATA_DIR']=str(data)
    env['LUMA_TEST_VOICE']=str(target/'_internal/voices/en_GB-cori-high.onnx')
    diagnostic=trial/'upgraded-diagnostic.json'
    subprocess.run([str(target/'Luma.exe'),'--self-test',str(diagnostic)],env=env,check=True,timeout=90)
    result=json.loads(diagnostic.read_text())
    report['checks']['upgraded_diagnostic']=result['passed']
    report['source_fingerprint']=result.get('source_fingerprint')
    uninstaller=target/'unins000.exe'
    assert uninstaller.resolve().parent==target.resolve()
    subprocess.run([str(uninstaller),'/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART'],check=True)
    report['checks']['uninstalled']=not (target/'Luma.exe').exists()
    report['checks']['uninstall_preserves_data']=all(sha(data/name)==value for name,value in originals.items())
    report['checks']['uninstall_preserves_portable_voice']=portable_voice.is_file() and sha(portable_voice)==own_voice_sha
    report['passed']=all(report['checks'].values())
    (ROOT/'verification/upgrade-result.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))
    if not report['passed']:raise RuntimeError('Upgrade acceptance failed')


if __name__=='__main__':run()
