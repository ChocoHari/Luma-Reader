import os
from pathlib import Path
import re
import sys
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from native_policy import excluded_binary,verify_native_policy


def test_policy_handles_windows_paths_case_and_future_video_plugin_versions():
    assert excluded_binary(r'PySide6\Qt6Quick.DLL')
    assert excluded_binary('cv2/opencv_videoio_ffmpeg9999_64.dll')
    assert not excluded_binary('LICENSE.Qt6Qml.txt')
    assert not excluded_binary('PySide6/avcodec-63.dll')


@pytest.mark.skipif(os.name!='nt',reason='Windows PE dependency check')
def test_dependency_guard_detects_imports_of_removed_libraries(tmp_path):
    # Change an import name in a temporary PE copy; never execute the copy.
    data=Path(sys.executable).read_bytes()
    assert re.search(b'kernel32.dll\x00',data,re.I)
    data=re.sub(b'kernel32.dll\x00',b'Qt6Quick.dll\x00',data,flags=re.I)
    target=tmp_path/'_internal/Qt6Widgets.dll';target.parent.mkdir()
    target.write_bytes(data)
    with pytest.raises(RuntimeError,match='qt6quick.dll'):
        verify_native_policy(tmp_path)
