from typing import Optional

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from storage.postgres.exceptions import DatabaseError, UniqueConstraintError
from storage.postgres.models import Call


class CallRepository:
    def __init__(self, session: Session):
        self.session = session
        
    def create(self, call_id: str, filename: Optional[str] = None, audio_path: Optional[str] = None, duration: Optional[float] = None, language: Optional[str] = None, speaker_count: Optional[int] = None, status: str = "PROCESSING") -> Call:
        call = Call(
            call_id=call_id,
            filename=filename,
            audio_path=audio_path,
            duration=duration,
            language=language,
            speaker_count=speaker_count,
            status=status
        )
        try:
            self.session.add(call)
            self.session.flush()
            return call
        except IntegrityError as e:
            self.session.rollback()
            raise UniqueConstraintError(f"Call with call_id {call_id} already exists") from e
        except Exception as e:
            self.session.rollback()
            raise DatabaseError(str(e)) from e
            
    def get_by_call_id(self, call_id: str) -> Optional[Call]:
        return self.session.query(Call).filter(Call.call_id == call_id).first()
