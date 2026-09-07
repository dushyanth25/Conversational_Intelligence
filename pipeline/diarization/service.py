import logging
from typing import List, Optional, Tuple

from config import get_settings
from models import AudioMetadata, DiarizationMetadata, DiarizationSegment

from .base import SpeakerDiarizationProvider
from .exceptions import DiarizationAudioInvalidError, DiarizationError
from .pyannote_provider import PyannoteDiarizationProvider

logger = logging.getLogger(__name__)


class DiarizationService:
    def __init__(self, provider: Optional[SpeakerDiarizationProvider] = None):
        self.settings = get_settings()
        self.provider = provider or PyannoteDiarizationProvider()
        if self.settings.DIARIZATION_ENABLED and provider is None:
            self.provider.load_model()

    def process(
        self,
        audio_metadata: AudioMetadata,
        min_speakers: Optional[int] = None,
        max_speakers: Optional[int] = None,
        num_speakers: Optional[int] = None,
    ) -> Tuple[List[DiarizationSegment], DiarizationMetadata]:

        call_id = audio_metadata.call_id

        if not self.settings.DIARIZATION_ENABLED:
            logger.info(
                f"Diarization disabled for {call_id}. Bypassing.",
                extra={
                    "call_id": call_id,
                    "pipeline_module": "diarization",
                    "status": "disabled",
                },
            )
            raise DiarizationError(f"Diarization is disabled in configuration for {call_id}")

        if not audio_metadata.processed_audio_path:
            raise DiarizationAudioInvalidError(
                "Missing processed audio path in metadata."
            )

        return self.provider.diarize(
            audio_metadata,
            min_speakers=min_speakers,
            max_speakers=max_speakers,
            num_speakers=num_speakers,
        )
