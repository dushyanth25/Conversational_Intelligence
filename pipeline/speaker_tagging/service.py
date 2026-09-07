import logging
from typing import List, Optional

from models import AlignedSegment, SpeakerRoleMapping

from .base import SpeakerRoleClassifier
from .rule_based import RuleBasedRoleClassifier

logger = logging.getLogger(__name__)


class SpeakerTaggingService:
    def __init__(self, classifier: Optional[SpeakerRoleClassifier] = None):
        self.classifier = classifier or RuleBasedRoleClassifier()

    def process(
        self, call_id: str, segments: List[AlignedSegment]
    ) -> List[SpeakerRoleMapping]:
        logger.info(
            f"Starting speaker role identification for {call_id}",
            extra={
                "call_id": call_id,
                "pipeline_module": "speaker_tagging",
                "segments_count": len(segments),
            },
        )

        try:
            mappings = self.classifier.classify(segments)
            
            # Log the roles found
            role_counts = {"AGENT": 0, "CUSTOMER": 0, "UNKNOWN": 0}
            for m in mappings:
                role_counts[m.role.value] += 1

            logger.info(
                f"Speaker tagging completed for {call_id}",
                extra={
                    "call_id": call_id,
                    "pipeline_module": "speaker_tagging",
                    "roles_found": role_counts,
                    "status": "completed",
                },
            )

            return mappings
        except Exception as e:
            logger.error(
                f"Speaker tagging failed for {call_id}: {e}",
                extra={
                    "call_id": call_id,
                    "pipeline_module": "speaker_tagging",
                    "status": "failed",
                    "error": str(e),
                },
            )
            raise
