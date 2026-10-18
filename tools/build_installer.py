"""Compile the per-user installer using the verified local Inno compiler."""
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[1]


if __name__=='__main__':
    compiler=ROOT/'tmp/installer-tools/compiler/ISCC.exe'
    if not compiler.is_file():raise SystemExit('Set up the verified Inno compiler described in release/BUILD_WINDOWS.md first.')
    if not (ROOT/'release/local-audit/binary-inventory.json').is_file():raise SystemExit('Build and audit Luma first.')
    subprocess.run([str(compiler),'/Qp',str(ROOT/'installer/Luma.iss')],cwd=ROOT,check=True)
