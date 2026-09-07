import abc
from typing import List, Optional, Tuple

from models import AudioMetadata, TranscriptionMetadata, TranscriptSegment, VADSegment


class ASRProvider(abc.ABC):
    """Abstract base class for all ASR providers."""

    @abc.abstractmethod
    def load_model(self) -> None:
        """Initialize and load the ASR model."""
        pass

    @abc.abstractmethod
    def transcribe(
        self,
        audio_metadata: AudioMetadata,
        vad_segments: Optional[List[VADSegment]] = None,
    ) -> Tuple[List[TranscriptSegment], TranscriptionMetadata]:
        """Transcribe audio and return segments and metadata."""
        pass
