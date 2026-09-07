from unittest.mock import MagicMock, patch

import pytest

from llm.exceptions import LLMRateLimitError, LLMTimeoutError
from llm.models import LLMResponse, PromptRequest
from llm.validation_exceptions import (
    InvalidEvidenceError,
    LLMJSONParseError,
    MissingParametersError,
)
from llm.validation_models import InsightBatchResult
from models.conversation import Conversation
from pipeline.insights.batch_models import InsightBatch
from pipeline.insights.batch_processor import BatchProcessor
from pipeline.insights.batch_service import BatchService
from pipeline.insights.exceptions import BatchProcessingError
from pipeline.insights.models import InsightPrompt


@pytest.fixture
def mock_llm_client():
    return MagicMock()

@pytest.fixture
def mock_request_builder():
    with patch("pipeline.insights.batch_processor.RequestBuilder") as mock:
        yield mock.return_value

@pytest.fixture
def mock_validator():
    with patch("pipeline.insights.batch_processor.ResponseValidator") as mock:
        yield mock.return_value

def test_successful_batch(mock_llm_client, mock_request_builder, mock_validator):
    conv = Conversation(call_id="C1", speaker_count=1, segments=[])
    batch = InsightBatch(
        batch_id="B1", parameters=[InsightPrompt(parameter="p1", prompt="p1")]
    )
    
    mock_request_builder.build_request.return_value = PromptRequest(
        system_prompt="s", user_prompt="u", batch_id="B1", call_id="C1", model="model"
    )
    mock_llm_client.generate.return_value = LLMResponse(content="{}", model="model")
    mock_validator.validate.return_value = InsightBatchResult(
        batch_id="B1", call_id="C1", results=[], status="VALIDATED"
    )
    
    processor = BatchProcessor(mock_llm_client)
    res = processor.process_batch("C1", conv, batch)
    assert res.status == "VALIDATED"
    assert res.batch_id == "B1"

def test_llm_timeout(mock_llm_client, mock_request_builder, mock_validator):
    conv = Conversation(call_id="C1", speaker_count=1, segments=[])
    batch = InsightBatch(
        batch_id="B1", parameters=[InsightPrompt(parameter="p1", prompt="p1")]
    )
    
    mock_request_builder.build_request.return_value = PromptRequest(
        system_prompt="s", user_prompt="u", batch_id="B1", call_id="C1", model="model"
    )
    mock_llm_client.generate.side_effect = LLMTimeoutError("Timeout")
    
    processor = BatchProcessor(mock_llm_client)
    with pytest.raises(BatchProcessingError, match="LLM Error"):
        processor.process_batch("C1", conv, batch)

def test_llm_rate_limit(mock_llm_client, mock_request_builder, mock_validator):
    conv = Conversation(call_id="C1", speaker_count=1, segments=[])
    batch = InsightBatch(
        batch_id="B1", parameters=[InsightPrompt(parameter="p1", prompt="p1")]
    )
    
    mock_request_builder.build_request.return_value = PromptRequest(
        system_prompt="s", user_prompt="u", batch_id="B1", call_id="C1", model="model"
    )
    mock_llm_client.generate.side_effect = LLMRateLimitError("Rate limit")
    
    processor = BatchProcessor(mock_llm_client)
    with pytest.raises(BatchProcessingError, match="LLM Error"):
        processor.process_batch("C1", conv, batch)

def test_invalid_json(mock_llm_client, mock_request_builder, mock_validator):
    conv = Conversation(call_id="C1", speaker_count=1, segments=[])
    batch = InsightBatch(
        batch_id="B1", parameters=[InsightPrompt(parameter="p1", prompt="p1")]
    )
    
    mock_request_builder.build_request.return_value = PromptRequest(
        system_prompt="s", user_prompt="u", batch_id="B1", call_id="C1", model="model"
    )
    mock_llm_client.generate.return_value = LLMResponse(
        content="invalid", model="model"
    )
    mock_validator.validate.side_effect = LLMJSONParseError("Parse error")
    
    processor = BatchProcessor(mock_llm_client)
    with pytest.raises(BatchProcessingError, match="Validation Error"):
        processor.process_batch("C1", conv, batch)

def test_missing_parameter(mock_llm_client, mock_request_builder, mock_validator):
    conv = Conversation(call_id="C1", speaker_count=1, segments=[])
    batch = InsightBatch(
        batch_id="B1", parameters=[InsightPrompt(parameter="p1", prompt="p1")]
    )
    
    mock_request_builder.build_request.return_value = PromptRequest(
        system_prompt="s", user_prompt="u", batch_id="B1", call_id="C1", model="model"
    )
    mock_llm_client.generate.return_value = LLMResponse(content="{}", model="model")
    mock_validator.validate.side_effect = MissingParametersError("Missing")
    
    processor = BatchProcessor(mock_llm_client)
    with pytest.raises(BatchProcessingError, match="Validation Error"):
        processor.process_batch("C1", conv, batch)

def test_invalid_evidence(mock_llm_client, mock_request_builder, mock_validator):
    conv = Conversation(call_id="C1", speaker_count=1, segments=[])
    batch = InsightBatch(
        batch_id="B1", parameters=[InsightPrompt(parameter="p1", prompt="p1")]
    )
    
    mock_request_builder.build_request.return_value = PromptRequest(
        system_prompt="s", user_prompt="u", batch_id="B1", call_id="C1", model="model"
    )
    mock_llm_client.generate.return_value = LLMResponse(content="{}", model="model")
    mock_validator.validate.side_effect = InvalidEvidenceError("Invalid")
    
    processor = BatchProcessor(mock_llm_client)
    with pytest.raises(BatchProcessingError, match="Validation Error"):
        processor.process_batch("C1", conv, batch)

def test_batch_service_integration(
    mock_llm_client, mock_request_builder, mock_validator
):
    conv = Conversation(call_id="C1", speaker_count=1, segments=[])
    batch = InsightBatch(
        batch_id="B1", parameters=[InsightPrompt(parameter="p1", prompt="p1")]
    )
    
    mock_request_builder.build_request.return_value = PromptRequest(
        system_prompt="s", user_prompt="u", batch_id="B1", call_id="C1", model="model"
    )
    mock_llm_client.generate.return_value = LLMResponse(content="{}", model="model")
    mock_validator.validate.return_value = InsightBatchResult(
        batch_id="B1", call_id="C1", results=[], status="VALIDATED"
    )
    
    service = BatchService(mock_llm_client)
    res = service.process("C1", conv, batch)
    assert res.status == "VALIDATED"

def test_unexpected_error(mock_llm_client, mock_request_builder, mock_validator):
    conv = Conversation(call_id="C1", speaker_count=1, segments=[])
    batch = InsightBatch(
        batch_id="B1", parameters=[InsightPrompt(parameter="p1", prompt="p1")]
    )
    
    mock_request_builder.build_request.side_effect = ValueError("Unexpected")
    
    processor = BatchProcessor(mock_llm_client)
    with pytest.raises(BatchProcessingError, match="Unexpected error"):
        processor.process_batch("C1", conv, batch)
