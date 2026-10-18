"""Preserve the licence shipped with the Python interpreter used to freeze Luma."""
import hashlib
from pathlib import Path
import sys


def copy_python_notice(output, base_prefix=None, version=None):
    source = Path(base_prefix or sys.base_prefix) / 'LICENSE.txt'
    if not source.is_file():
        raise RuntimeError('Python runtime LICENSE.txt is missing; cannot package runtime notices')
    payload = source.read_bytes()
    if not payload.strip():
        raise RuntimeError('Python runtime LICENSE.txt is empty')
    output = Path(output)
    target = output / 'third-party-notices/Python/LICENSE.txt'
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(payload)
    return {'package': 'Python', 'version': version or sys.version.split()[0],
            'file': target.relative_to(output).as_posix(),
            'sha256': hashlib.sha256(payload).hexdigest()}
