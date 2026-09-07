from datetime import datetime

import pytest
from pydantic import ValidationError

from models import (
    AlignedSegment,
    AudioInput,
    Conversation,
    DiarizationSegment,
    Evidence,
    InsightParameter,
    InsightResult,
    ParameterBatch,
    ProcessingJob,
    SpeakerRole,
    SpeakerRoleMapping,
    TranscriptSegment,
    VADSegment,
    WorkflowStatus,
    WorkflowStatusEnum,
)


def test_audio_input_valid():
    """Test valid AudioInput properties."""
    model = AudioInput(audio_path="test.wav", prompt_sheet="prompts.csv")
    assert model.audio_path == "test.wav"
    assert model.parallel_workers > 0
    assert model.language == "auto"
    assert model.call_id is not None


def test_audio_input_invalid_workers():
    """Test AudioInput rejects zero or negative workers."""
    with pytest.raises(ValidationError):
        AudioInput(
            audio_path="test.wav", prompt_sheet="prompts.csv", parallel_workers=0
        )


def test_vad_segment_valid():
    """Test valid VADSegment."""
    model = VADSegment(start=1.0, end=2.5, is_speech=True)
    assert model.start == 1.0


def test_vad_segment_invalid_timestamps():
    """Test VADSegment validates start < end."""
    with pytest.raises(ValidationError):
        VADSegment(start=2.5, end=1.0, is_speech=True)


def test_transcript_segment_valid():
    """Test valid TranscriptSegment."""
    model = TranscriptSegment(start=1.0, end=2.0, text="hello", confidence=0.9)
    assert model.text == "hello"


def test_transcript_segment_empty_text():
    """Test TranscriptSegment rejects empty text."""
    with pytest.raises(ValidationError):
        TranscriptSegment(start=1.0, end=2.0, text="")


def test_transcript_segment_invalid_confidence():
    """Test TranscriptSegment rejects confidence > 1.0."""
    with pytest.raises(ValidationError):
        TranscriptSegment(start=1.0, end=2.0, text="hello", confidence=1.5)


def test_diarization_segment():
    """Test DiarizationSegment rejects empty speaker."""
    with pytest.raises(ValidationError):
        DiarizationSegment(start=1.0, end=2.0, speaker="")


def test_conversation_serialization():
    """Test canonical Conversation model JSON serialization."""
    segment = AlignedSegment(start=0.0, end=1.0, speaker="SPEAKER_00", text="Hi")
    conv = Conversation(call_id="123", speaker_count=1, segments=[segment])
    json_data = conv.model_dump_json()

    conv_restored = Conversation.model_validate_json(json_data)
    assert conv_restored.call_id == "123"
    assert len(conv_restored.segments) == 1
    assert conv_restored.segments[0].text == "Hi"


def test_speaker_role_enum():
    """Test Enum validations."""
    assert SpeakerRole.AGENT.value == "AGENT"

    mapping = SpeakerRoleMapping(
        speaker="SPEAKER_00", role=SpeakerRole.AGENT, confidence=0.95
    )
    assert mapping.role == SpeakerRole.AGENT


def test_insights():
    """Test Insights canonical models."""
    with pytest.raises(ValidationError):
        InsightParameter(parameter="", prompt="test")

    param = InsightParameter(parameter="sentiment", prompt="Is this positive?")
    batch = ParameterBatch(batch_id="b1", call_id="c1", parameters=[param])
    assert len(batch.parameters) == 1

    evidence = Evidence(timestamp="00:01", speaker="A", text="Good")
    result = InsightResult(
        parameter="sentiment", result="Positive", confidence=0.9, evidence=[evidence]
    )

    # JSON test
    restored = InsightResult.model_validate_json(result.model_dump_json())
    assert restored.confidence == 0.9
    assert restored.evidence[0].timestamp == "00:01"


def test_workflow():
    """Test Workflow canonical models."""
    status = WorkflowStatus(
        workflow_id="w1", call_id="c1", status=WorkflowStatusEnum.RUNNING
    )
    assert status.status == WorkflowStatusEnum.RUNNING

    job = ProcessingJob(
        workflow_id="w1", call_id="c1", status=WorkflowStatusEnum.SUBMITTED
    )
    assert job.status == WorkflowStatusEnum.SUBMITTED
    assert isinstance(job.created_at, datetime)
