from sqlalchemy.orm import Session

from .models import BatchState
from .service import ProcessingStateService


class IdempotencyManager:
    def __init__(self, session: Session):
        self.session = session
        self.state_service = ProcessingStateService(session)

    def should_process_batch(self, call_id: str, batch_id: str, force_reprocess: bool = False) -> bool:
        """
        Check if a batch should be processed.
        Returns False if already VALIDATED (and not forcing reprocess), True otherwise.
        """
        if force_reprocess:
            return True
            
        state = self.state_service.get_batch_state(call_id, batch_id)
        if state == BatchState.VALIDATED:
            return False
        
        return True
