from typing import Optional

from pydantic import BaseModel, Field


class ProcessRequest(BaseModel):
    audio_path: str = Field(..., min_length=1)
    prompt_sheet: str = Field(..., min_length=1)
    parallel_workers: int = Field(default=1, ge=1)
    
    call_id: Optional[str] = None
    language: str = "auto"
    parameters_per_batch: int = Field(default=3, ge=1)
    enable_vad: bool = True
    enable_speaker_tagging: bool = True

class ProcessResponse(BaseModel):
    workflow_id: str
    call_id: str
    status: str

class StatusResponse(BaseModel):
    workflow_id: str
    call_id: str
    status: str
    started_at: Optional[str] = None
    updated_at: Optional[str] = None

class ResultResponse(BaseModel):
    workflow_id: str
    call_id: str
    status: str
    diarized_transcript: Optional[str] = None
    final_insights: Optional[str] = None
