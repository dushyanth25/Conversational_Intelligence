import logging
from typing import List, Optional, Tuple

from config import get_settings
from models import AudioMetadata, TranscriptionMetadata, TranscriptSegment, VADSegment

from .base import ASRProvider
from .exceptions import ASRAudioInvalidError
from .faster_whisper_provider import FasterWhisperProvider

logger = logging.getLogger(__name__)


class TranscriptionService:
    def __init__(self, provider: Optional[ASRProvider] = None):
        self.settings = get_settings()
        self.provider = provider or FasterWhisperProvider()
        self.provider.load_model()

    def process(
        self,
        audio_metadata: AudioMetadata,
        vad_segments: Optional[List[VADSegment]] = None,
    ) -> Tuple[List[TranscriptSegment], TranscriptionMetadata]:
        call_id = audio_metadata.call_id

        if not audio_metadata.processed_audio_path:
            raise ASRAudioInvalidError("Missing processed audio path in metadata")

        try:
            return self.provider.transcribe(audio_metadata, vad_segments)
        except Exception as e:
            logger.error(
                f"Transcription service failed for {call_id}: {e}",
                extra={
                    "call_id": call_id,
                    "pipeline_module": "transcription",
                    "status": "failed",
                    "error": str(e),
                },
            )
            raise
