import logging
import time
from pathlib import Path

from config import get_settings
from models import AudioInput, AudioMetadata

from . import ffmpeg
from .exceptions import (
    AudioFileNotFoundError,
    AudioProcessingError,
    EmptyAudioFileError,
    UnsupportedAudioFormatError,
)

logger = logging.getLogger(__name__)


class AudioPreprocessor:
    def __init__(self):
        self.settings = get_settings()
        self.supported_formats = [
            fmt.strip().lower()
            for fmt in self.settings.SUPPORTED_AUDIO_FORMATS.split(",")
        ]

    def process(self, audio_input: AudioInput) -> AudioMetadata:
        """Process and normalize the audio file."""
        start_time = time.time()
        call_id = audio_input.call_id
        input_path = Path(audio_input.audio_path)

        logger.info(
            f"Starting audio preprocessing for {call_id}",
            extra={
                "call_id": call_id,
                "pipeline_module": "preprocessing",
                "input_filename": input_path.name,
                "status": "started",
            },
        )

        try:
            # 1 & 2 & 3. Validate path and file existence
            if not input_path.exists() or not input_path.is_file():
                raise AudioFileNotFoundError(f"Audio file not found: {input_path}")

            # Empty file check
            if input_path.stat().st_size == 0:
                raise EmptyAudioFileError(f"Audio file is empty: {input_path}")

            # 4. Validate supported format
            ext = input_path.suffix.lstrip(".").lower()
            if ext not in self.supported_formats:
                raise UnsupportedAudioFormatError(
                    f"Unsupported format '{ext}'. Supported: {self.supported_formats}"
                )

            # 5 & 6. Detect metadata & dependencies
            ffmpeg.check_dependencies()
            raw_meta = ffmpeg.get_metadata(input_path)

            # Extract fields safely
            format_info = raw_meta.get("format", {})
            streams = raw_meta.get("streams", [])
            audio_stream = next(
                (s for s in streams if s.get("codec_type") == "audio"), {}
            )

            duration = float(format_info.get("duration", 0.0))
            if duration <= 0.0:
                duration = float(audio_stream.get("duration", 0.0))

            codec = audio_stream.get("codec_name", "unknown")
            file_size = int(format_info.get("size", 0))

            # 8. Create normalized output directory
            artifact_dir = Path("artifacts") / call_id / "audio"
            artifact_dir.mkdir(parents=True, exist_ok=True)
            output_path = artifact_dir / "processed_audio.wav"

            # 9. Convert to WAV, PCM, mono, 16 kHz
            target_sr = self.settings.AUDIO_SAMPLE_RATE
            target_channels = self.settings.AUDIO_CHANNELS
            
            ffmpeg.convert_audio(
                input_path, output_path, sample_rate=target_sr, channels=target_channels
            )

            # 10. Validate generated output
            if not output_path.exists() or output_path.stat().st_size == 0:
                raise AudioProcessingError("Generated output file is missing or empty.")

            processing_duration = time.time() - start_time

            logger.info(
                f"Audio preprocessing completed for {call_id}",
                extra={
                    "call_id": call_id,
                    "pipeline_module": "preprocessing",
                    "input_filename": input_path.name,
                    "output_path": str(output_path),
                    "duration": duration,
                    "status": "completed",
                    "processing_duration": processing_duration,
                },
            )

            # 11. Return AudioMetadata
            return AudioMetadata(
                call_id=call_id,
                filename=input_path.name,
                original_format=ext,
                duration=duration,
                sample_rate=target_sr,
                channels=target_channels,
                processed_audio_path=str(output_path),
                file_size=file_size,
                codec=codec,
            )

        except Exception as e:
            processing_duration = time.time() - start_time
            logger.error(
                f"Audio preprocessing failed for {call_id}: {str(e)}",
                extra={
                    "call_id": call_id,
                    "pipeline_module": "preprocessing",
                    "input_filename": input_path.name,
                    "status": "failed",
                    "processing_duration": processing_duration,
                    "error": str(e),
                },
            )
            raise
