import logging
import time
from typing import Optional

import groq
from groq import Groq

from config.settings import get_settings

from .base import LLMClient
from .exceptions import (
    LLMAuthenticationError,
    LLMConnectionError,
    LLMError,
    LLMRateLimitError,
    LLMRequestError,
    LLMResponseError,
    LLMTimeoutError,
)
from .models import LLMResponse, TokenUsage

logger = logging.getLogger(__name__)


class GroqClient(LLMClient):
    def __init__(self):
        settings = get_settings()
        
        api_keys_str = (
            settings.GROQ_API_KEY.get_secret_value() 
            if settings.GROQ_API_KEY else ""
        )
        self.api_keys = [k.strip() for k in api_keys_str.split(',')] if api_keys_str else []
        if not self.api_keys:
            raise LLMAuthenticationError("GROQ_API_KEY is missing from configuration")
        
        self.current_key_idx = 0
        self._init_client()
        
        self.default_model = settings.GROQ_MODEL
        self.default_temperature = settings.GROQ_TEMPERATURE
        self.default_max_tokens = settings.GROQ_MAX_TOKENS
        
        self.max_retries = settings.GROQ_MAX_RETRIES
        self.retry_backoff = settings.GROQ_RETRY_BACKOFF

    def _init_client(self):
        settings = get_settings()
        self.client = Groq(
            api_key=self.api_keys[self.current_key_idx],
            timeout=settings.GROQ_TIMEOUT,
            max_retries=0, # We handle retries ourselves manually
        )

    def rotate_key(self):
        self.current_key_idx = (self.current_key_idx + 1) % len(self.api_keys)
        logger.info(f"Rotating to API key index {self.current_key_idx}")
        self._init_client()

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
        
        req_model = model or self.default_model
        req_temp = temperature if temperature is not None else self.default_temperature
        req_max_tokens = (
            max_tokens if max_tokens is not None else self.default_max_tokens
        )
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        
        for attempt in range(self.max_retries + 1):
            try:
                response = self.client.chat.completions.create(
                    model=req_model,
                    messages=messages,
                    temperature=req_temp,
                    max_tokens=req_max_tokens,
                    timeout=timeout,
                    response_format=response_format,
                )
                
                if not response.choices:
                    raise LLMResponseError("Groq API returned no choices")
                
                choice = response.choices[0]
                
                usage = None
                if response.usage:
                    usage = TokenUsage(
                        input_tokens=response.usage.prompt_tokens,
                        output_tokens=response.usage.completion_tokens,
                        total_tokens=response.usage.total_tokens,
                    )
                
                return LLMResponse(
                    content=choice.message.content or "",
                    model=response.model,
                    usage=usage,
                    finish_reason=choice.finish_reason,
                )
                
            except groq.AuthenticationError as e:
                # Non-retryable
                logger.error("Authentication error with Groq API")
                raise LLMAuthenticationError(str(e)) from e
                
            except groq.BadRequestError as e:
                # Non-retryable
                logger.error("Bad request to Groq API")
                raise LLMRequestError(str(e)) from e
                
            except groq.RateLimitError as e:
                # Retryable
                if len(self.api_keys) > 1:
                    logger.warning("Rate limit hit, rotating API key.")
                    self.rotate_key()
                    continue
                
                if attempt == self.max_retries:
                    raise LLMRateLimitError(str(e)) from e
                self._backoff(attempt, e)
                
            except groq.APITimeoutError as e:
                # Retryable
                if attempt == self.max_retries:
                    raise LLMTimeoutError(str(e)) from e
                self._backoff(attempt, e)
                
            except groq.APIConnectionError as e:
                # Retryable
                if attempt == self.max_retries:
                    raise LLMConnectionError(str(e)) from e
                self._backoff(attempt, e)
                
            except groq.APIStatusError as e:
                # Usually retryable (e.g., 500, 502, 503)
                if e.status_code and 500 <= e.status_code < 600:
                    if attempt == self.max_retries:
                        raise LLMRequestError(f"Server error: {e.status_code}") from e
                    self._backoff(attempt, e)
                else:
                    # Non-retryable status error
                    raise LLMRequestError(str(e)) from e
                    
            except Exception as e:
                # Catch-all
                logger.error(f"Unexpected error calling Groq API: {type(e).__name__}")
                raise LLMError(f"Unexpected error: {e}") from e

    def _backoff(self, attempt: int, error: Exception):
        sleep_time = self.retry_backoff * (2 ** attempt)
        logger.warning(
            f"Groq API error ({type(error).__name__}). Retrying in {sleep_time}s... "
            f"(Attempt {attempt + 1}/{self.max_retries})"
        )
        time.sleep(sleep_time)
