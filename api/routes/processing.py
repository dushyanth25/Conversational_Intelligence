import logging

from fastapi import APIRouter, HTTPException, status

from ..schemas.processing import (
    ProcessRequest,
    ProcessResponse,
    ResultResponse,
    StatusResponse,
)
from ..services.workflow_service import WorkflowService

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/process", response_model=ProcessResponse, status_code=status.HTTP_202_ACCEPTED)
async def process_audio(request: ProcessRequest):
    service = WorkflowService()
    try:
        result = await service.submit_job(request)
        return ProcessResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error") from e

@router.get("/process/{workflow_id}", response_model=StatusResponse)
async def get_status(workflow_id: str):
    service = WorkflowService()
    result = service.get_status(workflow_id)
    if not result:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return StatusResponse(**result)

@router.get("/process/{workflow_id}/result", response_model=ResultResponse)
async def get_result(workflow_id: str):
    service = WorkflowService()
    result = service.get_result(workflow_id)
    if not result:
        raise HTTPException(status_code=404, detail="Workflow not found")
        
    if result["status"] not in ("SUCCEEDED", "COMPLETED"):
        raise HTTPException(status_code=425, detail="Result is not ready yet")
        
    return ResultResponse(**result)
