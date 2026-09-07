from typing import List, Optional

from pydantic import BaseModel, Field


class InsightParameter(BaseModel):
    parameter: str = Field(..., min_length=1)
    prompt: str = Field(..., min_length=1)


class ParameterBatch(BaseModel):
    batch_id: str = Field(..., min_length=1)
    call_id: str = Field(..., min_length=1)
    parameters: List[InsightParameter]


class Evidence(BaseModel):
    timestamp: str = Field(..., min_length=1)
    speaker: str = Field(..., min_length=1)
    text: str = Field(..., min_length=1)


class InsightResult(BaseModel):
    parameter: str = Field(..., min_length=1)
    result: str = Field(...)
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    evidence: List[Evidence] = Field(default_factory=list)


class LLMRequest(BaseModel):
    call_id: str = Field(..., min_length=1)
    batch_id: str = Field(..., min_length=1)
    transcript: str = Field(...)
    parameters: List[InsightParameter]


class LLMResponse(BaseModel):
    results: List[InsightResult] = Field(...)
