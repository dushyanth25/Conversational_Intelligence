from unittest.mock import patch

import pytest

from models import AudioMetadata
from pipeline.transcription.exceptions import (
    ASRAudioInvalidError,
    ASRInferenceError,
    ASRModelLoadError,
)
from pipeline.transcription.faster_whisper_provider import FasterWhisperProvider
from pipeline.transcription.service import TranscriptionService


@pytest.fixture
def audio_metadata():
    return AudioMetadata(
        call_id="CALL_ASR",
        filename="test.wav",
        original_format="wav",
        duration=10.0,
        sample_rate=16000,
        channels=1,
        processed_audio_path="/path/to/processed_audio.wav",
        file_size=1024,
    )


@pytest.fixture(autouse=True)
def clear_singleton():
    FasterWhisperProvider._instance = None
    yield
    FasterWhisperProvider._instance = None


@pytest.fixture
def mock_whisper():
    with patch("pipeline.transcription.faster_whisper_provider.WhisperModel") as mock:
        yield mock


def test_missing_processed_path(audio_metadata):
    audio_metadata.processed_audio_path = ""
    # Should raise error from service directly
    service = TranscriptionService()
    with pytest.raises(ASRAudioInvalidError):
        service.process(audio_metadata)


def test_model_load_failure(mock_whisper):
    mock_whisper.side_effect = Exception("Download failed")
    provider = FasterWhisperProvider()
    with pytest.raises(ASRModelLoadError):
        provider.load_model()


def test_inference_failure(mock_whisper, audio_metadata):
    mock_model_instance = mock_whisper.return_value
    mock_model_instance.transcribe.side_effect = Exception("CUDA error")

    provider = FasterWhisperProvider()
    provider.load_model()

    service = TranscriptionService(provider=provider)
    with pytest.raises(ASRInferenceError):
        service.process(audio_metadata)


def test_successful_transcription(mock_whisper, audio_metadata):
    mock_model_instance = mock_whisper.return_value

    # Mocking segments generator and info
    class MockSegment:
        def __init__(self, start, end, text, avg_logprob, words):
            self.start = start
            self.end = end
            self.text = text
            self.avg_logprob = avg_logprob
            self.words = words

    class MockWord:
        def __init__(self, start, end, word, probability):
            self.start = start
            self.end = end
            self.word = word
            self.probability = probability

    class MockInfo:
        def __init__(self, language, language_probability):
            self.language = language
            self.language_probability = language_probability

    mock_segments = [
        MockSegment(
            start=0.0,
            end=2.0,
            text="Hello world.",
            avg_logprob=-0.05,
            words=[
                MockWord(0.0, 1.0, "Hello", 0.99),
                MockWord(1.0, 2.0, "world.", 0.98),
            ],
        ),
        MockSegment(
            start=2.5,
            end=4.0,
            text="This is a test.",
            avg_logprob=-0.1,
            words=None,
        ),
    ]

    mock_info = MockInfo(language="en", language_probability=0.99)

    mock_model_instance.transcribe.return_value = (iter(mock_segments), mock_info)

    provider = FasterWhisperProvider()
    provider.load_model()

    service = TranscriptionService(provider=provider)
    segments, metadata = service.process(audio_metadata)

    # Assertions
    assert len(segments) == 2
    assert segments[0].text == "Hello world."
    assert segments[0].start == 0.0
    assert segments[0].end == 2.0
    assert segments[0].confidence > 0.9
    assert segments[0].language == "en"

    assert segments[0].words is not None
    assert len(segments[0].words) == 2
    assert segments[0].words[0].word == "Hello"

    assert segments[1].text == "This is a test."
    assert segments[1].words is None

    assert metadata.call_id == "CALL_ASR"
    assert metadata.detected_language == "en"
    assert metadata.language_probability == 0.99
    assert metadata.segment_count == 2
    assert metadata.duration == 10.0


def test_empty_transcription(mock_whisper, audio_metadata):
    mock_model_instance = mock_whisper.return_value

    class MockInfo:
        def __init__(self, language, language_probability):
            self.language = "en"
            self.language_probability = 0.5

    mock_info = MockInfo(language="en", language_probability=0.5)
    mock_model_instance.transcribe.return_value = (iter([]), mock_info)

    provider = FasterWhisperProvider()
    provider.load_model()

    service = TranscriptionService(provider=provider)
    segments, metadata = service.process(audio_metadata)

    assert len(segments) == 0
    assert metadata.segment_count == 0
