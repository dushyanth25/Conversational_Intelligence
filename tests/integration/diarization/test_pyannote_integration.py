
import pytest

from config import get_settings
from pipeline.diarization.pyannote_provider import PyannoteDiarizationProvider

try:
    import pyannote.audio  # noqa: F401
except ImportError:
    pytestmark = pytest.mark.skip(reason="pyannote.audio is not installed")

def test_pyannote_model_load():
    """Integration test to verify pyannote model loads, requires HF_TOKEN."""
    settings = get_settings()
    if not settings.HF_TOKEN:
        pytest.skip("HF_TOKEN is not configured")
        
    provider = PyannoteDiarizationProvider()
    provider.load_model()
    assert provider.pipeline is not None
