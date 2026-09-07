import logging
from typing import Any, Dict, List, Optional

from models import AlignedSegment, Conversation, SpeakerRole, SpeakerRoleMapping

from .csv_writer import CSVWriter
from .exceptions import TranscriptValidationError
from .serializer import JSONSerializer

logger = logging.getLogger(__name__)


class TranscriptService:
    def __init__(self):
        self.csv_writer = CSVWriter()
        self.json_serializer = JSONSerializer()

    def process(
        self,
        call_id: str,
        segments: List[AlignedSegment],
        role_mappings: List[SpeakerRoleMapping],
        csv_output_path: str,
        json_output_path: str,
        language: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Conversation:
        logger.info(
            f"Generating canonical transcript for {call_id}",
            extra={"call_id": call_id, "pipeline_module": "transcript"},
        )

        if not call_id:
            raise TranscriptValidationError("call_id cannot be empty")

        # Map speakers to roles
        role_map = {m.speaker: m.role for m in role_mappings}

        for i, segment in enumerate(segments):
            if not segment.speaker:
                raise TranscriptValidationError(f"Segment {i} missing speaker")
            if not segment.text.strip():
                raise TranscriptValidationError(f"Segment {i} missing text")
            if segment.start >= segment.end:
                raise TranscriptValidationError(
                    f"Segment {i} invalid timestamps: start >= end"
                )
            
            # Ordering check
            if i > 0 and segment.start < segments[i - 1].start:
                raise TranscriptValidationError(
                    "Segments are not chronologically ordered"
                )

            # Assign role
            segment.speaker_role = role_map.get(segment.speaker, SpeakerRole.UNKNOWN)

        unique_speakers = {s.speaker for s in segments if s.speaker != "UNKNOWN"}

        conversation = Conversation(
            call_id=call_id,
            language=language,
            speaker_count=len(unique_speakers),
            segments=segments,
            metadata=metadata or {},
        )

        # Write artifacts
        self.csv_writer.write(conversation, csv_output_path)
        self.json_serializer.write(conversation, json_output_path)

        return conversation
