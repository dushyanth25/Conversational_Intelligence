import pytest

from llm.validation_models import InsightBatchResult
from models.insights import InsightResult
from pipeline.insights.aggregation_exceptions import (
    DuplicateBatchError,
    DuplicateParameterError,
    InconsistentCallIdError,
    UnexpectedParameterError,
)
from pipeline.insights.aggregator import InsightAggregator
from pipeline.insights.batch_models import InsightBatch
from pipeline.insights.models import InsightPrompt


def create_prompt(name):
    return InsightPrompt(parameter=name, prompt=f"Check {name}")


def create_result(name):
    return InsightResult(parameter=name, result="val", confidence=1.0, evidence=[])


def test_one_batch():
    agg = InsightAggregator()
    expected_params = [create_prompt("p1")]
    expected_batches = [InsightBatch(batch_id="B1", parameters=expected_params)]
    batch_results = [
        InsightBatchResult(
            batch_id="B1",
            call_id="C1",
            results=[create_result("p1")],
            status="VALIDATED",
        )
    ]

    res = agg.aggregate("C1", {}, expected_params, expected_batches, batch_results)

    assert res.status == "COMPLETE"
    assert len(res.insights) == 1
    assert res.insights[0].parameter == "p1"
    assert "B1" in res.successful_batches
    assert not res.failed_batches
    assert not res.missing_batches


def test_multiple_batches():
    agg = InsightAggregator()
    expected_params = [create_prompt("p1"), create_prompt("p2")]
    expected_batches = [
        InsightBatch(batch_id="B1", parameters=[expected_params[0]]),
        InsightBatch(batch_id="B2", parameters=[expected_params[1]]),
    ]
    batch_results = [
        InsightBatchResult(
            batch_id="B1",
            call_id="C1",
            results=[create_result("p1")],
            status="VALIDATED",
        ),
        InsightBatchResult(
            batch_id="B2",
            call_id="C1",
            results=[create_result("p2")],
            status="VALIDATED",
        ),
    ]

    res = agg.aggregate("C1", {}, expected_params, expected_batches, batch_results)

    assert res.status == "COMPLETE"
    assert len(res.insights) == 2
    assert res.insights[0].parameter == "p1"
    assert res.insights[1].parameter == "p2"


def test_missing_batch():
    agg = InsightAggregator()
    expected_params = [create_prompt("p1"), create_prompt("p2")]
    expected_batches = [
        InsightBatch(batch_id="B1", parameters=[expected_params[0]]),
        InsightBatch(batch_id="B2", parameters=[expected_params[1]]),
    ]
    batch_results = [
        InsightBatchResult(
            batch_id="B1",
            call_id="C1",
            results=[create_result("p1")],
            status="VALIDATED",
        )
    ]

    res = agg.aggregate("C1", {}, expected_params, expected_batches, batch_results)

    assert res.status == "PARTIAL"
    assert len(res.insights) == 1
    assert "B2" in res.missing_batches


def test_duplicate_batch():
    agg = InsightAggregator()
    expected_params = [create_prompt("p1")]
    expected_batches = [InsightBatch(batch_id="B1", parameters=expected_params)]
    batch_results = [
        InsightBatchResult(
            batch_id="B1",
            call_id="C1",
            results=[create_result("p1")],
            status="VALIDATED",
        ),
        InsightBatchResult(
            batch_id="B1",
            call_id="C1",
            results=[create_result("p1")],
            status="VALIDATED",
        ),
    ]

    with pytest.raises(DuplicateBatchError):
        agg.aggregate("C1", {}, expected_params, expected_batches, batch_results)


def test_duplicate_parameter():
    agg = InsightAggregator()
    expected_params = [create_prompt("p1")]
    expected_batches = [
        InsightBatch(batch_id="B1", parameters=expected_params),
        InsightBatch(batch_id="B2", parameters=[]),
    ]
    batch_results = [
        InsightBatchResult(
            batch_id="B1",
            call_id="C1",
            results=[create_result("p1")],
            status="VALIDATED",
        ),
        InsightBatchResult(
            batch_id="B2",
            call_id="C1",
            results=[create_result("p1")],
            status="VALIDATED",
        ),
    ]

    with pytest.raises(DuplicateParameterError):
        agg.aggregate("C1", {}, expected_params, expected_batches, batch_results)


