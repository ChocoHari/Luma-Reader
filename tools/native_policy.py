"""Native libraries outside Luma's document/editor/audio feature set."""
from pathlib import PurePosixPath

EXCLUDED_NAMES={
    'icuuc.dll','icudt78.dll','qt6pdf.dll','qpdf.dll',
    'qt6virtualkeyboard.dll','qtvirtualkeyboardplugin.dll','qt6quick.dll',
    'qt6qml.dll','qt6qmlmeta.dll','qt6qmlmodels.dll','qt6qmlworkerscript.dll',
}


def excluded_binary(name):
    base=PurePosixPath(str(name).replace('\\','/')).name.lower()
    if not base.endswith(('.dll','.pyd')):return False
    return (base in EXCLUDED_NAMES or 'webengine' in base
            or base.startswith('opencv_videoio_ffmpeg')
            or base in {'qtqml.pyd','qtquick.pyd','qtquickwidgets.pyd','qtvirtualkeyboard.pyd','qtpdf.pyd'})


def verify_native_policy(output):
    from pathlib import Path
    import pefile
    output=Path(output)
    unexpected=[];dangling=[];count=0
    for path in output.rglob('*'):
        if not path.is_file() or path.suffix.lower() not in {'.dll','.pyd'}:continue
        relative=path.relative_to(output).as_posix()
        if relative.startswith('third-party-notices/'):continue
        if excluded_binary(path.name):unexpected.append(relative)
        count+=1
        with pefile.PE(str(path),fast_load=True) as pe:
            pe.parse_data_directories(directories=[1,13])
            for key in ('DIRECTORY_ENTRY_IMPORT','DIRECTORY_ENTRY_DELAY_IMPORT'):
                for entry in getattr(pe,key,[]):
                    dependency=entry.dll.decode().lower()
                    # Qt deliberately uses the Windows system ICU API.
                    if dependency=='icuuc.dll':continue
                    if excluded_binary(dependency):dangling.append({'file':relative,'dependency':dependency})
    if unexpected or dangling:raise RuntimeError(f'Native policy failure: excluded={unexpected}, dangling={dangling}')
    return {'native_libraries':count,'excluded_files':unexpected,'dangling_excluded_imports':dangling}
