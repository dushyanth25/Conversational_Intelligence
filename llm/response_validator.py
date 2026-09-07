import logging

from pydantic import ValidationError

from models.conversation import Conversation
from models.insights import LLMResponse as BaseLLMResponse
from pipeline.insights.batch_models import InsightBatch

from .response_parser import ResponseParser
from .validation_exceptions import (
    InvalidEvidenceError,
    LLMSchemaValidationError,
    MissingParametersError,
    UnexpectedParametersError,
)
from .validation_models import InsightBatchResult

logger = logging.getLogger(__name__)

class ResponseValidator:
    def __init__(self):
        self.parser = ResponseParser()

    def validate(
        self, raw_text: str, batch: InsightBatch, conversation: Conversation
    ) -> InsightBatchResult:
        parsed_json = self.parser.parse(raw_text)
        
        try:
            validated_response = BaseLLMResponse(**parsed_json)
        except ValidationError as e:
            raise LLMSchemaValidationError(f"Schema validation failed: {e}") from e
            
        if not validated_response.results and batch.parameters:
            pass # this is fine, we check missing anyway
            
        expected_params = {p.parameter for p in batch.parameters}
        received_params_list = [r.parameter for r in validated_response.results]
        
        if len(received_params_list) != len(set(received_params_list)):
            raise UnexpectedParametersError("Duplicate parameters found in results")
            
        received_params = set(received_params_list)
        
        missing = expected_params - received_params
        if missing:
            raise MissingParametersError(f"Missing parameters: {missing}")
            
        unexpected = received_params - expected_params
        if unexpected:
            raise UnexpectedParametersError(f"Unexpected parameters: {unexpected}")
            
        transcript_segments = []
        for seg in conversation.segments:
            speaker = seg.speaker_role.value if seg.speaker_role else "UNKNOWN"
            transcript_segments.append({
                "speaker": speaker,
                "original_speaker": seg.speaker,
                "text": " ".join(seg.text.split()).lower()
            })
            
        for result in validated_response.results:
            for ev in result.evidence:
                norm_ev_text = " ".join(ev.text.split()).lower()
                norm_ev_speaker = ev.speaker
                
                found = False
                for t_seg in transcript_segments:
                    if (
                        t_seg["speaker"] == norm_ev_speaker
                        or t_seg["original_speaker"] == norm_ev_speaker
                    ):
                        if (
                            norm_ev_text in t_seg["text"] 
                            or t_seg["text"] in norm_ev_text
                        ):
                            found = True
                            break
                            
                if not found:
                    raise InvalidEvidenceError(
                        f"Evidence text '{ev.text}' not found in transcript for speaker '{ev.speaker}'"
                    )
                    
        logger.info(
            f"Validated {len(validated_response.results)} results for batch "
            f"{batch.batch_id}",
            extra={
                "call_id": conversation.call_id,
                "batch_id": batch.batch_id,
                "expected_parameter_count": len(expected_params),
                "received_parameter_count": len(received_params),
                "validation_status": "success",
                "error_type": None
            }
        )

        return InsightBatchResult(
            batch_id=batch.batch_id,
            call_id=conversation.call_id,
            results=validated_response.results,
            status="validated"
        )
