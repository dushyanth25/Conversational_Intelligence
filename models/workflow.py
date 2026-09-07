from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class WorkflowStatusEnum(str, Enum):
    SUBMITTED = "SUBMITTED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    PARTIAL_FAILURE = "PARTIAL_FAILURE"
    FAILED = "FAILED"


class WorkflowStatus(BaseModel):
    workflow_id: str = Field(..., min_length=1)
    call_id: str = Field(..., min_length=1)
    status: WorkflowStatusEnum
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None


class ProcessingJob(BaseModel):
    workflow_id: str = Field(..., min_length=1)
    call_id: str = Field(..., min_length=1)
    status: WorkflowStatusEnum
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