def test_unexpected_parameter():
    agg = InsightAggregator()
    expected_params = [create_prompt("p1")]
    expected_batches = [InsightBatch(batch_id="B1", parameters=expected_params)]
    batch_results = [
        InsightBatchResult(
            batch_id="B1",
            call_id="C1",
            results=[create_result("p2")],
            status="VALIDATED",
        )
    ]

    with pytest.raises(UnexpectedParameterError):
        agg.aggregate("C1", {}, expected_params, expected_batches, batch_results)


def test_empty_results():
    agg = InsightAggregator()
    expected_params = [create_prompt("p1")]
    expected_batches = [InsightBatch(batch_id="B1", parameters=expected_params)]
    batch_results = [
        InsightBatchResult(batch_id="B1", call_id="C1", results=[], status="VALIDATED")
    ]

    res = agg.aggregate("C1", {}, expected_params, expected_batches, batch_results)
    assert res.status == "FAILED"
    assert len(res.insights) == 0


def test_failed_batch():
    agg = InsightAggregator()
    expected_params = [create_prompt("p1")]
    expected_batches = [InsightBatch(batch_id="B1", parameters=expected_params)]
    batch_results = [
        InsightBatchResult(
            batch_id="B1",
            call_id="C1",
            results=[],
            status="FAILED",
            error_type="LLMTimeout",
        )
    ]

    res = agg.aggregate("C1", {}, expected_params, expected_batches, batch_results)

    assert res.status == "FAILED"
    assert len(res.failed_batches) == 1
    assert res.failed_batches[0].error_type == "LLMTimeout"


def test_partial_result():
    agg = InsightAggregator()
    expected_params = [create_prompt("p1"), create_prompt("p2")]
    expected_batches = [
        InsightBatch(batch_id="B1", parameters=[expected_params[0]]),
        InsightBatch(batch_id="B2", parameters=[expected_params[1]]),
    ]
    batch_results = [
        InsightBatchResult(
            batch_id="B1",
            call_id="C1",
            results=[create_result("p1")],
            status="VALIDATED",
        ),
        InsightBatchResult(
            batch_id="B2",
            call_id="C1",
            results=[],
            status="FAILED",
            error_type="ParseError",
        ),
    ]

    res = agg.aggregate("C1", {}, expected_params, expected_batches, batch_results)

    assert res.status == "PARTIAL"
    assert len(res.insights) == 1


def test_parameter_ordering():
    agg = InsightAggregator()
    expected_params = [create_prompt("p1"), create_prompt("p2"), create_prompt("p3")]
    expected_batches = [InsightBatch(batch_id="B1", parameters=expected_params)]
    batch_results = [
        InsightBatchResult(
            batch_id="B1",
            call_id="C1",
            results=[create_result("p3"), create_result("p1"), create_result("p2")],
            status="VALIDATED",
        )
    ]

    res = agg.aggregate("C1", {}, expected_params, expected_batches, batch_results)

    assert res.insights[0].parameter == "p1"
    assert res.insights[1].parameter == "p2"
    assert res.insights[2].parameter == "p3"


def test_multiple_calls_cannot_be_mixed():
    agg = InsightAggregator()
    expected_params = [create_prompt("p1")]
    expected_batches = [InsightBatch(batch_id="B1", parameters=expected_params)]
    batch_results = [
        InsightBatchResult(
            batch_id="B1",
            call_id="C2",
            results=[create_result("p1")],
            status="VALIDATED",
        )
    ]

    with pytest.raises(InconsistentCallIdError):
        agg.aggregate("C1", {}, expected_params, expected_batches, batch_results)


def test_deterministic_output():
    agg = InsightAggregator()
    expected_params = [create_prompt("p1")]
    expected_batches = [InsightBatch(batch_id="B1", parameters=expected_params)]
    batch_results = [
        InsightBatchResult(
            batch_id="B1",
            call_id="C1",
            results=[create_result("p1")],
            status="VALIDATED",
        )
    ]

    res1 = agg.aggregate("C1", {}, expected_params, expected_batches, batch_results)
    res2 = agg.aggregate("C1", {}, expected_params, expected_batches, batch_results)

    d1 = res1.model_dump(exclude={"created_at"})
    d2 = res2.model_dump(exclude={"created_at"})
    assert d1 == d2
