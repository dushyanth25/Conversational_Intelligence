from .exceptions import InvalidStateTransition
from .models import BatchState, CallState, WorkflowState

CALL_TRANSITIONS = {
    CallState.RECEIVED: {CallState.PREPROCESSING, CallState.FAILED, CallState.COMPLETED},
    CallState.PREPROCESSING: {CallState.TRANSCRIBING, CallState.FAILED, CallState.COMPLETED},
    CallState.TRANSCRIBING: {CallState.DIARIZING, CallState.FAILED, CallState.COMPLETED},
    CallState.DIARIZING: {CallState.ALIGNING, CallState.FAILED, CallState.COMPLETED},
    CallState.ALIGNING: {CallState.TAGGING, CallState.FAILED, CallState.COMPLETED},
    CallState.TAGGING: {CallState.TRANSCRIPT_READY, CallState.FAILED, CallState.COMPLETED},
    CallState.TRANSCRIPT_READY: {CallState.INSIGHT_PROCESSING, CallState.COMPLETED, CallState.FAILED},
    CallState.INSIGHT_PROCESSING: {CallState.COMPLETED, CallState.PARTIAL, CallState.FAILED},
    CallState.COMPLETED: set(),
    CallState.PARTIAL: {CallState.COMPLETED, CallState.FAILED, CallState.INSIGHT_PROCESSING},
    CallState.FAILED: set(),
}

WORKFLOW_TRANSITIONS = {
    WorkflowState.SUBMITTED: {WorkflowState.RUNNING, WorkflowState.CANCELLED, WorkflowState.FAILED},
    WorkflowState.RUNNING: {WorkflowState.SUCCEEDED, WorkflowState.PARTIAL, WorkflowState.FAILED, WorkflowState.CANCELLED},
    WorkflowState.SUCCEEDED: set(),
    WorkflowState.PARTIAL: set(),
    WorkflowState.FAILED: set(),
    WorkflowState.CANCELLED: set(),
}

BATCH_TRANSITIONS = {
    BatchState.PENDING: {BatchState.PROCESSING, BatchState.FAILED},
    BatchState.PROCESSING: {BatchState.VALIDATED, BatchState.FAILED},
    BatchState.VALIDATED: set(),
    BatchState.FAILED: {BatchState.PROCESSING},  # Allow retrying failed batches
}

def validate_call_transition(current: CallState, target: CallState, force_reprocess: bool = False):
    if force_reprocess:
        return
    if target not in CALL_TRANSITIONS.get(current, set()):
        raise InvalidStateTransition(f"Cannot transition call from {current.value} to {target.value}")

def validate_workflow_transition(current: WorkflowState, target: WorkflowState, force_reprocess: bool = False):
    if force_reprocess:
        return
    if target not in WORKFLOW_TRANSITIONS.get(current, set()):
        raise InvalidStateTransition(f"Cannot transition workflow from {current.value} to {target.value}")

def validate_batch_transition(current: BatchState, target: BatchState, force_reprocess: bool = False):
    if force_reprocess:
        return
    if target not in BATCH_TRANSITIONS.get(current, set()):
        raise InvalidStateTransition(f"Cannot transition batch from {current.value} to {target.value}")
