"""Exercise an isolated verification installer; never target an existing installation."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import uuid
import sys
from build_installer import installer_version
from installed_payload import verify_installed_payload

ROOT=Path(__file__).resolve().parents[1]


def run():
    version=installer_version()
    candidate='--candidate' in sys.argv
    if candidate:
        import winreg
        key=r'Software\Microsoft\Windows\CurrentVersion\Uninstall\{A3658D58-C019-45CB-A0AF-2CBC8871E6B9}_is1'
        for hive in (winreg.HKEY_CURRENT_USER,winreg.HKEY_LOCAL_MACHINE):
            for view in (winreg.KEY_WOW64_64KEY,winreg.KEY_WOW64_32KEY):
                try:
                    handle=winreg.OpenKey(hive,key,0,winreg.KEY_READ|view)
                except FileNotFoundError:continue
                else:
                    handle.Close()
                    raise RuntimeError('Existing Luma install found; refusing candidate lifecycle test')
        installer=ROOT/f'dist/installer/Luma-{version}-Setup.exe'
    else:
        compiler=ROOT/'tmp/installer-tools/compiler/ISCC.exe'
        with (ROOT/'verification/installer-verification-compile.log').open('w') as log:
            subprocess.run([str(compiler),'/Qp','/DVerificationBuild=1',str(ROOT/'installer/Luma.iss')],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,check=True)
        installer=ROOT/f'dist/installer/Luma-{version}-Verification-Setup.exe'
    if not installer.is_file():
        raise FileNotFoundError(f'Build the {version} installer before testing: {installer}')
    trial=ROOT/'verification'/('installer-trial-'+uuid.uuid4().hex[:8])
    target=trial/'app';data=trial/'user-data'
    assert target.resolve().is_relative_to((ROOT/'verification').resolve())
    assert not target.exists()
    data.mkdir(parents=True)
    note=data/'my-note.md';note.write_text('# Keep my notes\n\nUpgrade preservation check.',encoding='utf-8')
    original=hashlib.sha256(note.read_bytes()).hexdigest()
    report={'verification_build':not candidate,'directory':trial.name,'checks':{}}
    args=[str(installer),'/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART','/NOICONS',f'/DIR={target}',f'/LOG={trial / "install.log"}']
    env=os.environ.copy();env['LUMA_DATA_DIR']=str(data)
    subprocess.run(args,check=True)
    report['checks']['installed']=(target/'Luma.exe').is_file()
    inventory=json.loads((ROOT/'release/local-audit/binary-inventory.json').read_text())
    report['installed_payload']=verify_installed_payload(target,inventory)
    report['checks']['installed_matches_audit']=report['installed_payload']['passed']
    env['LUMA_TEST_VOICE']=str(target/'_internal/voices/en_GB-cori-high.onnx')
    diagnostic=trial/'installed-diagnostic.json'
    subprocess.run([str(target/'Luma.exe'),'--self-test',str(diagnostic)],env=env,check=True,timeout=90)
    report['checks']['installed_diagnostic']=json.loads(diagnostic.read_text())['passed']
    subprocess.run(args,check=True)
    report['checks']['reinstalled_matches_audit']=verify_installed_payload(target,inventory)['passed']
    report['checks']['reinstall_preserves_note']=hashlib.sha256(note.read_bytes()).hexdigest()==original
    uninstaller=target/'unins000.exe'
    assert uninstaller.resolve().parent==target.resolve()
    subprocess.run([str(uninstaller),'/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART'],check=True)
    report['checks']['uninstalled']=not (target/'Luma.exe').exists()
    report['checks']['uninstall_preserves_note']=note.is_file() and hashlib.sha256(note.read_bytes()).hexdigest()==original
    report['passed']=all(report['checks'].values())
    (ROOT/'verification/installer-lifecycle.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))
    if not report['passed']:raise RuntimeError('Installer lifecycle checks failed')


if __name__=='__main__':run()
