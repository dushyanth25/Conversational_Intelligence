from datetime import datetime
from typing import Optional

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from storage.postgres.exceptions import DatabaseError, UniqueConstraintError
from storage.postgres.models import WorkflowRun


class WorkflowRepository:
    def __init__(self, session: Session):
        self.session = session
        
    def create(self, workflow_id: str, call_id: str, status: str = "PENDING") -> WorkflowRun:
        run = WorkflowRun(
            workflow_id=workflow_id,
            call_id=call_id,
            status=status
        )
        try:
            self.session.add(run)
            self.session.flush()
            return run
        except IntegrityError as e:
            self.session.rollback()
            raise UniqueConstraintError(f"Workflow {workflow_id} already exists") from e
        except Exception as e:
            self.session.rollback()
            raise DatabaseError(str(e)) from e
            
    def update_status(self, workflow_id: str, status: str, error_type: Optional[str] = None, error_message: Optional[str] = None) -> Optional[WorkflowRun]:
        try:
            run = self.session.query(WorkflowRun).filter(WorkflowRun.workflow_id == workflow_id).first()
            if not run:
                return None
            run.status = status
            if error_type:
                run.error_type = error_type
            if error_message:
                run.error_message = error_message
            if status in ("COMPLETED", "FAILED"):
                run.completed_at = datetime.utcnow()
            self.session.flush()
            return run
        except Exception as e:
            self.session.rollback()
            raise DatabaseError(str(e)) from e
