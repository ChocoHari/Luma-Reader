"""Map actual packaged native files to installed distribution records by hash."""
import importlib.metadata as metadata
import json
import sys
from pathlib import Path
from audit_release import digest

ROOT=Path(__file__).resolve().parents[1]


def main():
    installed={}
    for dist in metadata.distributions():
        for entry in dist.files or []:
            if Path(str(entry)).suffix.lower() not in {'.dll','.pyd','.onnx'}:continue
            path=Path(dist.locate_file(entry)).resolve()
            if not path.is_file() or not path.is_relative_to((ROOT/'.venv').resolve()):continue
            installed.setdefault(digest(path),[]).append({'package':dist.metadata.get('Name'),'version':dist.version,'file':str(entry).replace('\\','/')})
    runtime={}
    base=Path(sys.base_prefix)
    for directory in (base,base/'DLLs'):
        for path in directory.glob('*'):
            if path.is_file() and path.suffix.lower() in {'.dll','.pyd'}:
                runtime.setdefault(digest(path),[]).append(path.relative_to(base).as_posix())
    rows=[]
    for path in sorted((ROOT/'dist/Luma').rglob('*')):
        if not path.is_file() or path.suffix.lower() not in {'.dll','.pyd','.onnx'}:continue
        value=digest(path)
        rows.append({'file':path.relative_to(ROOT/'dist/Luma').as_posix(),'sha256':value,
                     'bytes':path.stat().st_size,'distribution_matches':installed.get(value,[]),
                     'python_runtime_matches':runtime.get(value,[])})
    report={'scope':'Actual packaged native/model files; package identity is not corresponding-source clearance',
            'python_runtime_version':sys.version.split()[0],
            'files':rows,'unmatched_files':[v['file'] for v in rows if not v['distribution_matches'] and not v['python_runtime_matches']]}
    output=ROOT/'release/local-audit/native-components.json'
    output.write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps({'native_files':len(rows),'matched_files':sum(bool(v['distribution_matches']) for v in rows),
                      'python_runtime_matches':sum(bool(v['python_runtime_matches']) for v in rows),
                      'unmatched':report['unmatched_files']},indent=2))


if __name__=='__main__':main()
