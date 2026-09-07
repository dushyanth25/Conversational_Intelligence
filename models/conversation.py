from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, model_validator

from .transcription import TranscriptionWord


class SpeakerRole(str, Enum):
    AGENT = "AGENT"
    CUSTOMER = "CUSTOMER"
    UNKNOWN = "UNKNOWN"


class SpeakerRoleMapping(BaseModel):
    speaker: str = Field(..., min_length=1)
    role: SpeakerRole
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)


class AlignedSegment(BaseModel):
    start: float = Field(ge=0.0)
    end: float
    speaker: str = Field(..., min_length=1)
    speaker_role: SpeakerRole = SpeakerRole.UNKNOWN
    text: str = Field(..., min_length=1)
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    language: Optional[str] = None
    words: Optional[List[TranscriptionWord]] = None

    @model_validator(mode="after")
    def check_timestamps(self) -> "AlignedSegment":
        if self.end <= self.start:
            raise ValueError("end must be strictly greater than start")
        return self


class Conversation(BaseModel):
    call_id: str = Field(..., min_length=1)
    language: Optional[str] = None
    speaker_count: int = Field(ge=0)
    segments: List[AlignedSegment] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
