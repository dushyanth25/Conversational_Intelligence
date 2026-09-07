import logging
from typing import List

from config.settings import get_settings

from .batch_exceptions import BatchValidationError
from .batch_models import InsightBatch
from .models import InsightPrompt

logger = logging.getLogger(__name__)


class InsightBatcher:
    def __init__(self, parameters_per_batch: int | None = None):
        settings = get_settings()
        self.batch_size = (
            parameters_per_batch
            if parameters_per_batch is not None
            else settings.PARAMETERS_PER_BATCH
        )

        if self.batch_size < 1:
            raise BatchValidationError(f"Invalid batch size: {self.batch_size}")

    def batch(self, prompts: List[InsightPrompt]) -> List[InsightBatch]:
        if prompts is None:
            raise BatchValidationError("Input prompts cannot be None")
        
        if not prompts:
            raise BatchValidationError("Empty parameter list")

        # Validate unique parameters and non-empty prompts
        seen = set()
        for i, prompt in enumerate(prompts):
            if not prompt.parameter:
                raise BatchValidationError(f"Prompt {i} missing parameter name")
            if not prompt.prompt:
                raise BatchValidationError(f"Prompt {i} missing prompt text")
            if prompt.parameter in seen:
                raise BatchValidationError(f"Duplicate parameter: {prompt.parameter}")
            seen.add(prompt.parameter)

        batches: List[InsightBatch] = []
        
        for i in range(0, len(prompts), self.batch_size):
            batch_num = (i // self.batch_size) + 1
            batch_id = f"batch_{batch_num:03d}"
            
            chunk = prompts[i:i + self.batch_size]
            
            batches.append(
                InsightBatch(
                    batch_id=batch_id,
                    parameters=chunk,
                )
            )

        logger.info(
            f"Batched {len(prompts)} parameters into {len(batches)} batches",
            extra={
                "module": "insights",
                "total_parameters": len(prompts),
                "total_batches": len(batches),
                "batch_size": self.batch_size,
            }
        )

        return batches
