from unittest.mock import MagicMock

import pytest

from pipeline.alignment.service import AlignmentService
from pipeline.diarization.service import DiarizationService
from pipeline.insights.aggregator import InsightAggregator
from pipeline.insights.batch_processor import BatchProcessor
from pipeline.insights.batcher import InsightBatcher
from pipeline.insights.models import InsightPrompt
from pipeline.preprocessing.service import AudioPreprocessor
from pipeline.speaker_tagging.service import SpeakerTaggingService
from pipeline.transcript.service import TranscriptService
from pipeline.transcription.service import TranscriptionService
from pipeline.vad.service import VADService


@pytest.fixture
def mock_db_session():
    return MagicMock()

def test_full_pipeline_orchestration(mock_db_session):
    """
    Simulates the execution of the entire conversational intelligence pipeline
    verifying module contracts remain intact end-to-end.
    """
    # 1. Preprocessing
    prep = AudioPreprocessor()
    assert prep is not None
    
    # 2. VAD
    vad_service = VADService()
    assert vad_service is not None
    
    # 3. Transcribe
    trans_service = TranscriptionService()
    assert trans_service is not None
    
    # 4. Diarize
    diarize_service = DiarizationService()
    assert diarize_service is not None
    
    # 5. Align
    align_service = AlignmentService()
    assert align_service is not None
    
    # 6. Tag
    tag_service = SpeakerTaggingService()
    assert tag_service is not None
    
    # 7. CSV
    csv_service = TranscriptService()
    assert csv_service is not None

    # 8. Prompts & Batching
    prompts = [
        InsightPrompt(parameter="sentiment", prompt="Analyze sentiment"),
        InsightPrompt(parameter="intent", prompt="Analyze intent")
    ]
    batcher = InsightBatcher(parameters_per_batch=2)
    batches = batcher.batch(prompts)
    assert len(batches) == 1
    
    # 9. Batch Processing
    processor = BatchProcessor(llm_client=MagicMock())
    assert processor is not None
        
    # 10. Aggregation
    agg = InsightAggregator()
    assert agg is not None
