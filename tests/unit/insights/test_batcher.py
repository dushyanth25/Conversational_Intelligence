import pytest

from pipeline.insights.batch_exceptions import BatchValidationError
from pipeline.insights.batcher import InsightBatcher
from pipeline.insights.models import InsightPrompt


def make_prompts(count: int):
    return [
        InsightPrompt(parameter=f"param_{i}", prompt=f"Prompt {i}")
        for i in range(count)
    ]

def test_batch_3_params_size_3():
    batcher = InsightBatcher(parameters_per_batch=3)
    batches = batcher.batch(make_prompts(3))
    assert len(batches) == 1
    assert batches[0].batch_id == "batch_001"
    assert len(batches[0].parameters) == 3

def test_batch_6_params_size_3():
    batcher = InsightBatcher(parameters_per_batch=3)
    batches = batcher.batch(make_prompts(6))
    assert len(batches) == 2
    assert batches[0].batch_id == "batch_001"
    assert batches[1].batch_id == "batch_002"
    assert len(batches[0].parameters) == 3
    assert len(batches[1].parameters) == 3

def test_batch_7_params_size_3():
    batcher = InsightBatcher(parameters_per_batch=3)
    batches = batcher.batch(make_prompts(7))
    assert len(batches) == 3
    assert len(batches[0].parameters) == 3
    assert len(batches[1].parameters) == 3
    assert len(batches[2].parameters) == 1

def test_batch_10_params_size_3():
    batcher = InsightBatcher(parameters_per_batch=3)
    batches = batcher.batch(make_prompts(10))
    assert len(batches) == 4
    assert len(batches[3].parameters) == 1

def test_batch_size_1():
    batcher = InsightBatcher(parameters_per_batch=1)
    batches = batcher.batch(make_prompts(3))
    assert len(batches) == 3
    assert batches[0].batch_id == "batch_001"
    assert batches[1].batch_id == "batch_002"
    assert batches[2].batch_id == "batch_003"

def test_batch_size_larger_than_count():
    batcher = InsightBatcher(parameters_per_batch=10)
    batches = batcher.batch(make_prompts(3))
    assert len(batches) == 1
    assert len(batches[0].parameters) == 3

def test_empty_parameter_list():
    batcher = InsightBatcher()
    with pytest.raises(BatchValidationError, match="Empty parameter list"):
        batcher.batch([])

def test_none_input():
    batcher = InsightBatcher()
    with pytest.raises(BatchValidationError, match="Input prompts cannot be None"):
        batcher.batch(None)

def test_invalid_batch_size():
    with pytest.raises(BatchValidationError, match="Invalid batch size"):
        InsightBatcher(parameters_per_batch=0)

def test_duplicate_parameter():
    batcher = InsightBatcher()
    prompts = make_prompts(2)
    prompts[1].parameter = prompts[0].parameter
    with pytest.raises(BatchValidationError, match="Duplicate parameter"):
        batcher.batch(prompts)

def test_ordering_preservation():
    batcher = InsightBatcher(parameters_per_batch=2)
    prompts = make_prompts(4)
    batches = batcher.batch(prompts)
    assert batches[0].parameters[0].parameter == "param_0"
    assert batches[0].parameters[1].parameter == "param_1"
    assert batches[1].parameters[0].parameter == "param_2"
    assert batches[1].parameters[1].parameter == "param_3"

def test_deterministic_batch_ids():
    batcher = InsightBatcher(parameters_per_batch=2)
    prompts = make_prompts(4)
    batches = batcher.batch(prompts)
    assert batches[0].batch_id == "batch_001"
    assert batches[1].batch_id == "batch_002"

def test_default_config():
    batcher = InsightBatcher()
    # By default, Settings has PARAMETERS_PER_BATCH = 3
    assert batcher.batch_size == 3
