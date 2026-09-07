from unittest.mock import MagicMock

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from storage.postgres.exceptions import DatabaseError, UniqueConstraintError
from storage.postgres.models import (
    TranscriptSegment,
    WorkflowRun,
)
from storage.postgres.repositories.calls import CallRepository
from storage.postgres.repositories.insights import InsightRepository
from storage.postgres.repositories.transcripts import TranscriptRepository
from storage.postgres.repositories.workflows import WorkflowRepository


@pytest.fixture
def mock_session():
    session = MagicMock(spec=Session)
    return session

def test_create_call(mock_session):
    repo = CallRepository(mock_session)
    call = repo.create("CALL_1", "test.wav")
    assert call.call_id == "CALL_1"
    assert call.filename == "test.wav"
    mock_session.add.assert_called_once()
    mock_session.flush.assert_called_once()

def test_duplicate_call(mock_session):
    repo = CallRepository(mock_session)
    mock_session.flush.side_effect = IntegrityError(None, None, Exception())
    with pytest.raises(UniqueConstraintError):
        repo.create("CALL_1")
    mock_session.rollback.assert_called_once()

def test_store_transcript(mock_session):
    repo = TranscriptRepository(mock_session)
    segments = [
        {"start_time": 0.0, "end_time": 1.0, "speaker_id": "SPK1", "speaker_role": "AGENT", "text": "hello"}
    ]
    db_segs = repo.add_segments("CALL_1", segments)
    assert len(db_segs) == 1
    assert db_segs[0].speaker_id == "SPK1"
    mock_session.add_all.assert_called_once()
    mock_session.flush.assert_called_once()

def test_store_transcript_error(mock_session):
    repo = TranscriptRepository(mock_session)
    mock_session.flush.side_effect = Exception("failed")
    with pytest.raises(DatabaseError):
        repo.add_segments("CALL_1", [{"start_time": 0.0, "end_time": 1.0, "speaker_id": "SPK1", "speaker_role": "AGENT", "text": "hello"}])
    mock_session.rollback.assert_called_once()

def test_retrieve_transcript(mock_session):
    repo = TranscriptRepository(mock_session)
    mock_query = mock_session.query.return_value.filter.return_value.order_by.return_value
    mock_query.all.return_value = [TranscriptSegment(call_id="CALL_1")]
    segs = repo.get_by_call_id("CALL_1")
    assert len(segs) == 1

def test_store_insight(mock_session):
    repo = InsightRepository(mock_session)
    insight = repo.add_insight("CALL_1", "sentiment", {"score": 0.9})
    assert insight.call_id == "CALL_1"
    assert insight.parameter == "sentiment"
    assert insight.result == {"score": 0.9}
    mock_session.add.assert_called_once()

def test_duplicate_insight(mock_session):
    repo = InsightRepository(mock_session)
    mock_session.flush.side_effect = IntegrityError(None, None, Exception())
    with pytest.raises(UniqueConstraintError):
        repo.add_insight("CALL_1", "sentiment", {})
    mock_session.rollback.assert_called_once()

def test_store_evidence(mock_session):
    repo = InsightRepository(mock_session)
    repo.add_insight("CALL_1", "sentiment", {}, evidence=[{"text": "hello", "speaker": "SPK1"}])
    mock_session.add_all.assert_called_once()

def test_create_workflow(mock_session):
    repo = WorkflowRepository(mock_session)
    run = repo.create("WF_1", "CALL_1")
    assert run.workflow_id == "WF_1"
    assert run.status == "PENDING"

def test_update_workflow(mock_session):
    repo = WorkflowRepository(mock_session)
    mock_run = WorkflowRun(workflow_id="WF_1", status="PENDING")
    mock_session.query.return_value.filter.return_value.first.return_value = mock_run
    
    updated = repo.update_status("WF_1", "COMPLETED")
    assert updated.status == "COMPLETED"
    assert updated.completed_at is not None
    mock_session.flush.assert_called_once()
