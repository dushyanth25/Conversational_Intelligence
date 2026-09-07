from pydantic import BaseModel, Field, model_validator


class DiarizationSegment(BaseModel):
    start: float = Field(ge=0.0)
    end: float
    speaker: str = Field(..., min_length=1)

    @model_validator(mode="after")
    def check_timestamps(self) -> "DiarizationSegment":
        if self.end <= self.start:
            raise ValueError("end must be strictly greater than start")
        return self


class DiarizationMetadata(BaseModel):
    """Metadata about the diarization process."""
    call_id: str = Field(..., min_length=1)
    speaker_count: int = Field(..., ge=0)
    duration: float = Field(..., ge=0.0)
    model_name: str = Field(..., min_length=1)
    device: str = Field(..., min_length=1)
    processing_duration: float = Field(..., ge=0.0)
