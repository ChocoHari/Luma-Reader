"""Compile the per-user installer using the verified local Inno compiler."""
from pathlib import Path
import re
import subprocess

ROOT=Path(__file__).resolve().parents[1]


def installer_version(root=ROOT):
    """Read the same default version used by the installer compiler."""
    source=(Path(root)/'installer/Luma.iss').read_text(encoding='utf-8')
    versions=re.findall(r'^\s*#define\s+AppVersion\s+"([0-9]+\.[0-9]+\.[0-9]+(?:-[A-Za-z0-9.]+)?)"\s*$',source,re.M)
    if len(versions)!=1:
        raise ValueError('Installer must define one explicit valid default AppVersion')
    return versions[0]


if __name__=='__main__':
    compiler=ROOT/'tmp/installer-tools/compiler/ISCC.exe'
    if not compiler.is_file():raise SystemExit('Set up the verified Inno compiler described in release/BUILD_WINDOWS.md first.')
    if not (ROOT/'release/local-audit/binary-inventory.json').is_file():raise SystemExit('Build and audit Luma first.')
    subprocess.run([str(compiler),'/Qp',str(ROOT/'installer/Luma.iss')],cwd=ROOT,check=True)
