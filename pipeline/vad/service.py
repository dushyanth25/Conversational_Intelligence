import logging
import time
from typing import List

import torchaudio

from config import get_settings
from models import AudioMetadata, VADSegment

from .exceptions import VADAudioInvalidError, VADDisabledError, VADInferenceError
from .model import SileroVADModel

logger = logging.getLogger(__name__)


class VADService:
    def __init__(self):
        self.settings = get_settings()
        self.model = SileroVADModel()

        # We only load if enabled
        if self.settings.VAD_ENABLED:
            # Use settings for model if needed, but default is standard
            self.model.load()

    def process(self, audio_metadata: AudioMetadata) -> List[VADSegment]:
        """Detect speech regions from normalized audio."""
        call_id = audio_metadata.call_id
        start_time = time.time()

        logger.info(
            f"Starting VAD processing for {call_id}",
            extra={
                "call_id": call_id,
                "pipeline_module": "vad",
                "input_filename": audio_metadata.filename,
                "status": "started",
            },
        )

        if not self.settings.VAD_ENABLED:
            logger.info(
                f"VAD disabled for {call_id}. Bypassing.",
                extra={
                    "call_id": call_id,
                    "pipeline_module": "vad",
                    "status": "bypassed",
                },
            )
            raise VADDisabledError(f"VAD is disabled in configuration for {call_id}")

        # Validate input matches normalized expectations
        # Expected: WAV, 16kHz, mono
        if audio_metadata.sample_rate != 16000:
            raise VADAudioInvalidError(
                f"Expected 16kHz audio, got {audio_metadata.sample_rate}Hz"
            )

        if audio_metadata.channels != 1:
            raise VADAudioInvalidError(
                f"Expected mono (1) audio, got {audio_metadata.channels} channels"
            )

        if not audio_metadata.processed_audio_path:
            raise VADAudioInvalidError("Missing processed_audio_path in metadata")

        try:
            try:
                waveform, sr = torchaudio.load(audio_metadata.processed_audio_path)
            except Exception:
                import soundfile as sf
                import torch
                data, sr = sf.read(audio_metadata.processed_audio_path, dtype="float32")
                waveform = torch.from_numpy(data)
                if waveform.ndim == 1:
                    waveform = waveform.unsqueeze(0)
                else:
                    waveform = waveform.t()

            # Additional check just in case file didn't match metadata
            if sr != 16000:
                raise VADAudioInvalidError(
                    f"File sample rate {sr} does not match 16kHz requirement"
                )

            if waveform.size(1) == 0:
                # empty audio
                segments = []
            else:
                # Silero expects 1D tensor for mono audio,
                # torchaudio loads as [channels, time]
                wav_tensor = waveform[0]

                # Inference
                raw_segments = self.model.get_speech_timestamps(
                    wav_tensor, sampling_rate=16000
                )

                segments = []
                for seg in raw_segments:
                    start_time_sec = round(seg["start"] / 16000.0, 3)
                    end_time_sec = round(seg["end"] / 16000.0, 3)
                    # Silero output timestamps are sample indices
                    segments.append(
                        VADSegment(
                            start=start_time_sec,
                            end=end_time_sec,
                            is_speech=True,
                        )
                    )

            processing_duration = time.time() - start_time
            logger.info(
                f"VAD processing completed for {call_id}. "
                f"Found {len(segments)} segments.",
                extra={
                    "call_id": call_id,
                    "pipeline_module": "vad",
                    "speech_segment_count": len(segments),
                    "audio_duration": audio_metadata.duration,
                    "processing_duration": processing_duration,
                    "status": "completed",
                },
            )

            return segments

        except (VADAudioInvalidError, VADInferenceError):
            raise
        except Exception as e:
            logger.error(
                f"VAD processing failed for {call_id}: {e}",
                extra={
                    "call_id": call_id,
                    "pipeline_module": "vad",
                    "status": "failed",
                    "error": str(e),
                },
            )
            raise VADInferenceError(f"Failed to process audio for VAD: {e}") from e
