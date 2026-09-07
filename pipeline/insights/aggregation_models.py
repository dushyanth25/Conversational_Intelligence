from typing import List

from pydantic import BaseModel, Field

from models.insights import InsightResult


class FailedBatchInfo(BaseModel):
    batch_id: str
    error_type: str

class FinalInsightResult(BaseModel):
    call_id: str
    status: str = Field(..., description="COMPLETE, PARTIAL, or FAILED")
    total_parameters: int
    successful_batches: List[str] = Field(default_factory=list)
    failed_batches: List[FailedBatchInfo] = Field(default_factory=list)
    missing_batches: List[str] = Field(default_factory=list)
    insights: List[InsightResult] = Field(default_factory=list)
    created_at: str
