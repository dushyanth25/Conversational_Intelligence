import logging
from typing import Optional

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from storage.postgres.models import BatchRun, Call, WorkflowRun

from .exceptions import (
    ConcurrentUpdateError,
    EntityNotFoundError,
)
from .models import BatchState, CallState, WorkflowState
from .transitions import (
    validate_batch_transition,
    validate_call_transition,
    validate_workflow_transition,
)

logger = logging.getLogger(__name__)

class ProcessingStateService:
    def __init__(self, session: Session):
        self.session = session
        
    def get_call_state(self, call_id: str) -> Optional[CallState]:
        call = self.session.query(Call).filter(Call.call_id == call_id).first()
        if not call:
            return None
        return CallState(call.status)
        
    def set_call_state(self, call_id: str, new_state: CallState) -> CallState:
        call = self.session.query(Call).filter(Call.call_id == call_id).first()
        if not call:
            raise EntityNotFoundError(f"Call {call_id} not found")
        call.status = new_state.value
        try:
            self.session.flush()
            return new_state
        except Exception as e:
            self.session.rollback()
            raise ConcurrentUpdateError(str(e)) from e
        
    def transition_call_state(self, call_id: str, new_state: CallState, force_reprocess: bool = False) -> CallState:
        call = self.session.query(Call).filter(Call.call_id == call_id).with_for_update().first()
        if not call:
            raise EntityNotFoundError(f"Call {call_id} not found")
            
        current_state = CallState(call.status)
        validate_call_transition(current_state, new_state, force_reprocess)
        
        call.status = new_state.value
        logger.info(f"Transitioned Call {call_id} from {current_state.value} to {new_state.value}")
        
        try:
            self.session.flush()
            return new_state
        except Exception as e:
            self.session.rollback()
            raise ConcurrentUpdateError(f"Failed to update call state for {call_id}: {e}") from e

    def get_batch_state(self, call_id: str, batch_id: str) -> Optional[BatchState]:
        run = self.session.query(BatchRun).filter(BatchRun.call_id == call_id, BatchRun.batch_id == batch_id).first()
        if not run:
            return None
        return BatchState(run.status)

    def transition_batch_state(self, call_id: str, batch_id: str, new_state: BatchState, force_reprocess: bool = False) -> BatchState:
        run = self.session.query(BatchRun).filter(BatchRun.call_id == call_id, BatchRun.batch_id == batch_id).with_for_update().first()
        if not run:
            run = BatchRun(call_id=call_id, batch_id=batch_id, status=new_state.value)
            try:
                self.session.add(run)
                self.session.flush()
                return new_state
            except IntegrityError as e:
                self.session.rollback()
                raise ConcurrentUpdateError(f"Failed to create batch {batch_id} for call {call_id}") from e
        
        current_state = BatchState(run.status)
        validate_batch_transition(current_state, new_state, force_reprocess)
        
        run.status = new_state.value
        logger.info(f"Transitioned Batch {batch_id} (Call {call_id}) from {current_state.value} to {new_state.value}")
        
        try:
            self.session.flush()
            return new_state
        except Exception as e:
            self.session.rollback()
            raise ConcurrentUpdateError(f"Failed to update batch state: {e}") from e

    def get_workflow_state(self, workflow_id: str) -> Optional[WorkflowState]:
        run = self.session.query(WorkflowRun).filter(WorkflowRun.workflow_id == workflow_id).first()
        if not run:
            return None
        return WorkflowState(run.status)

    def transition_workflow_state(self, workflow_id: str, new_state: WorkflowState, error_type: Optional[str] = None, error_message: Optional[str] = None, force_reprocess: bool = False) -> WorkflowState:
        run = self.session.query(WorkflowRun).filter(WorkflowRun.workflow_id == workflow_id).with_for_update().first()
        if not run:
            raise EntityNotFoundError(f"Workflow {workflow_id} not found")
            
        current_state = WorkflowState(run.status)
        validate_workflow_transition(current_state, new_state, force_reprocess)
        
        run.status = new_state.value
        if error_type:
            run.error_type = error_type
        if error_message:
            run.error_message = error_message
            
        logger.info(f"Transitioned Workflow {workflow_id} from {current_state.value} to {new_state.value}")
        
        try:
            self.session.flush()
            return new_state
        except Exception as e:
            self.session.rollback()
            raise ConcurrentUpdateError(f"Failed to update workflow state: {e}") from e
