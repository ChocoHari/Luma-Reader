"""Verify privacy configuration before the inference SDK is initialized."""
import os
from pathlib import Path
import subprocess
import sys


def test_fresh_process_disables_sdk_before_import_and_reapplies_policy(tmp_path):
    # A fake SDK observes the environment at its first import, before any API
    # call could repair startup ordering. No network or model is needed.
    (tmp_path/'onnxruntime.py').write_text(
        "import os\n"
        "assert os.environ['ORT_DISABLE_TELEMETRY']=='1'\n"
        "calls=0\n"
        "def disable_telemetry_events():\n"
        "    global calls\n"
        "    calls+=1\n",encoding='utf-8')
    root=Path(__file__).resolve().parents[1]
    env=os.environ.copy()
    env['PYTHONPATH']=os.pathsep.join((str(tmp_path),str(root)))
    env['ORT_DISABLE_TELEMETRY']='0'
    subprocess.run([sys.executable,'-c',
        "import os,sys; import runtime_privacy as p; "
        "assert 'onnxruntime' not in sys.modules; "
        "sdk=p.prepare_inference_runtime(); "
        "os.environ['ORT_DISABLE_TELEMETRY']='0'; "
        "assert p.prepare_inference_runtime() is sdk; "
        "assert sdk.calls==2; assert os.environ['ORT_DISABLE_TELEMETRY']=='1'"],
        cwd=tmp_path,env=env,check=True,timeout=15)


def test_configuration_failure_does_not_silently_continue(monkeypatch):
    import types
    import pytest
    import runtime_privacy
    def fail():
        raise RuntimeError('Privacy configuration failed')
    monkeypatch.setitem(sys.modules,'onnxruntime',types.SimpleNamespace(disable_telemetry_events=fail))
    with pytest.raises(RuntimeError,match='Privacy configuration failed'):
        runtime_privacy.prepare_inference_runtime()
