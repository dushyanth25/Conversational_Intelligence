import logging
from typing import List

from models import AlignedSegment, DiarizationSegment, TranscriptSegment

from .algorithm import align_segments

logger = logging.getLogger(__name__)

class AlignmentService:
    def __init__(self, tolerance: float = 0.1):
        self.tolerance = tolerance

    def process(
        self,
        call_id: str,
        transcript_segments: List[TranscriptSegment],
        diarization_segments: List[DiarizationSegment],
    ) -> List[AlignedSegment]:
        
        logger.info(
            f"Starting timestamp alignment for {call_id}",
            extra={
                "call_id": call_id,
                "pipeline_module": "alignment",
                "transcript_segments_count": len(transcript_segments),
                "diarization_segments_count": len(diarization_segments),
            }
        )
        
        try:
            aligned = align_segments(
                transcript_segments, 
                diarization_segments, 
                tolerance=self.tolerance
            )
            
            logger.info(
                f"Alignment completed for {call_id}. Produced {len(aligned)} segments.",
                extra={
                    "call_id": call_id,
                    "pipeline_module": "alignment",
                    "aligned_segments_count": len(aligned),
                    "status": "completed"
                }
            )
            
            return aligned
            
        except Exception as e:
            logger.error(
                f"Alignment failed for {call_id}: {e}",
                extra={
                    "call_id": call_id,
                    "pipeline_module": "alignment",
                    "status": "failed",
                    "error": str(e)
                }
            )
            raise
