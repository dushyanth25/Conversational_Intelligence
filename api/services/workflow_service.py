import logging
import uuid
from typing import Any, Dict, Optional

from pipeline.state import CallState, ProcessingStateService, WorkflowState
from storage.postgres.database import get_db_session
from storage.postgres.models import Call, WorkflowRun

from ..clients.argo_client import ArgoClientError, ArgoWorkflowClient
from ..schemas.processing import ProcessRequest

logger = logging.getLogger(__name__)

class WorkflowService:
    def __init__(self):
        self.argo_client = ArgoWorkflowClient()
        
    async def submit_job(self, request: ProcessRequest) -> Dict[str, Any]:
        call_id = request.call_id or f"CALL_{uuid.uuid4().hex[:8]}"
        
        with get_db_session() as session:
            state_service = ProcessingStateService(session)
            
            existing_call = state_service.get_call_state(call_id)
            if existing_call:
                logger.warning(f"Call {call_id} already exists")
                raise ValueError("Duplicate call ID")
                
            call = Call(
                call_id=call_id,
                audio_path=request.audio_path,
                language=request.language,
                status=CallState.RECEIVED.value
            )
            session.add(call)
            session.flush()
            
            try:
                workflow_id = await self.argo_client.submit_workflow({
                    "call_id": call_id,
                    "audio_path": request.audio_path,
                    "prompt_sheet": request.prompt_sheet,
                    "parallel_workers": request.parallel_workers,
                    "parameters_per_batch": request.parameters_per_batch,
                    "enable_vad": request.enable_vad,
                    "enable_speaker_tagging": request.enable_speaker_tagging
                })
            except ArgoClientError as e:
                session.rollback()
                logger.error(f"Failed to submit workflow to Argo: {e}")
                raise RuntimeError("Argo unavailable") from e
                
            run = WorkflowRun(
                workflow_id=workflow_id,
                call_id=call_id,
                status=WorkflowState.SUBMITTED.value
            )
            session.add(run)
            session.commit()
            
            logger.info(f"Registered job for call {call_id} with workflow {workflow_id}")
            return {
                "workflow_id": workflow_id,
                "call_id": call_id,
                "status": WorkflowState.SUBMITTED.value
            }

    def get_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        with get_db_session() as session:
            run = session.query(WorkflowRun).filter(WorkflowRun.workflow_id == workflow_id).first()
            if not run:
                return None
                
            return {
                "workflow_id": run.workflow_id,
                "call_id": run.call_id,
                "status": run.status,
                "started_at": run.started_at.isoformat() if run.started_at else None,
                "updated_at": run.updated_at.isoformat() if run.updated_at else None
            }

    def get_result(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        with get_db_session() as session:
            run = session.query(WorkflowRun).filter(WorkflowRun.workflow_id == workflow_id).first()
            if not run:
                return None
                
            if run.status != WorkflowState.SUCCEEDED.value:
                return {
                    "workflow_id": run.workflow_id,
                    "call_id": run.call_id,
                    "status": run.status
                }
                
            return {
                "workflow_id": run.workflow_id,
                "call_id": run.call_id,
                "status": "COMPLETED",
                "diarized_transcript": f"minio://conversation-intelligence/diarized/{run.call_id}.csv",
                "final_insights": f"minio://conversation-intelligence/insights/{run.call_id}.json"
            }
