from datetime import datetime, timezone
from typing import Any, List, Set

from llm.validation_models import InsightBatchResult
from pipeline.insights.batch_models import InsightBatch
from pipeline.insights.models import InsightPrompt

from .aggregation_exceptions import (
    DuplicateBatchError,
    DuplicateParameterError,
    InconsistentCallIdError,
    UnexpectedParameterError,
)
from .aggregation_models import FailedBatchInfo, FinalInsightResult


class InsightAggregator:
    def aggregate(
        self,
        call_id: str,
        conversation_metadata: Any,
        expected_parameters: List[InsightPrompt],
        expected_batches: List[InsightBatch],
        batch_results: List[InsightBatchResult],
    ) -> FinalInsightResult:

        expected_param_names = [p.parameter for p in expected_parameters]
        expected_batch_ids = [b.batch_id for b in expected_batches]

        seen_batches: Set[str] = set()
        seen_params: Set[str] = set()

        successful_batches = []
        failed_batches = []

        insights_by_param = {}

        for br in batch_results:
            if br.call_id != call_id:
                raise InconsistentCallIdError(
                    f"Batch {br.batch_id} has inconsistent call_id: "
                    f"{br.call_id} != {call_id}"
                )

            if br.batch_id in seen_batches:
                raise DuplicateBatchError(f"Duplicate batch ID received: {br.batch_id}")
            seen_batches.add(br.batch_id)

            if br.status == "FAILED":
                failed_batches.append(
                    FailedBatchInfo(
                        batch_id=br.batch_id, error_type=br.error_type or "UnknownError"
                    )
                )
                continue

            successful_batches.append(br.batch_id)

            for result in br.results:
                param = result.parameter
                if param not in expected_param_names:
                    raise UnexpectedParameterError(
                        f"Unexpected parameter received: {param}"
                    )

                if param in seen_params:
                    raise DuplicateParameterError(
                        f"Duplicate parameter received: {param}"
                    )
                seen_params.add(param)

                insights_by_param[param] = result

        missing_batches = [b for b in expected_batch_ids if b not in seen_batches]

        if missing_batches or failed_batches:
            if not seen_params:
                status = "FAILED"
            else:
                status = "PARTIAL"
        else:
            if not seen_params and expected_param_names:
                status = "FAILED"
            else:
                status = "COMPLETE"

        final_insights = []
        for p in expected_param_names:
            if p in insights_by_param:
                final_insights.append(insights_by_param[p])

        return FinalInsightResult(
            call_id=call_id,
            status=status,
            total_parameters=len(expected_param_names),
            successful_batches=successful_batches,
            failed_batches=failed_batches,
            missing_batches=missing_batches,
            insights=final_insights,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
