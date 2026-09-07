import csv
import logging
import time
from pathlib import Path
from typing import List

from .exceptions import (
    DuplicateParameterError,
    EmptyPromptError,
    InsightsError,
    MissingColumnError,
    PromptCSVValidationError,
    PromptFileNotFoundError,
)
from .models import InsightPrompt, InsightPromptSet

logger = logging.getLogger(__name__)

class PromptCSVParser:
    def parse(self, file_path: str | Path) -> InsightPromptSet:
        path = Path(file_path)
        
        start_time = time.time()
        
        if not path.exists():
            raise PromptFileNotFoundError(f"Prompt CSV not found: {path}")
        if not path.is_file():
            raise PromptFileNotFoundError(f"Path is not a file: {path}")

        prompts: List[InsightPrompt] = []
        seen_parameters = set()

        try:
            with open(path, "r", encoding="utf-8-sig") as f:
                reader = csv.reader(f)
                
                try:
                    header = next(reader)
                except StopIteration:
                    raise PromptCSVValidationError(f"Empty CSV file: {path}") from None
                
                header = [h.strip().lower() for h in header if h.strip()]
                
                if "parameter" not in header:
                    raise MissingColumnError("Missing 'parameter' column in CSV")
                if "prompt" not in header:
                    raise MissingColumnError("Missing 'prompt' column in CSV")
                
                param_idx = header.index("parameter")
                prompt_idx = header.index("prompt")

                for row_idx, row in enumerate(reader, start=2):
                    if not row or not any(row):
                        continue
                    
                    if len(row) <= max(param_idx, prompt_idx):
                        raise PromptCSVValidationError(f"Row {row_idx} is malformed")

                    parameter = row[param_idx].strip()
                    prompt = row[prompt_idx].strip()
                    
                    if not parameter:
                        raise EmptyPromptError(f"Empty parameter on row {row_idx}")
                    if not prompt:
                        raise EmptyPromptError(f"Empty prompt on row {row_idx}")
                    
                    if parameter in seen_parameters:
                        raise DuplicateParameterError(
                            f"Duplicate parameter found: {parameter}"
                        )
                    
                    seen_parameters.add(parameter)
                    prompts.append(InsightPrompt(parameter=parameter, prompt=prompt))
                    
        except InsightsError:
            raise
        except Exception as e:
            raise PromptCSVValidationError(f"Failed to parse CSV: {e}") from e

        duration = time.time() - start_time
        
        logger.info(
            f"Parsed {len(prompts)} insights from {path}",
            extra={
                "module": "insights",
                "source_file": str(path),
                "parameter_count": len(prompts),
                "status": "success",
                "processing_duration": duration,
            }
        )

        return InsightPromptSet(
            prompts=prompts,
            count=len(prompts),
            source_file=str(path)
        )
