import abc
from typing import List

from models import AlignedSegment, SpeakerRoleMapping


class SpeakerRoleClassifier(abc.ABC):
    """Abstract base class for all Speaker Role classifiers."""

    @abc.abstractmethod
    def classify(self, segments: List[AlignedSegment]) -> List[SpeakerRoleMapping]:
        """Classify speakers in the conversation and return role mappings."""
        pass
