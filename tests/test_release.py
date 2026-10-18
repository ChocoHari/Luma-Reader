import importlib.util
from pathlib import Path

SPEC = importlib.util.spec_from_file_location('audit_release', Path(__file__).resolve().parents[1] / 'tools/audit_release.py')
audit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit)


def test_source_paths_reject_private_traversal_and_absolute(tmp_path):
    for name in ('../private.txt', 'data/settings.json', 'C:/private.txt', '/private.txt'):
        assert audit.validate_sources(tmp_path, {'files': [name], 'excluded_directories': ['data']})


def test_source_paths_reject_missing_file(tmp_path):
    assert audit.validate_sources(tmp_path, {'files': ['missing.py'], 'excluded_directories': []})


def test_voice_selection_requires_explicit_review():
    assert not audit.approved_voices({'voices': [{'sha256': 'a', 'redistribution_approved': False}]})
    assert not audit.approved_voices({'voices': [{'sha256': 'a', 'redistribution_approved': True}]})
    voice = {'sha256': 'a', 'redistribution_approved': True, 'review_evidence': 'review.md'}
    assert audit.approved_voices({'voices': [voice]}) == [voice]


def test_actual_public_sources_and_release_gates():
    import json
    root = Path(__file__).resolve().parents[1]
    assert not audit.validate_sources(root, json.loads((root / 'release/source-allowlist.json').read_text()))
    assert json.loads((root / 'release/release-gates.json').read_text())['public_binary_approved'] is False
    assert (root / 'LICENSE').stat().st_size > 30000
