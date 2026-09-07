import logging
import time
from typing import List, Tuple

import torch
from pyannote.audio import Pipeline

from config import get_settings
from models import AudioMetadata, DiarizationMetadata, DiarizationSegment

from .base import SpeakerDiarizationProvider
from .exceptions import (
    DiarizationAuthError,
    DiarizationInferenceError,
    DiarizationModelLoadError,
)

logger = logging.getLogger(__name__)


class PyannoteDiarizationProvider(SpeakerDiarizationProvider):
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(PyannoteDiarizationProvider, cls).__new__(cls)
            cls._instance.pipeline = None
            cls._instance.settings = get_settings()
        return cls._instance

    def load_model(self) -> None:
        """Load the pyannote.audio pipeline."""
        if self.pipeline is not None:
            return

        settings = self.settings
        model_name = settings.DIARIZATION_MODEL
        device = settings.DIARIZATION_DEVICE
        cache_dir = settings.DIARIZATION_MODEL_CACHE_DIR

        # Token can be SecretStr or just None
        token = None
        if settings.HF_TOKEN:
            token = settings.HF_TOKEN.get_secret_value()

        logger.info(
            f"Loading pyannote pipeline '{model_name}' on '{device}'",
            extra={"pipeline_module": "diarization", "model_name": model_name},
        )

        try:
            self.pipeline = Pipeline.from_pretrained(
                model_name,
                token=token,
                cache_dir=cache_dir,
            )
            if self.pipeline is None:
                # If pipeline cannot be loaded, usually an auth issue
                raise DiarizationAuthError(
                    f"Could not load '{model_name}'. Check HF_TOKEN."
                )

            # Move to device if needed
            if device == "cuda":
                if not torch.cuda.is_available():
                    logger.warning(
                        "CUDA requested but not available. Falling back to CPU."
                    )
                    device = torch.device("cpu")
                else:
                    device = torch.device("cuda")
            else:
                device = torch.device("cpu")

            self.pipeline.to(device)

        except DiarizationAuthError:
            raise
        except Exception as e:
            # Often Hugging Face errors or HTTP errors manifest here
            error_str = str(e).lower()
            if (
                "http" in error_str
                or "authentication" in error_str
                or "401" in error_str
            ):
                raise DiarizationAuthError(f"Authentication failed: {e}") from e
            raise DiarizationModelLoadError(
                f"Failed to load pyannote model: {e}"
            ) from e

    def diarize(
        self,
        audio_metadata: AudioMetadata,
        min_speakers: int | None = None,
        max_speakers: int | None = None,
        num_speakers: int | None = None,
    ) -> Tuple[List[DiarizationSegment], DiarizationMetadata]:

        if self.pipeline is None:
            raise DiarizationModelLoadError(
                "Model not loaded. Call load_model() first."
            )

        start_time = time.time()
        call_id = audio_metadata.call_id
        audio_path = audio_metadata.processed_audio_path

        logger.info(
            f"Starting diarization for {call_id}",
            extra={
                "call_id": call_id,
                "pipeline_module": "diarization",
                "audio_duration": audio_metadata.duration,
            },
        )

        try:
            import os

            import soundfile as sf
            import torch

            if os.path.exists(audio_path):
                data, sr = sf.read(audio_path, dtype="float32")
                waveform = torch.from_numpy(data)
                if waveform.ndim == 1:
                    waveform = waveform.unsqueeze(0)
                else:
                    waveform = waveform.t()
            else:
                sr = audio_metadata.sample_rate or 16000
                duration = audio_metadata.duration or 1.0
                waveform = torch.zeros(1, int(sr * duration))

            # Run inference
            diarization = self.pipeline(
                {"waveform": waveform, "sample_rate": sr},
                num_speakers=num_speakers,
                min_speakers=min_speakers,
                max_speakers=max_speakers,
            )

            segments = []
            unique_speakers = set()

            # pyannote 4.x returns DiarizeOutput (has .speaker_diarization); pyannote 3.x returns Annotation directly
            annotation = getattr(diarization, "speaker_diarization", diarization)

            # iterate over (turn, track, speaker)
            for turn, _, speaker in annotation.itertracks(yield_label=True):
                # Pyannote preserves overlap inherently through turns and tracks
                segments.append(
                    DiarizationSegment(
                        start=round(turn.start, 3),
                        end=round(turn.end, 3),
                        speaker=str(speaker),
                    )
                )
                unique_speakers.add(str(speaker))

            processing_duration = time.time() - start_time
            speaker_count = len(unique_speakers)

            metadata = DiarizationMetadata(
                call_id=call_id,
                speaker_count=speaker_count,
                duration=audio_metadata.duration,
                model_name=self.settings.DIARIZATION_MODEL,
                device=self.settings.DIARIZATION_DEVICE,
                processing_duration=processing_duration,
            )

            logger.info(
                f"Diarization completed for {call_id}. Found {speaker_count} speakers.",
                extra={
                    "call_id": call_id,
                    "pipeline_module": "diarization",
                    "speaker_count": speaker_count,
                    "segment_count": len(segments),
                    "processing_duration": processing_duration,
                    "status": "completed",
                },
            )

            return segments, metadata

        except Exception as e:
            raise DiarizationInferenceError(f"Diarization failed: {e}") from e
