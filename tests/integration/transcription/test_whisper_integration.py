
import pytest

from pipeline.transcription.faster_whisper_provider import FasterWhisperProvider

# Skip if faster_whisper is not installed
try:
    import faster_whisper  # noqa: F401
except ImportError:
    pytestmark = pytest.mark.skip(reason="faster-whisper is not installed")

def test_whisper_model_load():
    """Integration test to verify faster-whisper loads without errors."""
    provider = FasterWhisperProvider()
    provider.load_model()
    assert provider.model is not None
