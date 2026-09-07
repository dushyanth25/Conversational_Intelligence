from models import DiarizationSegment, TranscriptSegment
from models.transcription import TranscriptionWord
from pipeline.alignment.algorithm import align_segments, get_overlap
from pipeline.alignment.service import AlignmentService


def ts(start, end, text, words=None):
    return TranscriptSegment(
        start=start, end=end, text=text, confidence=0.9, language="en", words=words
    )

def ds(start, end, speaker):
    return DiarizationSegment(start=start, end=end, speaker=speaker)

def test_get_overlap():
    assert get_overlap(1.0, 4.0, 0.5, 3.0) == 2.0
    assert get_overlap(1.0, 4.0, 3.0, 5.0) == 1.0
    assert get_overlap(1.0, 2.0, 3.0, 4.0) == 0.0
    assert get_overlap(1.0, 4.0, 2.0, 3.0) == 1.0

def test_perfect_overlap():
    aligned = align_segments([ts(1.0, 4.0, "Hello")], [ds(1.0, 4.0, "SPEAKER_00")])
    assert len(aligned) == 1
    assert aligned[0].speaker == "SPEAKER_00"
    assert aligned[0].text == "Hello"

def test_partial_overlap():
    aligned = align_segments([ts(1.2, 4.5, "Hello")], [ds(1.0, 4.8, "SPEAKER_00")])
    assert aligned[0].speaker == "SPEAKER_00"
    assert aligned[0].start == 1.2
    assert aligned[0].end == 4.5

def test_no_overlap():
    aligned = align_segments([ts(1.0, 2.0, "Hello")], [ds(3.0, 5.0, "SPEAKER_00")])
    assert aligned[0].speaker == "UNKNOWN"

def test_multiple_speakers():
    d_segs = [ds(0.0, 2.0, "SPEAKER_00"), ds(2.0, 6.0, "SPEAKER_01")]
    aligned = align_segments([ts(1.0, 5.0, "Hello")], d_segs)
    assert aligned[0].speaker == "SPEAKER_01"

def test_boundary_mismatch():
    aligned = align_segments(
        [ts(1.0, 2.0, "Hello")], [ds(2.01, 3.0, "SPEAKER_00")], 0.1
    )
    assert aligned[0].speaker == "SPEAKER_00"

def test_word_level_timestamps():
    words = [
        TranscriptionWord(start=1.0, end=2.0, word="Hello", probability=0.9),
        TranscriptionWord(start=3.0, end=5.0, word="world", probability=0.9)
    ]
    aligned = align_segments(
        [ts(1.0, 5.0, "Hello world", words)],
        [ds(0.5, 2.5, "SPEAKER_00"), ds(2.5, 6.0, "SPEAKER_01")]
    )
    assert len(aligned) == 2
    assert aligned[0].text == "Hello"
    assert aligned[0].speaker == "SPEAKER_00"
    assert aligned[1].text == "world"
    assert aligned[1].speaker == "SPEAKER_01"

def test_text_preservation():
    aligned = align_segments([ts(1.0, 4.0, "Msg")], [])
    assert aligned[0].speaker == "UNKNOWN"
    assert aligned[0].text == "Msg"

def test_service():
    service = AlignmentService()
    aligned = service.process(
        "CALL_123", [ts(1.0, 4.0, "Test")], [ds(0.5, 4.5, "SPK_0")]
    )
    assert aligned[0].speaker == "SPK_0"

def test_chronological_ordering():
    t_segs = [ts(1.0, 2.0, "A"), ts(3.0, 4.0, "B")]
    d_segs = [ds(3.0, 4.5, "S2"), ds(0.5, 2.5, "S1")]
    aligned = align_segments(t_segs, d_segs)
    assert aligned[0].text == "A"
    assert aligned[0].speaker == "S1"
    assert aligned[1].text == "B"
    assert aligned[1].speaker == "S2"
