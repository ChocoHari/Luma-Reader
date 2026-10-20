from pathlib import Path
import sys
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from build_installer import installer_version


def test_version_tracks_next_installer_instead_of_old_fixture(tmp_path):
    (tmp_path/'installer').mkdir()
    spec=tmp_path/'installer/Luma.iss'
    for version in ('0.3.1-dev','1.2.0'):
        spec.write_text(f'#ifndef AppVersion\n#define AppVersion "{version}"\n#endif\n',encoding='utf-8')
        assert installer_version(tmp_path)==version


@pytest.mark.parametrize('source',['#define AppVersion "../old"',
    '#define AppVersion "0.3.1-dev"\n#define AppVersion "0.3.0-dev"',''])
def test_ambiguous_or_unsafe_versions_fail_before_install(tmp_path,source):
    (tmp_path/'installer').mkdir()
    (tmp_path/'installer/Luma.iss').write_text(source,encoding='utf-8')
    with pytest.raises(ValueError):installer_version(tmp_path)
