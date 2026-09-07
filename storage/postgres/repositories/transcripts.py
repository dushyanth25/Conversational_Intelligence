from typing import List

from sqlalchemy.orm import Session

from storage.postgres.exceptions import DatabaseError
from storage.postgres.models import TranscriptSegment


class TranscriptRepository:
    def __init__(self, session: Session):
        self.session = session
        
    def add_segments(self, call_id: str, segments: List[dict]) -> List[TranscriptSegment]:
        db_segments = []
        for seg in segments:
            db_segments.append(TranscriptSegment(
                call_id=call_id,
                start_time=seg["start_time"],
                end_time=seg["end_time"],
                speaker_id=seg["speaker_id"],
                speaker_role=seg.get("speaker_role"),
                text=seg["text"],
                confidence=seg.get("confidence")
            ))
        try:
            self.session.add_all(db_segments)
            self.session.flush()
            return db_segments
        except Exception as e:
            self.session.rollback()
            raise DatabaseError(str(e)) from e

    def get_by_call_id(self, call_id: str) -> List[TranscriptSegment]:
        return self.session.query(TranscriptSegment).filter(TranscriptSegment.call_id == call_id).order_by(TranscriptSegment.start_time).all()
