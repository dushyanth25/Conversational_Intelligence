import csv
import json

import pytest

from models import AlignedSegment, SpeakerRole, SpeakerRoleMapping
from pipeline.transcript.exceptions import TranscriptValidationError
from pipeline.transcript.service import TranscriptService


def seg(start, end, speaker, text):
    return AlignedSegment(start=start, end=end, speaker=speaker, text=text)

def test_canonical_conversation_creation(tmp_path):
    service = TranscriptService()
    csv_path = tmp_path / "out.csv"
    json_path = tmp_path / "out.json"

    segments = [seg(1.0, 2.0, "SPEAKER_00", "Hello, I am calling regarding my order.")]
    mappings = [SpeakerRoleMapping(speaker="SPEAKER_00", role=SpeakerRole.CUSTOMER)]

    conv = service.process(
        "CALL_001", segments, mappings, str(csv_path), str(json_path)
    )

    assert conv.call_id == "CALL_001"
    assert conv.speaker_count == 1
    assert conv.segments[0].speaker == "SPEAKER_00"
    assert conv.segments[0].speaker_role == SpeakerRole.CUSTOMER
    assert csv_path.exists()
    assert json_path.exists()

def test_csv_exact_three_columns(tmp_path):
    service = TranscriptService()
    csv_path = tmp_path / "out.csv"
    segments = [seg(1.0, 2.0, "SPEAKER_00", "Hello")]
    service.process("C1", segments, [], str(csv_path), str(tmp_path / "out.json"))

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
        assert header == ["timestamp", "speaker", "transcript"]
        row = next(reader)
        assert len(row) == 3

def test_chronological_ordering(tmp_path):
    service = TranscriptService()
    segments = [
        seg(2.0, 3.0, "SPEAKER_00", "B"),
        seg(1.0, 1.5, "SPEAKER_01", "A")
    ]
    with pytest.raises(TranscriptValidationError, match="chronologically ordered"):
        service.process(
            "C1", segments, [], str(tmp_path / "csv"), str(tmp_path / "json")
        )

def test_unknown_role(tmp_path):
    service = TranscriptService()
    csv_path = tmp_path / "out.csv"
    segments = [seg(1.0, 2.0, "SPEAKER_00", "Hello")]
    
    conv = service.process(
        "C1", segments, [], str(csv_path), str(tmp_path / "out.json")
    )
    assert conv.segments[0].speaker == "SPEAKER_00"
    assert conv.segments[0].speaker_role == SpeakerRole.UNKNOWN

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader)
        row = next(reader)
        assert row[1] == "UNKNOWN"

def test_multilingual_text(tmp_path):
    service = TranscriptService()
    csv_path = tmp_path / "out.csv"
    segments = [seg(1.0, 2.0, "SPEAKER_00", "எனது ஆர்டர் இன்னும் வரவில்லை.")]
    
    service.process("C1", segments, [], str(csv_path), str(tmp_path / "out.json"))
    
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader)
        row = next(reader)
        assert row[2] == "எனது ஆர்டர் இன்னும் வரவில்லை."

def test_csv_escaping(tmp_path):
    service = TranscriptService()
    csv_path = tmp_path / "out.csv"
    segments = [seg(1.0, 2.0, "SPEAKER_00", 'He said, "Hello\nWorld"')]
    
    service.process("C1", segments, [], str(csv_path), str(tmp_path / "out.json"))
    
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader)
        row = next(reader)
        assert row[2] == 'He said, "Hello\nWorld"'

def test_empty_transcript_rejection(tmp_path):
    service = TranscriptService()
    segments = [seg(1.0, 2.0, "SPEAKER_00", "   ")]
    with pytest.raises(TranscriptValidationError, match="missing text"):
        service.process(
            "C1", segments, [], str(tmp_path / "csv"), str(tmp_path / "json")
        )

def test_invalid_timestamps(tmp_path):
    with pytest.raises(ValueError):
        seg(2.0, 1.0, "SPEAKER_00", "Hello")

def test_deterministic_output(tmp_path):
    service = TranscriptService()
    csv_path = tmp_path / "out.csv"
    segments = [seg(1.0, 2.0, "SPEAKER_00", "Hello")]
    
    service.process("C1", segments, [], str(csv_path), str(tmp_path / "out.json"))
    content1 = csv_path.read_text()
    
    service.process("C1", segments, [], str(csv_path), str(tmp_path / "out.json"))
    content2 = csv_path.read_text()
    
    assert content1 == content2

def test_json_serialization(tmp_path):
    service = TranscriptService()
    json_path = tmp_path / "out.json"
    segments = [seg(1.0, 2.0, "SPEAKER_00", "Hello")]
    service.process("C1", segments, [], str(tmp_path / "csv"), str(json_path))
    
    data = json.loads(json_path.read_text())
    assert data["call_id"] == "C1"
    assert data["segments"][0]["text"] == "Hello"
