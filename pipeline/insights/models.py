from typing import List

from pydantic import BaseModel, Field


class InsightPrompt(BaseModel):
    parameter: str = Field(..., min_length=1)
    prompt: str = Field(..., min_length=1)

class InsightPromptSet(BaseModel):
    prompts: List[InsightPrompt]
    count: int = Field(ge=0)
    source_file: str = Field(..., min_length=1)
