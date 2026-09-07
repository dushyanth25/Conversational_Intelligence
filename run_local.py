import json
import sys
from pathlib import Path

from llm.groq_client import GroqClient
from models.audio import AudioInput
from pipeline.alignment.service import AlignmentService
from pipeline.diarization.service import DiarizationService
from pipeline.insights.aggregator import InsightAggregator
from pipeline.insights.batch_processor import BatchProcessor
from pipeline.insights.batcher import InsightBatcher
from pipeline.insights.prompt_parser import PromptCSVParser
from pipeline.preprocessing.service import AudioPreprocessor
from pipeline.speaker_tagging.service import SpeakerTaggingService
from pipeline.transcript.service import TranscriptService
from pipeline.transcription.service import TranscriptionService
from pipeline.vad.service import VADService
from storage.databricks.sink import DatabricksSink


def run_pipeline(audio_file: str, prompt_file: str, call_id: str):
    print(f"Starting local pipeline execution for {audio_file}...")
    
    # 1. Provide an audio input object
    audio_input = AudioInput(
        call_id=call_id,
        audio_path=audio_file,
        prompt_sheet=prompt_file,
        language="en"
    )
    
    print("\n[1/10] Preprocessing Audio...")
    prep = AudioPreprocessor()
    audio_meta = prep.process(audio_input)
    print(f"Processed audio saved to: {audio_meta.processed_audio_path}")
    
    print("\n[2/10] Running VAD (Voice Activity Detection)...")
    vad = VADService()
    vad_res = vad.process(audio_meta)
    print(f"Detected {len(vad_res)} speech segments.")
    
    print("\n[3/10] Transcribing with faster-whisper...")
    trans = TranscriptionService()
    transcript_segments, transcript_meta = trans.process(audio_meta, vad_segments=vad_res)
    print(f"Transcription complete: {len(transcript_segments)} segments found.")
    
    print("\n[4/10] Diarizing with pyannote...")
    diarize = DiarizationService()
    diarization_segments, diarization_meta = diarize.process(audio_meta)
    print(f"Diarization complete: {len(diarization_segments)} speaker segments found.")
    
    print("\n[5/10] Aligning Transcripts and Speakers...")
    align = AlignmentService()
    aligned = align.process(call_id, transcript_segments, diarization_segments)
    
    print("\n[6/10] Tagging Speaker Roles (Agent/Customer)...")
    tag = SpeakerTaggingService()
    role_mappings = tag.process(call_id, aligned)
    
    print("\n[7/10] Generating Final CSV Transcript...")
    transcript_service = TranscriptService()
    out_dir = Path(f"artifacts/{call_id}")
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / "transcript.csv"
    json_path = out_dir / "transcript.json"
    canonical_conversation = transcript_service.process(call_id, aligned, role_mappings, str(csv_path), str(json_path))
    print(f"Transcript saved to {csv_path}")
    
    print("\n[8/10] Parsing Prompts & Batching...")
    parser = PromptCSVParser()
    prompt_set = parser.parse(Path(prompt_file))
    batcher = InsightBatcher(parameters_per_batch=3)
    batches = batcher.batch(prompt_set.prompts)
    print(f"Generated {len(batches)} batches for insights.")
    
    print("\n[9/10] Insight Processing (Calling Groq LLM)...")
    # Initialize Groq client
    llm = GroqClient()
    processor = BatchProcessor(llm_client=llm)
    
    batch_results = []
    for batch in batches:
        print(f"   Processing batch: {batch.batch_id} with {len(batch.parameters)} parameters...")
        result = processor.process_batch(call_id, canonical_conversation, batch)
        batch_results.append(result)
        
        # Avoid Groq rate limit (6000 TPM limit means we need ~20s to refill 2000 tokens)
        import time
        print("Sleeping for 25 seconds to respect Groq's 6000 TPM limit...")
        time.sleep(25)
        
    print("\n[10/10] Aggregating Final Insights...")
    aggregator = InsightAggregator()
    final_insights = aggregator.aggregate(
        call_id=call_id,
        conversation_metadata=canonical_conversation.metadata,
        expected_parameters=prompt_set.prompts,
        expected_batches=batches,
        batch_results=batch_results
    )
    
    print("\n✅ Pipeline Complete! Results:")
    print("================================")
    for insight in final_insights.insights:
        print(f"[{insight.parameter.upper()}]: {insight.result}")
        print(f" Confidence: {insight.confidence}")
        print(f" Evidence: {insight.evidence}")
        print("---")
        
    json_path = out_dir / "insights.json"
    with open(json_path, "w") as f:
        f.write(final_insights.model_dump_json(indent=2))
    print(f"Final JSON saved to {json_path}")
    
    print("\n[11/11] Saving to Databricks...")
    databricks_sink = DatabricksSink()
    with open(out_dir / "transcript.json", "r") as f:
        transcript_data = json.load(f)
        
    databricks_sink.save_insights_and_transcript(
        call_id=call_id,
        transcript_data=transcript_data,
        insights_data=final_insights.model_dump()
    )

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python run_local.py <path_to_wav> <path_to_csv> <call_id>")
        sys.exit(1)
    run_pipeline(sys.argv[1], sys.argv[2], sys.argv[3])
