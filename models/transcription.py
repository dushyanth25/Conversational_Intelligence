from typing import List, Optional

from pydantic import BaseModel, Field, model_validator


class TranscriptionWord(BaseModel):
    """Word-level timestamp representation."""
    start: float = Field(..., ge=0.0)
    end: float = Field(..., ge=0.0)
    word: str = Field(..., min_length=1)
    probability: float = Field(..., ge=0.0, le=1.0)

    @model_validator(mode="after")
    def check_timestamps(self) -> "TranscriptionWord":
        if self.end <= self.start:
            raise ValueError("end must be strictly greater than start")
        return self


class TranscriptSegment(BaseModel):
    """A segment of transcribed audio."""
    start: float = Field(..., ge=0.0)
    end: float = Field(..., ge=0.0)
    text: str = Field(..., min_length=1)
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    language: Optional[str] = None
    words: Optional[List[TranscriptionWord]] = None

    @model_validator(mode="after")
    def check_timestamps(self) -> "TranscriptSegment":
        if self.end <= self.start:
            raise ValueError("end must be strictly greater than start")
        return self


class TranscriptionMetadata(BaseModel):
    """Metadata about the transcription process."""
    call_id: str = Field(..., min_length=1)
    detected_language: Optional[str] = None
    language_probability: Optional[float] = Field(None, ge=0.0, le=1.0)
    duration: Optional[float] = Field(None, ge=0.0)
    segment_count: int = Field(..., ge=0)
    model_name: str = Field(..., min_length=1)
    device: str = Field(..., min_length=1)
    processing_duration: float = Field(..., ge=0.0)
