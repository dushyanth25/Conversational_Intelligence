import sys

import pytest
import torch

from pipeline.vad.model import SileroVADModel

if getattr(sys.modules.get("torch", None), "__version__", None) == "mocked":
    pytestmark = pytest.mark.skip(reason="Torch is not installed")

def test_silero_model_load_and_inference():
    """Integration test to verify real Silero VAD loads and runs."""
    model = SileroVADModel()
    
    # Load model (downloads if not cached)
    model.load()
    
    # Create fake audio 1 sec of zeros
    fake_audio = torch.zeros(16000)
    
    # Should not crash, and should probably return empty speech segments
    timestamps = model.get_speech_timestamps(fake_audio, sampling_rate=16000)
    
    assert isinstance(timestamps, list)
