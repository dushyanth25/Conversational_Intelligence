from typing import List

from pydantic import BaseModel, Field

from .models import InsightPrompt


class InsightBatch(BaseModel):
    batch_id: str = Field(..., min_length=1)
    parameters: List[InsightPrompt]
