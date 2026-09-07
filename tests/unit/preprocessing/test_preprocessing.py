from pathlib import Path
from unittest.mock import patch

import pytest

from models import AudioInput
from pipeline.preprocessing.exceptions import (
    AudioFileNotFoundError,
    AudioProcessingError,
    CorruptedAudioError,
    EmptyAudioFileError,
    UnsupportedAudioFormatError,
)
from pipeline.preprocessing.service import AudioPreprocessor


@pytest.fixture
def preprocessor():
    return AudioPreprocessor()


@pytest.fixture
def mock_ffmpeg():
    with patch("pipeline.preprocessing.service.ffmpeg") as mock:
        mock.get_metadata.return_value = {
            "format": {"duration": "125.4", "size": "1024"},
            "streams": [
                {
                    "codec_type": "audio",
                    "sample_rate": "44100",
                    "channels": "2",
                    "codec_name": "mp3",
                }
            ],
        }
        yield mock


@pytest.fixture
def audio_input(tmp_path):
    # Create a dummy file
    audio_file = tmp_path / "test.mp3"
    audio_file.write_bytes(b"dummy data")
    return AudioInput(
        audio_path=str(audio_file), prompt_sheet="prompts.csv", call_id="CALL_001"
    )


def test_missing_file(preprocessor):
    audio_input = AudioInput(audio_path="nonexistent.wav", prompt_sheet="prompts.csv")
    with pytest.raises(AudioFileNotFoundError):
        preprocessor.process(audio_input)


def test_empty_file(preprocessor, tmp_path):
    empty_file = tmp_path / "empty.wav"
    empty_file.touch()
    audio_input = AudioInput(audio_path=str(empty_file), prompt_sheet="prompts.csv")
    with pytest.raises(EmptyAudioFileError):
        preprocessor.process(audio_input)


def test_unsupported_extension(preprocessor, tmp_path):
    unsupported_file = tmp_path / "video.mp4"
    unsupported_file.write_bytes(b"data")
    audio_input = AudioInput(
        audio_path=str(unsupported_file), prompt_sheet="prompts.csv"
    )
    with pytest.raises(UnsupportedAudioFormatError):
        preprocessor.process(audio_input)


def test_successful_processing(preprocessor, mock_ffmpeg, audio_input):
    # Mock the conversion to actually create an output file so validation passes
    def mock_convert(in_path, out_path, **kwargs):
        out_path = Path(out_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_bytes(b"fake wav data")

    mock_ffmpeg.convert_audio.side_effect = mock_convert

    metadata = preprocessor.process(audio_input)

    assert metadata.call_id == "CALL_001"
    assert metadata.original_format == "mp3"
    assert metadata.duration == 125.4
    assert metadata.sample_rate == 16000
    assert metadata.channels == 1
    assert "processed_audio.wav" in metadata.processed_audio_path

    # Verify ffmpeg was called
    mock_ffmpeg.check_dependencies.assert_called_once()
    mock_ffmpeg.get_metadata.assert_called_once()
    mock_ffmpeg.convert_audio.assert_called_once()


def test_ffmpeg_failure(preprocessor, mock_ffmpeg, audio_input):
    mock_ffmpeg.convert_audio.side_effect = AudioProcessingError("conversion failed")

    with pytest.raises(AudioProcessingError):
        preprocessor.process(audio_input)


def test_output_missing_validation(preprocessor, mock_ffmpeg, audio_input):
    audio_input.call_id = "CALL_MISSING"
    # Convert doesn't create the file
    def mock_convert_no_op(in_path, out_path, **kwargs):
        pass

    mock_ffmpeg.convert_audio.side_effect = mock_convert_no_op

    with pytest.raises(AudioProcessingError, match="missing or empty"):
        preprocessor.process(audio_input)


def test_corrupted_audio(preprocessor, audio_input):
    with patch(
        "pipeline.preprocessing.service.ffmpeg.get_metadata"
    ) as mock_get_metadata:
        with patch("pipeline.preprocessing.service.ffmpeg.check_dependencies"):
            mock_get_metadata.side_effect = CorruptedAudioError("Corrupted")
            with pytest.raises(CorruptedAudioError):
                preprocessor.process(audio_input)


def test_supported_formats(preprocessor, tmp_path, mock_ffmpeg):
    def mock_convert(in_path, out_path, **kwargs):
        out_path = Path(out_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_bytes(b"fake wav data")

    mock_ffmpeg.convert_audio.side_effect = mock_convert

    formats = ["wav", "mp3", "m4a", "flac"]
    for ext in formats:
        file = tmp_path / f"test.{ext}"
        file.write_bytes(b"data")
        audio_input = AudioInput(
            audio_path=str(file), prompt_sheet="prompts.csv", call_id=f"CALL_{ext}"
        )
        metadata = preprocessor.process(audio_input)
        assert metadata.original_format == ext
