from unittest.mock import patch

import pytest
import torch

from models import AudioMetadata
from pipeline.vad.exceptions import (
    VADAudioInvalidError,
    VADDisabledError,
    VADInferenceError,
)
from pipeline.vad.service import VADService


@pytest.fixture
def mock_torchaudio():
    with patch("pipeline.vad.service.torchaudio") as mock:
        yield mock


@pytest.fixture
def mock_vad_model():
    with patch("pipeline.vad.service.SileroVADModel") as mock:
        yield mock


@pytest.fixture
def audio_metadata():
    return AudioMetadata(
        call_id="CALL_VAD",
        filename="test.wav",
        original_format="wav",
        duration=10.0,
        sample_rate=16000,
        channels=1,
        processed_audio_path="/path/to/processed_audio.wav",
        file_size=1024,
    )


def test_vad_disabled(audio_metadata):
    with patch("pipeline.vad.service.get_settings") as mock_settings:
        mock_settings.return_value.VAD_ENABLED = False
        service = VADService()
        with pytest.raises(VADDisabledError):
            service.process(audio_metadata)


def test_invalid_sample_rate(audio_metadata):
    audio_metadata.sample_rate = 8000
    service = VADService()
    with pytest.raises(VADAudioInvalidError):
        service.process(audio_metadata)


def test_invalid_channels(audio_metadata):
    audio_metadata.channels = 2
    service = VADService()
    with pytest.raises(VADAudioInvalidError):
        service.process(audio_metadata)


def test_missing_processed_path(audio_metadata):
    audio_metadata.processed_audio_path = ""
    service = VADService()
    with pytest.raises(VADAudioInvalidError):
        service.process(audio_metadata)


def test_empty_audio(mock_torchaudio, mock_vad_model, audio_metadata):
    # Mock empty tensor: [channels, time]
    mock_torchaudio.load.return_value = (torch.zeros(1, 0), 16000)

    service = VADService()
    segments = service.process(audio_metadata)

    assert len(segments) == 0


def test_no_speech(mock_torchaudio, mock_vad_model, audio_metadata):
    mock_torchaudio.load.return_value = (torch.zeros(1, 160000), 16000)
    mock_instance = mock_vad_model.return_value
    mock_instance.get_speech_timestamps.return_value = []

    service = VADService()
    segments = service.process(audio_metadata)

    assert len(segments) == 0


def test_one_speech_region(mock_torchaudio, mock_vad_model, audio_metadata):
    mock_torchaudio.load.return_value = (torch.zeros(1, 160000), 16000)
    mock_instance = mock_vad_model.return_value
    # Silero output is in samples. 16000 samples = 1 sec
    mock_instance.get_speech_timestamps.return_value = [
        {"start": 16000, "end": 32000}
    ]

    service = VADService()
    segments = service.process(audio_metadata)

    assert len(segments) == 1
    assert segments[0].start == 1.0
    assert segments[0].end == 2.0
    assert segments[0].is_speech is True


def test_multiple_speech_regions(mock_torchaudio, mock_vad_model, audio_metadata):
    mock_torchaudio.load.return_value = (torch.zeros(1, 160000), 16000)
    mock_instance = mock_vad_model.return_value
    mock_instance.get_speech_timestamps.return_value = [
        {"start": 16000, "end": 32000},
        {"start": 64000, "end": 80000},
    ]

    service = VADService()
    segments = service.process(audio_metadata)

    assert len(segments) == 2
    assert segments[0].start == 1.0
    assert segments[0].end == 2.0
    assert segments[1].start == 4.0
    assert segments[1].end == 5.0
    
    # Check ordering
    assert segments[0].start < segments[1].start


def test_inference_failure(mock_torchaudio, mock_vad_model, audio_metadata):
    mock_torchaudio.load.return_value = (torch.zeros(1, 160000), 16000)
    mock_instance = mock_vad_model.return_value
    mock_instance.get_speech_timestamps.side_effect = VADInferenceError("Failed")

    service = VADService()
    with pytest.raises(VADInferenceError):
        service.process(audio_metadata)
