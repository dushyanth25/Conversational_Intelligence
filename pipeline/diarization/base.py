import abc
from typing import List, Tuple

from models import AudioMetadata, DiarizationMetadata, DiarizationSegment


class SpeakerDiarizationProvider(abc.ABC):
    """Abstract base class for all Diarization providers."""

    @abc.abstractmethod
    def load_model(self) -> None:
        """Initialize and load the Diarization model."""
        pass

    @abc.abstractmethod
    def diarize(
        self,
        audio_metadata: AudioMetadata,
        min_speakers: int | None = None,
        max_speakers: int | None = None,
        num_speakers: int | None = None,
    ) -> Tuple[List[DiarizationSegment], DiarizationMetadata]:
        """Diarize audio and return segments and metadata."""
        pass
