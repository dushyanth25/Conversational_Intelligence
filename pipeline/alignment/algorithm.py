from typing import List, Tuple

from models import AlignedSegment, DiarizationSegment, TranscriptSegment
from models.transcription import TranscriptionWord


def get_overlap(start1: float, end1: float, start2: float, end2: float) -> float:
    """Calculate the overlap duration between two intervals."""
    overlap_start = max(start1, start2)
    overlap_end = min(end1, end2)
    return max(0.0, overlap_end - overlap_start)


def align_word_to_speaker(
    word: TranscriptionWord,
    diarization_segments: List[DiarizationSegment],
    tolerance: float = 0.1,
) -> str:
    """
    Find the dominant speaker for a single word.
    Fallback to 'UNKNOWN' if no overlap found.
    """
    best_speaker = "UNKNOWN"
    max_overlap = 0.0

    for d_seg in diarization_segments:
        if d_seg.end + tolerance < word.start:
            continue
        if d_seg.start - tolerance > word.end:
            break

        overlap = get_overlap(
            word.start - tolerance, word.end + tolerance, d_seg.start, d_seg.end
        )
        if overlap > max_overlap:
            max_overlap = overlap
            best_speaker = d_seg.speaker

    return best_speaker


def split_segment_by_words(
    segment: TranscriptSegment,
    diarization_segments: List[DiarizationSegment],
    tolerance: float = 0.1,
) -> List[AlignedSegment]:
    """
    Split a transcript segment that has word-level timestamps into multiple 
    aligned segments if different speakers speak different words.
    """
    if not segment.words:
        return []

    current_speaker = None
    current_words = []
    aligned_segments = []

    def flush():
        if not current_words:
            return
        
        start = current_words[0].start
        end = current_words[-1].end
        text = " ".join(w.word for w in current_words)
        
        aligned_segments.append(
            AlignedSegment(
                start=start,
                end=end,
                speaker=current_speaker,
                text=text,
                confidence=segment.confidence,
                language=segment.language,
                words=current_words.copy()
            )
        )

    for word in segment.words:
        speaker = align_word_to_speaker(word, diarization_segments, tolerance)
        
        if current_speaker is None:
            current_speaker = speaker

        if speaker != current_speaker:
            flush()
            current_speaker = speaker
            current_words = [word]
        else:
            current_words.append(word)

    flush()
    return aligned_segments


def get_dominant_speaker(
    start: float,
    end: float,
    diarization_segments: List[DiarizationSegment],
    tolerance: float = 0.1,
) -> Tuple[str, float]:
    """
    Find the dominant speaker for an interval.
    Returns (speaker, overlap_duration).
    """
    best_speaker = "UNKNOWN"
    max_overlap = 0.0

    for d_seg in diarization_segments:
        if d_seg.end + tolerance < start:
            continue
        if d_seg.start - tolerance > end:
            break

        overlap = get_overlap(
            start - tolerance, end + tolerance, d_seg.start, d_seg.end
        )
        if overlap > max_overlap:
            max_overlap = overlap
            best_speaker = d_seg.speaker

    return best_speaker, max_overlap


def align_segments(
    transcript_segments: List[TranscriptSegment],
    diarization_segments: List[DiarizationSegment],
    tolerance: float = 0.1,
) -> List[AlignedSegment]:
    """
    Combine ASR transcript segments with speaker diarization segments.
    """
    aligned = []
    
    # Sort diarization segments by start time
    sorted_diarization = sorted(diarization_segments, key=lambda x: x.start)

    for t_seg in transcript_segments:
        # Optimization: narrow down possible diarization segments
        relevant_diarization = [
            d for d in sorted_diarization 
            if not (d.end + tolerance < t_seg.start or d.start - tolerance > t_seg.end)
        ]

        if not relevant_diarization:
            # No overlap found -> UNKNOWN
            aligned.append(
                AlignedSegment(
                    start=t_seg.start,
                    end=t_seg.end,
                    speaker="UNKNOWN",
                    text=t_seg.text,
                    confidence=t_seg.confidence,
                    language=t_seg.language,
                    words=t_seg.words
                )
            )
            continue

        # Check if multiple speakers overlap this segment
        overlapping_speakers = set()
        for d_seg in relevant_diarization:
            overlap = get_overlap(
                t_seg.start - tolerance, t_seg.end + tolerance, d_seg.start, d_seg.end
            )
            if overlap > 0:
                overlapping_speakers.add(d_seg.speaker)

        if len(overlapping_speakers) > 1 and t_seg.words:
            # We have multiple speakers and word-level timestamps! Split it.
            split_aligned = split_segment_by_words(
                t_seg, relevant_diarization, tolerance
            )
            aligned.extend(split_aligned)
        else:
            # Single speaker, or no word-level timestamps to split
            best_speaker, _ = get_dominant_speaker(
                t_seg.start, t_seg.end, relevant_diarization, tolerance
            )
            
            aligned.append(
                AlignedSegment(
                    start=t_seg.start,
                    end=t_seg.end,
                    speaker=best_speaker,
                    text=t_seg.text,
                    confidence=t_seg.confidence,
                    language=t_seg.language,
                    words=t_seg.words
                )
            )

    return aligned
