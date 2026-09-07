import pytest

from llm.context import FullTranscriptContext
from llm.request_builder import RequestBuilder
from models.conversation import AlignedSegment, Conversation, SpeakerRole
from pipeline.insights.batch_models import InsightBatch
from pipeline.insights.models import InsightPrompt


def create_conversation(segments=None):
    if segments is None:
        segments = [
            AlignedSegment(
                start=0.0,
                end=1.5,
                speaker="SPEAKER_00",
                speaker_role=SpeakerRole.AGENT,
                text="Hello there"
            ),
            AlignedSegment(
                start=2.0,
                end=3.5,
                speaker="SPEAKER_01",
                speaker_role=SpeakerRole.CUSTOMER,
                text="Hi I have a problem"
            )
        ]
    return Conversation(
        call_id="CALL_123",
        speaker_count=2,
        segments=segments,
    )

def create_batch(prompts=None):
    if prompts is None:
        prompts = [
            InsightPrompt(parameter="sentiment", prompt="Analyze sentiment."),
            InsightPrompt(parameter="intent", prompt="Identify intent."),
            InsightPrompt(parameter="resolution", prompt="Check resolution.")
        ]
    return InsightBatch(
        batch_id="batch_001",
        parameters=prompts
    )

def test_three_parameter_batch():
    conv = create_conversation()
    batch = create_batch()
    builder = RequestBuilder()
    req = builder.build_request(conv, batch)
    
    assert req.batch_id == "batch_001"
    assert req.call_id == "CALL_123"
    assert "sentiment" in req.user_prompt
    assert "intent" in req.user_prompt
    assert "resolution" in req.user_prompt

def test_one_parameter_batch():
    conv = create_conversation()
    batch = create_batch(
        [InsightPrompt(parameter="sentiment", prompt="Analyze sentiment.")]
    )
    builder = RequestBuilder()
    req = builder.build_request(conv, batch)
    
    assert "sentiment" in req.user_prompt
    assert "intent" not in req.user_prompt

def test_transcript_formatting():
    conv = create_conversation()
    batch = create_batch()
    builder = RequestBuilder()
    req = builder.build_request(conv, batch)
    
    assert "[0.00 - 1.50] SPEAKER_00 (AGENT): Hello there" in req.user_prompt
    assert "[2.00 - 3.50] SPEAKER_01 (CUSTOMER): Hi I have a problem" in req.user_prompt

def test_evidence_instruction():
    builder = RequestBuilder()
    req = builder.build_request(create_conversation(), create_batch())
    
    assert "fabricate evidence" in req.system_prompt
    assert "Base your conclusions ONLY on the supplied transcript" in req.system_prompt

def test_parameter_preservation():
    conv = create_conversation()
    batch = create_batch()
    builder = RequestBuilder()
    req = builder.build_request(conv, batch)
    assert "PARAMETER:\nsentiment" in req.user_prompt

def test_prompt_preservation():
    conv = create_conversation()
    batch = create_batch()
    builder = RequestBuilder()
    req = builder.build_request(conv, batch)
    assert "PROMPT:\nAnalyze sentiment." in req.user_prompt

def test_unicode_tamil_transcript():
    conv = create_conversation([
        AlignedSegment(
            start=0.0, end=1.0, speaker="SPEAKER_00", 
            speaker_role=SpeakerRole.CUSTOMER, text="வணக்கம்"
        )
    ])
    batch = create_batch()
    builder = RequestBuilder()
    req = builder.build_request(conv, batch)
    assert "வணக்கம்" in req.user_prompt

def test_empty_transcript_handling():
    conv = create_conversation([])
    batch = create_batch()
    builder = RequestBuilder()
    req = builder.build_request(conv, batch)
    
    assert "CONVERSATION:" in req.user_prompt
    assert "REQUESTED INSIGHTS" in req.user_prompt

def test_deterministic_output():
    conv = create_conversation()
    batch = create_batch()
    builder = RequestBuilder()
    req1 = builder.build_request(conv, batch)
    req2 = builder.build_request(conv, batch)
    assert req1.user_prompt == req2.user_prompt
    assert req1.system_prompt == req2.system_prompt

def test_no_hardcoded_parameter_names():
    conv = create_conversation()
    batch = create_batch(
        [InsightPrompt(parameter="random_param_99", prompt="Do stuff.")]
    )
    builder = RequestBuilder()
    req = builder.build_request(conv, batch)
    assert "random_param_99" in req.user_prompt
    assert "sentiment" not in req.user_prompt

def test_long_context_handling():
    conv = create_conversation([
        AlignedSegment(
            start=0.0, end=1.0, speaker="SPEAKER_00", text="A" * 50000
        )
    ])
    # Assume default limit is 100000
    ctx = FullTranscriptContext(conv, max_length=1000)
    with pytest.raises(ValueError, match="exceeds maximum allowed length"):
        ctx.get_context()
