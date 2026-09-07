from typing import List, Optional

from pydantic import BaseModel, Field

from models.insights import InsightResult


class InsightBatchResult(BaseModel):
    batch_id: str = Field(..., min_length=1)
    call_id: str = Field(..., min_length=1)
    results: List[InsightResult]
    status: str = Field(default="validated")
    error_type: Optional[str] = None
