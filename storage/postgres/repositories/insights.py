from typing import Any, List, Optional

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from storage.postgres.exceptions import DatabaseError, UniqueConstraintError
from storage.postgres.models import Insight, InsightEvidence


class InsightRepository:
    def __init__(self, session: Session):
        self.session = session
        
    def add_insight(self, call_id: str, parameter: str, result: Any, confidence: Optional[float] = None, evidence: Optional[List[dict]] = None) -> Insight:
        insight = Insight(
            call_id=call_id,
            parameter=parameter,
            result=result,
            confidence=confidence
        )
        try:
            self.session.add(insight)
            self.session.flush()
            
            if evidence:
                db_evidence = []
                for ev in evidence:
                    db_evidence.append(InsightEvidence(
                        insight_id=insight.id,
                        timestamp=ev.get("timestamp"),
                        speaker=ev.get("speaker"),
                        text=ev.get("text"),
                        segment_id=ev.get("segment_id")
                    ))
                self.session.add_all(db_evidence)
                self.session.flush()
                
            return insight
        except IntegrityError as e:
            self.session.rollback()
            raise UniqueConstraintError(f"Insight for {call_id} and {parameter} already exists") from e
        except Exception as e:
            self.session.rollback()
            raise DatabaseError(str(e)) from e
            
    def get_by_call_id(self, call_id: str) -> List[Insight]:
        return self.session.query(Insight).filter(Insight.call_id == call_id).all()
