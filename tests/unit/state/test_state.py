from unittest.mock import MagicMock

import pytest
from sqlalchemy.orm import Session

from pipeline.state import (
    BatchState,
    CallState,
    EntityNotFoundError,
    IdempotencyManager,
    InvalidStateTransition,
    ProcessingStateService,
    WorkflowState,
)
from storage.postgres.models import BatchRun, Call


@pytest.fixture
def mock_session():
    return MagicMock(spec=Session)

def test_valid_call_transition(mock_session):
    mock_session.query().filter().with_for_update().first.return_value = Call(status=CallState.RECEIVED.value)
    service = ProcessingStateService(mock_session)
    new_state = service.transition_call_state("C1", CallState.PREPROCESSING)
    assert new_state == CallState.PREPROCESSING
    mock_session.flush.assert_called_once()

def test_invalid_call_transition(mock_session):
    mock_session.query().filter().with_for_update().first.return_value = Call(status=CallState.COMPLETED.value)
    service = ProcessingStateService(mock_session)
    with pytest.raises(InvalidStateTransition):
        service.transition_call_state("C1", CallState.PREPROCESSING)

def test_force_reprocess_transition(mock_session):
    mock_session.query().filter().with_for_update().first.return_value = Call(status=CallState.COMPLETED.value)
    service = ProcessingStateService(mock_session)
    new_state = service.transition_call_state("C1", CallState.PREPROCESSING, force_reprocess=True)
    assert new_state == CallState.PREPROCESSING

def test_batch_creation(mock_session):
    mock_session.query().filter().with_for_update().first.return_value = None
    service = ProcessingStateService(mock_session)
    new_state = service.transition_batch_state("C1", "B1", BatchState.PROCESSING)
    assert new_state == BatchState.PROCESSING
    mock_session.add.assert_called_once()

def test_batch_retry_eligibility(mock_session):
    mock_session.query().filter().with_for_update().first.return_value = BatchRun(status=BatchState.FAILED.value)
    service = ProcessingStateService(mock_session)
    new_state = service.transition_batch_state("C1", "B1", BatchState.PROCESSING)
    assert new_state == BatchState.PROCESSING

def test_workflow_missing(mock_session):
    mock_session.query().filter().with_for_update().first.return_value = None
    service = ProcessingStateService(mock_session)
    with pytest.raises(EntityNotFoundError):
        service.transition_workflow_state("W1", WorkflowState.RUNNING)

def test_idempotency_should_skip(mock_session):
    mock_session.query().filter().first.return_value = BatchRun(status=BatchState.VALIDATED.value)
    manager = IdempotencyManager(mock_session)
    assert manager.should_process_batch("C1", "B1") is False

def test_idempotency_should_process_if_failed(mock_session):
    mock_session.query().filter().first.return_value = BatchRun(status=BatchState.FAILED.value)
    manager = IdempotencyManager(mock_session)
    assert manager.should_process_batch("C1", "B1") is True

def test_idempotency_force_reprocess(mock_session):
    mock_session.query().filter().first.return_value = BatchRun(status=BatchState.VALIDATED.value)
    manager = IdempotencyManager(mock_session)
    assert manager.should_process_batch("C1", "B1", force_reprocess=True) is True
