from runtime_paths import data_directory,migrate_legacy_data


def test_user_portable_and_override_paths(tmp_path):
    assert data_directory({'LOCALAPPDATA':str(tmp_path)},home=tmp_path)==tmp_path/'Luma Reader'
    exe=tmp_path/'portable'/'Luma.exe'
    assert data_directory({'LUMA_PORTABLE':'1'},executable=exe)==exe.parent/'Luma Data'
    assert data_directory({'LUMA_DATA_DIR':str(tmp_path/'custom'),'LUMA_PORTABLE':'1'})==tmp_path/'custom'


def test_migration_copies_only_known_files_without_overwrite(tmp_path):
    source=tmp_path/'old';target=tmp_path/'new'
    (source/'ocr'/'book').mkdir(parents=True)
    (source/'recovery').mkdir()
    (source/'settings.json').write_text('{"old":true}')
    (source/'ocr'/'book'/'1.json').write_text('{"text":"cached"}')
    (source/'recovery'/'draft.json').write_text('{"text":"note"}')
    (source/'private.pdf').write_bytes(b'private')
    (source/'application.log').write_text('private diagnostics')
    target.mkdir();(target/'settings.json').write_text('{"new":true}')
    assert migrate_legacy_data(source,target)==2
    assert (target/'settings.json').read_text()=='{"new":true}'
    assert not (target/'private.pdf').exists()
    assert not (target/'application.log').exists()
    assert (source/'recovery'/'draft.json').exists()
    (target/'recovery'/'draft.json').unlink()
    assert migrate_legacy_data(source,target)==0
    assert not (target/'recovery'/'draft.json').exists()
    assert migrate_legacy_data(source,source)==0
