from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)

@pytest.fixture
def mock_db_session():
    with patch("api.services.workflow_service.get_db_session") as mock_session:
        session_instance = MagicMock()
        mock_session.return_value.__enter__.return_value = session_instance
        yield session_instance

def test_health():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok", "message": "Application process is alive"}

def test_ready():
    with patch("api.routes.health.engine.connect"):
        res = client.get("/ready")
        assert res.status_code == 200
        assert res.json() == {"status": "ready"}

def test_process_valid(mock_db_session):
    with patch("api.clients.argo_client.ArgoWorkflowClient.submit_workflow", new_callable=AsyncMock) as mock_submit:
        mock_submit.return_value = "wf-123"
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        req = {
            "audio_path": "s3://bucket/audio.wav",
            "prompt_sheet": "s3://bucket/prompt.csv",
            "parallel_workers": 2
        }
        res = client.post("/process", json=req)
        assert res.status_code == 202
        data = res.json()
        assert data["workflow_id"] == "wf-123"
        assert data["status"] == "SUBMITTED"

def test_process_invalid_path():
    req = {
        "audio_path": "",
        "prompt_sheet": "s3://bucket/prompt.csv",
        "parallel_workers": 2
    }
    res = client.post("/process", json=req)
    assert res.status_code == 422

def test_process_invalid_worker():
    req = {
        "audio_path": "s3://bucket/audio.wav",
        "prompt_sheet": "s3://bucket/prompt.csv",
        "parallel_workers": 0
    }
    res = client.post("/process", json=req)
    assert res.status_code == 422

def test_process_duplicate_call(mock_db_session):
    mock_db_session.query.return_value.filter.return_value.first.return_value = MagicMock()
    req = {
        "audio_path": "s3://bucket/audio.wav",
        "prompt_sheet": "s3://bucket/prompt.csv",
        "call_id": "CALL_DUP"
    }
    with patch("api.services.workflow_service.ProcessingStateService.get_call_state") as mock_state:
        mock_state.return_value = "RECEIVED"
        res = client.post("/process", json=req)
        assert res.status_code == 400
        assert "Duplicate" in res.json()["detail"]

def test_process_argo_failure(mock_db_session):
    from api.clients.argo_client import ArgoClientError
    with patch("api.clients.argo_client.ArgoWorkflowClient.submit_workflow", new_callable=AsyncMock) as mock_submit:
        mock_submit.side_effect = ArgoClientError("failed")
        with patch("api.services.workflow_service.ProcessingStateService.get_call_state") as mock_state:
            mock_state.return_value = None
            req = {
                "audio_path": "s3://bucket/audio.wav",
                "prompt_sheet": "s3://bucket/prompt.csv",
            }
            res = client.post("/process", json=req)
            assert res.status_code == 503

def test_get_status(mock_db_session):
    mock_run = MagicMock()
    mock_run.workflow_id = "wf-123"
    mock_run.call_id = "CALL_1"
    mock_run.status = "RUNNING"
    mock_run.started_at.isoformat.return_value = "2026-08-10"
    mock_run.updated_at.isoformat.return_value = "2026-08-10"
    
    mock_db_session.query.return_value.filter.return_value.first.return_value = mock_run
    
    res = client.get("/process/wf-123")
    assert res.status_code == 200
    assert res.json()["status"] == "RUNNING"

def test_get_result_not_ready(mock_db_session):
    mock_run = MagicMock()
    mock_run.status = "RUNNING"
    mock_db_session.query.return_value.filter.return_value.first.return_value = mock_run
    
    res = client.get("/process/wf-123/result")
    assert res.status_code == 425

def test_get_result_ready(mock_db_session):
    mock_run = MagicMock()
    mock_run.workflow_id = "wf-123"
    mock_run.call_id = "CALL_1"
    mock_run.status = "SUCCEEDED"
    mock_db_session.query.return_value.filter.return_value.first.return_value = mock_run
    
    res = client.get("/process/wf-123/result")
    assert res.status_code == 200
    assert "diarized_transcript" in res.json()
