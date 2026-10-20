# Development binary only: public redistribution is controlled by release/release-gates.json.
from pathlib import Path
import os
import sys
from PyInstaller.utils.hooks import collect_data_files,collect_dynamic_libs

root=Path(SPECPATH)
sys.path.insert(0,str(root/'tools'))
from native_policy import excluded_binary
datas=[(str(root/name),'.') for name in ('LICENSE','NOTICE','THIRD_PARTY.md','USER_GUIDE.md','OTHER_READERS.md')]
datas += [(str(root/'release'/name),'release') for name in ('KNOWN_ISSUES.md','PRIVACY.md')]
datas += [(str(root/'release/local-audit/SOURCE_MANIFEST.json'),'.')]
datas += [(str(root/'assets'/name),'assets') for name in ('luma.ico','luma.png','book-wave.svg','page-sound.svg','luma-orbit.svg')]
# Optional language-processing weights have separate provenance requirements.
# The reviewed package includes only the selected voice and the three OCR models.
datas += collect_data_files('piper',excludes=['**/*.onnx'])+collect_data_files('rapidocr',excludes=['**/*.onnx'])
from ocr_backend import verified_models
datas += [(str(path),'ocr_models') for path in verified_models().values()]
binaries=collect_dynamic_libs('piper')+collect_dynamic_libs('onnxruntime')
a=Analysis([str(root/'tools/frozen_entry.py')],pathex=[str(root)],binaries=binaries,datas=datas,
    hiddenimports=['piper','rapidocr','rapidocr.inference_engine.onnxruntime','onnxruntime','frozen_diagnostics'],
    excludes=['PySide6.QtWebEngineCore','PySide6.QtWebEngineWidgets','PySide6.QtWebEngineQuick',
              'PySide6.QtPdf','PySide6.QtPdfWidgets','pytest','tkinter'],noarchive=False)
# Qt uses the Windows system ICU API. Do not shadow it with a different ICU
# found on the developer PATH (for example a Poppler runtime).
a.binaries=[item for item in a.binaries if not excluded_binary(item[0])]
# Refuse libraries harvested from unrelated applications on a developer machine.
trusted=[Path(sys.prefix).resolve(),Path(sys.base_prefix).resolve(),
         Path(os.environ.get('SystemRoot','C:/Windows')).resolve()]
for name,source,kind in a.binaries:
    if not any(Path(source).resolve().is_relative_to(base) for base in trusted):
        raise RuntimeError(f'Unexpected native-library origin for {name}: {source}')
pyz=PYZ(a.pure)
exe=EXE(pyz,a.scripts,[],exclude_binaries=True,name='Luma',debug=False,
    bootloader_ignore_signals=False,strip=False,upx=False,console=False,icon=str(root/'assets/luma.ico'))
coll=COLLECT(exe,a.binaries,a.datas,strip=False,upx=False,name='Luma')
