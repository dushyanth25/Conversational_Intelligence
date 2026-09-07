import json

import pytest

from llm.response_validator import ResponseValidator
from llm.validation_exceptions import (
    InvalidEvidenceError,
    LLMJSONParseError,
    LLMSchemaValidationError,
    MissingParametersError,
    UnexpectedParametersError,
)
from models.conversation import AlignedSegment, Conversation, SpeakerRole
from pipeline.insights.batch_models import InsightBatch
from pipeline.insights.models import InsightPrompt


def create_conversation():
    return Conversation(
        call_id="CALL_123",
        speaker_count=2,
        segments=[
            AlignedSegment(
                start=0.0,
                end=1.5,
                speaker="SPEAKER_00",
                speaker_role=SpeakerRole.CUSTOMER,
                text="I have been waiting for this for two weeks."
            ),
            AlignedSegment(
                start=2.0,
                end=3.5,
                speaker="SPEAKER_01",
                speaker_role=SpeakerRole.AGENT,
                text="வணக்கம்"
            )
        ]
    )

def create_batch(params=None):
    if params is None:
        params = ["sentiment", "intent", "resolution"]
    prompts = [InsightPrompt(parameter=p, prompt=f"Check {p}.") for p in params]
    return InsightBatch(batch_id="batch_001", parameters=prompts)

def test_valid_response():
    conv = create_conversation()
    batch = create_batch(["sentiment"])
    raw_text = json.dumps({
        "results": [
            {
                "parameter": "sentiment",
                "result": "negative",
                "confidence": 0.92,
                "evidence": [
                    {
                        "timestamp": "00:03:21",
                        "speaker": "CUSTOMER",
                        "text": "I have been waiting for this for two weeks."
                    }
                ]
            }
        ]
    })
    
    val = ResponseValidator()
    result = val.validate(raw_text, batch, conv)
    assert result.status == "validated"
    assert result.results[0].parameter == "sentiment"
    assert result.results[0].confidence == 0.92

def test_valid_three_parameter_response():
    conv = create_conversation()
    batch = create_batch(["sentiment", "intent", "resolution"])
    raw_text = json.dumps({
        "results": [
            {"parameter": "sentiment", "result": "negative", "confidence": 0.9},
            {"parameter": "intent", "result": "complaint", "confidence": 0.8},
            {"parameter": "resolution", "result": "no", "confidence": 0.99}
        ]
    })
    
    val = ResponseValidator()
    result = val.validate(raw_text, batch, conv)
    assert len(result.results) == 3

def test_missing_parameter():
    conv = create_conversation()
    batch = create_batch(["sentiment", "intent", "resolution"])
    raw_text = json.dumps({
        "results": [
            {"parameter": "sentiment", "result": "negative", "confidence": 0.9},
            {"parameter": "intent", "result": "complaint", "confidence": 0.8}
        ]
    })
    
    val = ResponseValidator()
    with pytest.raises(MissingParametersError):
        val.validate(raw_text, batch, conv)

def test_extra_parameter():
    conv = create_conversation()
    batch = create_batch(["sentiment", "intent"])
    raw_text = json.dumps({
        "results": [
            {"parameter": "sentiment", "result": "negative", "confidence": 0.9},
            {"parameter": "intent", "result": "complaint", "confidence": 0.8},
            {"parameter": "resolution", "result": "no", "confidence": 0.99}
        ]
    })
    
    val = ResponseValidator()
    with pytest.raises(UnexpectedParametersError):
        val.validate(raw_text, batch, conv)

def test_duplicate_parameter():
    conv = create_conversation()
    batch = create_batch(["sentiment"])
    raw_text = json.dumps({
        "results": [
            {"parameter": "sentiment", "result": "a"},
            {"parameter": "sentiment", "result": "b"}
        ]
    })
    
    val = ResponseValidator()
    with pytest.raises(UnexpectedParametersError, match="Duplicate"):
        val.validate(raw_text, batch, conv)

def test_invalid_json():
    conv = create_conversation()
    batch = create_batch(["sentiment"])
    raw_text = "Here is the answer:\n { 'results': [ "
    
    val = ResponseValidator()
    with pytest.raises(LLMJSONParseError):
        val.validate(raw_text, batch, conv)

