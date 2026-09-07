import uuid
from typing import Optional

from pydantic import BaseModel, Field


class AudioInput(BaseModel):
    call_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    audio_path: str = Field(...)
    prompt_sheet: str = Field(...)
    parallel_workers: int = Field(default=1, gt=0)
    language: str = Field(default="auto")
    parameters_per_batch: int = Field(default=3, gt=0)
    enable_vad: bool = True
    enable_speaker_tagging: bool = True


class AudioMetadata(BaseModel):
    call_id: str
    filename: str
    original_format: str
    duration: float = Field(ge=0)
    sample_rate: int = Field(gt=0)
    channels: int = Field(gt=0)
    processed_audio_path: str

    file_size: Optional[int] = Field(default=None, ge=0)
    created_at: Optional[str] = None
    codec: Optional[str] = None
