"""Application assets and writable user storage, independent of installation location."""
from pathlib import Path
import os
import shutil
import sys

ASSET_ROOT=Path(__file__).resolve().parent


def data_directory(environ=None,home=None,executable=None):
    env=os.environ if environ is None else environ
    home=Path.home() if home is None else Path(home)
    if env.get('LUMA_DATA_DIR'):
        return Path(env['LUMA_DATA_DIR']).expanduser().resolve()
    if env.get('LUMA_PORTABLE')=='1':
        return Path(executable or sys.executable).resolve().parent/'Luma Data'
    return Path(env.get('LOCALAPPDATA',home/'AppData'/'Local'))/'Luma Reader'


def migrate_legacy_data(source,target):
    """Copy known user data without overwriting newer files or moving originals."""
    source,target=Path(source),Path(target)
    if source.resolve()==target.resolve():return 0
    marker=target/'.legacy-migration-complete'
    if marker.exists() or not source.is_dir():return 0
    copied=0
    candidates=[source/'settings.json']
    for name in ('ocr','recovery'):
        folder=source/name
        if folder.is_dir():candidates.extend(folder.rglob('*.json'))
    for path in candidates:
        if not path.is_file() or path.is_symlink():continue
        relative=path.relative_to(source)
        dest=target/relative
        # Refuse links that resolve outside either root.
        if not path.resolve().is_relative_to(source.resolve()) or not dest.resolve().is_relative_to(target.resolve()):continue
        if dest.exists():continue
        dest.parent.mkdir(parents=True,exist_ok=True)
        # Exclusive creation preserves destination files even if another instance races us.
        try:
            with dest.open('xb') as output,path.open('rb') as input:
                shutil.copyfileobj(input,output)
            copied+=1
        except FileExistsError:pass
    target.mkdir(parents=True,exist_ok=True)
    marker.write_text('Legacy data copied once; originals preserved.\n',encoding='utf-8')
    return copied


DATA_ROOT=data_directory()
VOICE_ROOT=DATA_ROOT/'voices'
EXPORT_ROOT=Path.home()/'Documents'
if not EXPORT_ROOT.is_dir():EXPORT_ROOT=Path.home()