def test_json_inside_markdown_code_fence():
    conv = create_conversation()
    batch = create_batch(["sentiment"])
    raw_text = "```json\n" + json.dumps({
        "results": [
            {"parameter": "sentiment", "result": "negative"}
        ]
    }) + "\n```"
    
    val = ResponseValidator()
    result = val.validate(raw_text, batch, conv)
    assert result.results[0].parameter == "sentiment"

def test_invalid_confidence():
    conv = create_conversation()
    batch = create_batch(["sentiment"])
    raw_text = json.dumps({
        "results": [
            {"parameter": "sentiment", "result": "negative", "confidence": 1.5}
        ]
    })
    
    val = ResponseValidator()
    with pytest.raises(LLMSchemaValidationError):
        val.validate(raw_text, batch, conv)

def test_empty_result():
    conv = create_conversation()
    batch = create_batch(["sentiment"])
    raw_text = json.dumps({
        "results": [
            {"parameter": "sentiment", "result": "", "confidence": 0.9}
        ]
    })
    
    val = ResponseValidator()
    # Pydantic may or may not allow empty string for result based on schema. 
    # Since Field(...) doesn't have min_length=1, it is valid.
    result = val.validate(raw_text, batch, conv)
    assert result.results[0].result == ""

def test_invalid_evidence():
    conv = create_conversation()
    batch = create_batch(["sentiment"])
    raw_text = json.dumps({
        "results": [
            {
                "parameter": "sentiment", 
                "result": "negative", 
                "evidence": [
                    {"timestamp": "123"} # missing speaker and text
                ]
            }
        ]
    })
    
    val = ResponseValidator()
    with pytest.raises(LLMSchemaValidationError):
        val.validate(raw_text, batch, conv)

def test_evidence_not_found_in_transcript():
    conv = create_conversation()
    batch = create_batch(["sentiment"])
    raw_text = json.dumps({
        "results": [
            {
                "parameter": "sentiment",
                "result": "negative",
                "evidence": [
                    {
                        "timestamp": "00:03:21",
                        "speaker": "CUSTOMER",
                        "text": "I never said this."
                    }
                ]
            }
        ]
    })
    
    val = ResponseValidator()
    with pytest.raises(InvalidEvidenceError):
        val.validate(raw_text, batch, conv)

def test_unicode_evidence():
    conv = create_conversation()
    batch = create_batch(["sentiment"])
    raw_text = json.dumps({
        "results": [
            {
                "parameter": "sentiment",
                "result": "negative",
                "evidence": [
                    {
                        "timestamp": "00:03:21",
                        "speaker": "AGENT",
                        "text": "வணக்கம்"
                    }
                ]
            }
        ]
    })
    
    val = ResponseValidator()
    result = val.validate(raw_text, batch, conv)
    assert result.results[0].evidence[0].text == "வணக்கம்"

def test_empty_results():
    conv = create_conversation()
    batch = create_batch(["sentiment"])
    raw_text = json.dumps({"results": []})
    
    val = ResponseValidator()
    with pytest.raises(MissingParametersError):
        val.validate(raw_text, batch, conv)

def test_wrong_response_type():
    conv = create_conversation()
    batch = create_batch(["sentiment"])
    raw_text = json.dumps([{"parameter": "sentiment", "result": "negative"}])
    
    val = ResponseValidator()
    with pytest.raises(LLMJSONParseError):
        val.validate(raw_text, batch, conv)

def test_missing_results_field():
    conv = create_conversation()
    batch = create_batch(["sentiment"])
    raw_text = json.dumps({"data": []})
    
    val = ResponseValidator()
    with pytest.raises(LLMSchemaValidationError):
        val.validate(raw_text, batch, conv)

def test_deterministic_validation():
    conv = create_conversation()
    batch = create_batch(["sentiment"])
    raw_text = json.dumps({
        "results": [{"parameter": "sentiment", "result": "negative"}]
    })
    
    val = ResponseValidator()
    result1 = val.validate(raw_text, batch, conv)
    result2 = val.validate(raw_text, batch, conv)
    assert result1.model_dump() == result2.model_dump()
