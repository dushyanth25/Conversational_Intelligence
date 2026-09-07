from unittest.mock import MagicMock, patch

import groq
import httpx
import pytest

from config.settings import Settings
from llm.exceptions import (
    LLMAuthenticationError,
    LLMRateLimitError,
    LLMRequestError,
)
from llm.groq_client import GroqClient


@pytest.fixture
def mock_settings():
    return Settings(
        GROQ_API_KEY="test_key", GROQ_MAX_RETRIES=2, GROQ_RETRY_BACKOFF=0.01
    )

def test_missing_api_key():
    with patch("llm.groq_client.get_settings") as mock_get:
        mock_get.return_value = Settings(GROQ_API_KEY=None)
        with pytest.raises(LLMAuthenticationError, match="missing"):
            GroqClient()

@patch("llm.groq_client.Groq")
@patch("llm.groq_client.get_settings")
def test_successful_request(mock_get, mock_groq_class, mock_settings):
    mock_get.return_value = mock_settings
    mock_client = MagicMock()
    mock_groq_class.return_value = mock_client
    
    mock_response = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = "Response text"
    mock_choice.finish_reason = "stop"
    mock_response.choices = [mock_choice]
    mock_response.model = "llama3"
    mock_response.usage.prompt_tokens = 10
    mock_response.usage.completion_tokens = 20
    mock_response.usage.total_tokens = 30
    
    mock_client.chat.completions.create.return_value = mock_response
    
    client = GroqClient()
    response = client.generate("system", "user")
    
    assert response.content == "Response text"
    assert response.model == "llama3"
    assert response.finish_reason == "stop"
    assert response.usage.input_tokens == 10
    assert response.usage.output_tokens == 20
    assert response.usage.total_tokens == 30
    
@patch("llm.groq_client.Groq")
@patch("llm.groq_client.get_settings")
def test_authentication_error(mock_get, mock_groq_class, mock_settings):
    mock_get.return_value = mock_settings
    mock_client = MagicMock()
    mock_groq_class.return_value = mock_client
    
    mock_client.chat.completions.create.side_effect = groq.AuthenticationError(
        message="Auth failed", response=MagicMock(), body=None
    )
    
    client = GroqClient()
    with pytest.raises(LLMAuthenticationError):
        client.generate("system", "user")

@patch("llm.groq_client.Groq")
@patch("llm.groq_client.get_settings")
def test_rate_limit_retry(mock_get, mock_groq_class, mock_settings):
    mock_get.return_value = mock_settings
    mock_client = MagicMock()
    mock_groq_class.return_value = mock_client
    
    mock_response = MagicMock()
    mock_response.choices[0].message.content = "Success"
    mock_response.choices[0].finish_reason = "stop"
    mock_response.model = "model"
    mock_response.usage = None
    
    mock_client.chat.completions.create.side_effect = [
        groq.RateLimitError(message="Rate limit", response=MagicMock(), body=None),
        groq.RateLimitError(message="Rate limit", response=MagicMock(), body=None),
        mock_response
    ]
    
    client = GroqClient()
    response = client.generate("system", "user")
    assert response.content == "Success"
    assert mock_client.chat.completions.create.call_count == 3

@patch("llm.groq_client.Groq")
@patch("llm.groq_client.get_settings")
def test_rate_limit_failure(mock_get, mock_groq_class, mock_settings):
    mock_get.return_value = mock_settings
    mock_client = MagicMock()
    mock_groq_class.return_value = mock_client
    
    mock_client.chat.completions.create.side_effect = groq.RateLimitError(
        message="Rate limit", response=MagicMock(), body=None
    )
    
    client = GroqClient()
    with pytest.raises(LLMRateLimitError):
        client.generate("system", "user")

@patch("llm.groq_client.Groq")
@patch("llm.groq_client.get_settings")
def test_server_error_retry(mock_get, mock_groq_class, mock_settings):
    mock_get.return_value = mock_settings
    mock_client = MagicMock()
    mock_groq_class.return_value = mock_client
    
    mock_response = MagicMock()
    mock_response.choices[0].message.content = "Success"
    mock_response.choices[0].finish_reason = "stop"
    mock_response.model = "model"
    mock_response.usage = None
    
    err_response = httpx.Response(503, request=httpx.Request("POST", "url"))
    
    mock_client.chat.completions.create.side_effect = [
        groq.APIStatusError(message="503", response=err_response, body=None),
        mock_response
    ]
    
    client = GroqClient()
    response = client.generate("system", "user")
    assert response.content == "Success"

@patch("llm.groq_client.Groq")
@patch("llm.groq_client.get_settings")
def test_bad_request_non_retryable(mock_get, mock_groq_class, mock_settings):
    mock_get.return_value = mock_settings
    mock_client = MagicMock()
    mock_groq_class.return_value = mock_client
    
    mock_client.chat.completions.create.side_effect = groq.BadRequestError(
        message="Bad Request", response=MagicMock(), body=None
    )
    
    client = GroqClient()
    with pytest.raises(LLMRequestError):
        client.generate("system", "user")
    
    assert mock_client.chat.completions.create.call_count == 1
