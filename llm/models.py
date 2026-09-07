from typing import Optional

from pydantic import BaseModel, Field


class TokenUsage(BaseModel):
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    total_tokens: Optional[int] = None

class LLMResponse(BaseModel):
    content: str
    model: str
    usage: Optional[TokenUsage] = None
    finish_reason: Optional[str] = None

class PromptRequest(BaseModel):
    system_prompt: str = Field(...)
    user_prompt: str = Field(...)
    batch_id: str = Field(...)
    call_id: str = Field(...)
    model: str = Field(...)
