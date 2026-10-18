"""Reject model files outside the explicitly reviewed package paths."""
from pathlib import Path


def verify_model_allowlist(output, allowed_paths):
    output=Path(output)
    allowed=set(allowed_paths)
    actual={p.relative_to(output).as_posix() for p in output.rglob('*') if p.is_file() and p.suffix.casefold()=='.onnx'}
    unexpected=actual-allowed
    missing=allowed-actual
    if unexpected or missing:
        raise RuntimeError(f'Packaged model allowlist mismatch: unexpected={sorted(unexpected)}, missing={sorted(missing)}')
    return sorted(actual)
