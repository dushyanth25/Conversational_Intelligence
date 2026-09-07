import logging
import time

from llm.base import LLMClient
from llm.exceptions import LLMError
from llm.request_builder import RequestBuilder
from llm.response_validator import ResponseValidator
from llm.validation_exceptions import (
    InvalidEvidenceError,
    LLMJSONParseError,
    LLMSchemaValidationError,
    MissingParametersError,
    UnexpectedParametersError,
)
from llm.validation_models import InsightBatchResult
from models.conversation import Conversation
from pipeline.insights.batch_models import InsightBatch

from .exceptions import BatchProcessingError

logger = logging.getLogger(__name__)

class BatchProcessor:
    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client
        self.request_builder = RequestBuilder()
        self.validator = ResponseValidator()

    def process_batch(
        self, call_id: str, conversation: Conversation, batch: InsightBatch
    ) -> InsightBatchResult:
        start_time = time.time()
        status = "PROCESSING"
        error_type = None
        results = []

        logger.info(
            f"Starting processing for batch {batch.batch_id} of call {call_id}",
            extra={
                "call_id": call_id,
                "batch_id": batch.batch_id,
                "parameter_count": len(batch.parameters),
                "status": status,
            }
        )

        try:
            prompt_req = self.request_builder.build_request(conversation, batch)
            
            llm_response = self.llm_client.generate(
                system_prompt=prompt_req.system_prompt,
                user_prompt=prompt_req.user_prompt,
                model=prompt_req.model,
                response_format={"type": "json_object"}
            )
            
            validated_batch_result = self.validator.validate(
                raw_text=llm_response.content,
                batch=batch,
                conversation=conversation
            )
            
            status = "VALIDATED"
            results = validated_batch_result.results
            
        except (
            LLMJSONParseError, 
            LLMSchemaValidationError, 
            MissingParametersError, 
            UnexpectedParametersError, 
            InvalidEvidenceError
        ) as e:
            status = "FAILED"
            error_type = type(e).__name__
            logger.error(f"Validation Error processing batch {batch.batch_id}: {e}")
            raise BatchProcessingError(f"Validation Error: {e}") from e
        except LLMError as e:
            status = "FAILED"
            error_type = type(e).__name__
            logger.error(f"LLM Error processing batch {batch.batch_id}: {e}")
            raise BatchProcessingError(f"LLM Error: {e}") from e
        except Exception as e:
            status = "FAILED"
            error_type = type(e).__name__
            logger.error(f"Unexpected error processing batch {batch.batch_id}: {e}")
            raise BatchProcessingError(f"Unexpected error: {e}") from e
        finally:
            end_time = time.time()
            logger.info(
                f"Finished processing batch {batch.batch_id} for call {call_id}",
                extra={
                    "call_id": call_id,
                    "batch_id": batch.batch_id,
                    "status": status,
                    "error_type": error_type,
                    "start_time": start_time,
                    "end_time": end_time,
                    "duration": end_time - start_time,
                }
            )
            
        return InsightBatchResult(
            batch_id=batch.batch_id,
            call_id=call_id,
            results=results,
            status=status
        )
