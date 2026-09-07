from llm.base import LLMClient
from llm.validation_models import InsightBatchResult
from models.conversation import Conversation
from pipeline.insights.batch_models import InsightBatch

from .batch_processor import BatchProcessor


class BatchService:
    def __init__(self, llm_client: LLMClient):
        self.processor = BatchProcessor(llm_client)
        
    def process(
        self, call_id: str, conversation: Conversation, batch: InsightBatch
    ) -> InsightBatchResult:
        return self.processor.process_batch(call_id, conversation, batch)
