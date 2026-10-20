"""Disable inference telemetry before importing engines or creating sessions."""
import os

# Set unconditionally: Luma's local processing policy also applies when the
# parent process has explicitly enabled this SDK's telemetry.
os.environ['ORT_DISABLE_TELEMETRY'] = '1'


def prepare_inference_runtime():
    """Apply the documented API too, including older Windows runtime builds.

    Do not suppress errors: model initialization must not silently continue if
    the privacy configuration could not be applied.
    """
    os.environ['ORT_DISABLE_TELEMETRY'] = '1'
    import onnxruntime
    onnxruntime.disable_telemetry_events()
    return onnxruntime
