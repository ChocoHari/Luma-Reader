from pathlib import Path
import sys
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from build_installer import installer_version,upgrade_installers


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


def test_upgrade_uses_current_version_and_explicit_retained_baseline(tmp_path):
    (tmp_path/'installer').mkdir()
    (tmp_path/'installer/Luma.iss').write_text('#define AppVersion "0.3.2-dev"\n')
    old=tmp_path/'saved/old.exe';old.parent.mkdir();old.write_bytes(b'not executed')
    pair=upgrade_installers(tmp_path,'saved/old.exe','0.3.1-dev')
    assert pair['old']==old
    assert pair['new']==tmp_path/'dist/installer/Luma-0.3.2-dev-Setup.exe'
    assert (pair['from_version'],pair['to_version'])==('0.3.1-dev','0.3.2-dev')
    with pytest.raises(ValueError,match='inside the project'):
        upgrade_installers(tmp_path,tmp_path.parent/'external.exe','0.3.1-dev')
    with pytest.raises(ValueError,match='different versions'):
        upgrade_installers(tmp_path,old,'0.3.2-dev')
    with pytest.raises(FileNotFoundError):
        upgrade_installers(tmp_path,'missing.exe','0.3.1-dev')
