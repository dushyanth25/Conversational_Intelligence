from abc import ABC, abstractmethod
from typing import Optional

from .models import LLMResponse


class LLMClient(ABC):
    @abstractmethod
    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        timeout: Optional[float] = None,
        response_format: Optional[dict] = None,
    ) -> LLMResponse:
        pass
