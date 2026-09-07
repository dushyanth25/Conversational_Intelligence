import logging
import math
import time
from typing import List, Optional, Tuple

from faster_whisper import WhisperModel

from config import get_settings
from models import (
    AudioMetadata,
    TranscriptionMetadata,
    TranscriptionWord,
    TranscriptSegment,
    VADSegment,
)

from .base import ASRProvider
from .exceptions import ASRInferenceError, ASRModelLoadError

logger = logging.getLogger(__name__)


class FasterWhisperProvider(ASRProvider):
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(FasterWhisperProvider, cls).__new__(cls)
            cls._instance.model = None
            cls._instance.settings = get_settings()
        return cls._instance

    def load_model(self) -> None:
        """Load the faster-whisper model."""
        if self.model is not None:
            return

        settings = self.settings
        model_size = settings.ASR_MODEL
        device = settings.ASR_DEVICE  # "cuda" or "cpu"
        compute_type = settings.ASR_COMPUTE_TYPE  # "float16" or "int8"
        download_root = settings.ASR_MODEL_CACHE_DIR

        logger.info(
            f"Loading faster-whisper model '{model_size}' on '{device}'",
            extra={
                "pipeline_module": "transcription",
                "model_name": model_size,
            },
        )

        try:
            self.model = WhisperModel(
                model_size_or_path=model_size,
                device=device,
                compute_type=compute_type,
                download_root=download_root,
            )
        except Exception as e:
            raise ASRModelLoadError(f"Failed to load whisper model: {e}") from e

    def transcribe(
        self,
        audio_metadata: AudioMetadata,
        vad_segments: Optional[List[VADSegment]] = None,
    ) -> Tuple[List[TranscriptSegment], TranscriptionMetadata]:
        """Transcribe audio using faster-whisper."""
        if self.model is None:
            raise ASRModelLoadError("Model not loaded. Call load_model() first.")

        start_time = time.time()
        call_id = audio_metadata.call_id
        audio_path = audio_metadata.processed_audio_path

        # Configure language
        language = self.settings.ASR_LANGUAGE
        if language and language.lower() == "auto":
            language = None  # None lets faster-whisper detect it

        logger.info(
            f"Starting transcription for {call_id}",
            extra={
                "call_id": call_id,
                "pipeline_module": "transcription",
                "audio_duration": audio_metadata.duration,
            },
        )

        try:
            segments_generator, info = self.model.transcribe(
                audio_path,
                beam_size=5,
                language=language,
                word_timestamps=True,
                vad_filter=True if vad_segments is None else False,
            )

            transcript_segments = []
            for segment in segments_generator:
                words = []
                if segment.words:
                    for w in segment.words:
                        end_time = w.end
                        if end_time <= w.start:
                            end_time = w.start + 0.01
                        words.append(
                            TranscriptionWord(
                                start=w.start,
                                end=end_time,
                                word=w.word,
                                probability=w.probability,
                            )
                        )

                confidence = (
                    math.exp(segment.avg_logprob)
                    if segment.avg_logprob < 0
                    else 1.0
                )
                confidence = max(0.0, min(1.0, confidence))

                segment_end = segment.end
                if segment_end <= segment.start:
                    segment_end = segment.start + 0.01

                transcript_segments.append(
                    TranscriptSegment(
                        start=segment.start,
                        end=segment_end,
                        text=segment.text.strip(),
                        confidence=confidence,
                        language=info.language,
                        words=words if words else None,
                    )
                )

            processing_duration = time.time() - start_time

            metadata = TranscriptionMetadata(
                call_id=call_id,
                detected_language=info.language,
                language_probability=info.language_probability,
                duration=audio_metadata.duration,
                segment_count=len(transcript_segments),
                model_name=self.settings.ASR_MODEL,
                device=self.settings.ASR_DEVICE,
                processing_duration=processing_duration,
            )

            logger.info(
                f"Transcription completed for {call_id}. "
                f"Found {len(transcript_segments)} segments.",
                extra={
                    "call_id": call_id,
                    "pipeline_module": "transcription",
                    "segment_count": len(transcript_segments),
                    "processing_duration": processing_duration,
                    "language": info.language,
                },
            )

            return transcript_segments, metadata

        except Exception as e:
            raise ASRInferenceError(f"Transcription failed: {e}") from e
