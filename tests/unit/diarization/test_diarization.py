from unittest.mock import MagicMock, patch

import pytest

from config.settings import Settings
from models import AudioMetadata, DiarizationSegment
from pipeline.diarization.exceptions import (
    DiarizationAudioInvalidError,
    DiarizationAuthError,
    DiarizationError,
    DiarizationInferenceError,
)
from pipeline.diarization.pyannote_provider import PyannoteDiarizationProvider
from pipeline.diarization.service import DiarizationService


@pytest.fixture(autouse=True)
def clear_singleton():
    PyannoteDiarizationProvider._instance = None
    yield
    PyannoteDiarizationProvider._instance = None


@pytest.fixture
def audio_metadata():
    return AudioMetadata(
        call_id="CALL_DIAR",
        filename="test.wav",
        original_format="wav",
        duration=10.0,
        sample_rate=16000,
        channels=1,
        processed_audio_path="/path/to/processed_audio.wav",
        file_size=1024,
    )


@pytest.fixture
def mock_pipeline():
    with patch("pipeline.diarization.pyannote_provider.Pipeline") as mock:
        yield mock


def test_missing_processed_path(audio_metadata):
    audio_metadata.processed_audio_path = ""
    # With DIARIZATION_ENABLED=True, service loads model on init. 
    # Let's patch settings to avoid model load for this simple check.
    with patch("pipeline.diarization.service.get_settings") as mock_settings:
        mock_s = Settings()
        mock_s.DIARIZATION_ENABLED = False
        mock_settings.return_value = mock_s
        
        service = DiarizationService()
        with pytest.raises(DiarizationError, match="disabled"):
            service.process(audio_metadata)
            
    with patch("pipeline.diarization.service.get_settings") as mock_settings:
        mock_s = Settings()
        mock_s.DIARIZATION_ENABLED = True
        mock_settings.return_value = mock_s
        
        # Patch load_model so it doesn't fail
        with patch.object(PyannoteDiarizationProvider, 'load_model'):
            service = DiarizationService()
            with pytest.raises(DiarizationAudioInvalidError):
                service.process(audio_metadata)


def test_model_load_failure(mock_pipeline):
    mock_pipeline.from_pretrained.return_value = None
    provider = PyannoteDiarizationProvider()
    with pytest.raises(DiarizationAuthError):
        provider.load_model()


def test_authentication_failure(mock_pipeline):
    mock_pipeline.from_pretrained.side_effect = Exception(
        "401 Client Error: Unauthorized for url"
    )
    provider = PyannoteDiarizationProvider()
    with pytest.raises(DiarizationAuthError):
        provider.load_model()


def test_inference_failure(mock_pipeline, audio_metadata):
    mock_pipeline_instance = MagicMock()
    mock_pipeline_instance.side_effect = Exception("CUDA error")
    mock_pipeline.from_pretrained.return_value = mock_pipeline_instance

    provider = PyannoteDiarizationProvider()
    provider.load_model()

    service = DiarizationService(provider=provider)
    with pytest.raises(DiarizationInferenceError):
        service.process(audio_metadata)


def test_successful_diarization(mock_pipeline, audio_metadata):
    mock_pipeline_instance = MagicMock()
    mock_pipeline.from_pretrained.return_value = mock_pipeline_instance

    class MockTurn:
        def __init__(self, start, end):
            self.start = start
            self.end = end

    class MockAnnotation:
        def itertracks(self, yield_label):
            return [
                (MockTurn(0.0, 2.5), None, "SPEAKER_00"),
                (MockTurn(2.0, 4.0), None, "SPEAKER_01"), # overlap
            ]

    mock_pipeline_instance.return_value = MockAnnotation()

    provider = PyannoteDiarizationProvider()
    provider.load_model()

    service = DiarizationService(provider=provider)
    segments, metadata = service.process(audio_metadata)

    assert len(segments) == 2
    assert segments[0].speaker == "SPEAKER_00"
    assert segments[0].start == 0.0
    assert segments[0].end == 2.5
    
    assert segments[1].speaker == "SPEAKER_01"
    assert segments[1].start == 2.0
    assert segments[1].end == 4.0

    assert metadata.speaker_count == 2
    assert metadata.duration == 10.0


def test_empty_diarization(mock_pipeline, audio_metadata):
    mock_pipeline_instance = MagicMock()
    mock_pipeline.from_pretrained.return_value = mock_pipeline_instance

    class MockAnnotation:
        def itertracks(self, yield_label):
            return []

    mock_pipeline_instance.return_value = MockAnnotation()

    provider = PyannoteDiarizationProvider()
    provider.load_model()

    service = DiarizationService(provider=provider)
    segments, metadata = service.process(audio_metadata)

    assert len(segments) == 0
    assert metadata.speaker_count == 0


def test_invalid_timestamps():
    with pytest.raises(ValueError):
        DiarizationSegment(start=5.0, end=4.0, speaker="SPEAKER_00")
