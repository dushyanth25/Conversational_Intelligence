from pydantic import BaseModel, Field, model_validator


class VADSegment(BaseModel):
    start: float = Field(ge=0.0)
    end: float
    is_speech: bool

    @model_validator(mode="after")
    def check_timestamps(self) -> "VADSegment":
        if self.end <= self.start:
            raise ValueError("end must be strictly greater than start")
        return self
