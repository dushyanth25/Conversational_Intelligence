import pytest

from pipeline.insights.exceptions import (
    DuplicateParameterError,
    EmptyPromptError,
    MissingColumnError,
    PromptCSVValidationError,
    PromptFileNotFoundError,
)
from pipeline.insights.prompt_parser import PromptCSVParser


def test_valid_csv(tmp_path):
    f = tmp_path / "valid.csv"
    f.write_text(
        "parameter,prompt\nsentiment,analyze sentiment\nintent,analyze intent", 
        encoding="utf-8"
    )
    parser = PromptCSVParser()
    result = parser.parse(f)
    assert result.count == 2
    assert result.prompts[0].parameter == "sentiment"
    assert result.prompts[1].parameter == "intent"

def test_empty_csv(tmp_path):
    f = tmp_path / "empty.csv"
    f.write_text("", encoding="utf-8")
    parser = PromptCSVParser()
    with pytest.raises(PromptCSVValidationError):
        parser.parse(f)

def test_missing_file(tmp_path):
    parser = PromptCSVParser()
    with pytest.raises(PromptFileNotFoundError):
        parser.parse(tmp_path / "does_not_exist.csv")

def test_missing_parameter_column(tmp_path):
    f = tmp_path / "missing.csv"
    f.write_text("prompt\nanalyze something", encoding="utf-8")
    parser = PromptCSVParser()
    with pytest.raises(MissingColumnError):
        parser.parse(f)

def test_missing_prompt_column(tmp_path):
    f = tmp_path / "missing.csv"
    f.write_text("parameter\nsentiment", encoding="utf-8")
    parser = PromptCSVParser()
    with pytest.raises(MissingColumnError):
        parser.parse(f)

def test_empty_parameter(tmp_path):
    f = tmp_path / "empty_param.csv"
    f.write_text("parameter,prompt\n,analyze something", encoding="utf-8")
    parser = PromptCSVParser()
    with pytest.raises(EmptyPromptError):
        parser.parse(f)

def test_empty_prompt(tmp_path):
    f = tmp_path / "empty_prompt.csv"
    f.write_text("parameter,prompt\nsentiment,", encoding="utf-8")
    parser = PromptCSVParser()
    with pytest.raises(EmptyPromptError):
        parser.parse(f)

def test_duplicate_parameter(tmp_path):
    f = tmp_path / "dup.csv"
    f.write_text(
        "parameter,prompt\nsentiment,analyze\nsentiment,analyze again", 
        encoding="utf-8"
    )
    parser = PromptCSVParser()
    with pytest.raises(DuplicateParameterError):
        parser.parse(f)

def test_quoted_prompt(tmp_path):
    f = tmp_path / "quoted.csv"
    f.write_text('parameter,prompt\nsentiment,"Analyze, with commas"', encoding="utf-8")
    parser = PromptCSVParser()
    result = parser.parse(f)
    assert result.prompts[0].prompt == "Analyze, with commas"

def test_prompt_containing_commas(tmp_path):
    f = tmp_path / "commas.csv"
    f.write_text('parameter,prompt\nintent,"hello, world, test"', encoding="utf-8")
    parser = PromptCSVParser()
    result = parser.parse(f)
    assert result.prompts[0].prompt == "hello, world, test"

def test_unicode_prompt(tmp_path):
    f = tmp_path / "unicode.csv"
    f.write_text("parameter,prompt\nsentiment,😊", encoding="utf-8")
    parser = PromptCSVParser()
    result = parser.parse(f)
    assert result.prompts[0].prompt == "😊"

def test_tamil_prompt(tmp_path):
    f = tmp_path / "tamil.csv"
    f.write_text("parameter,prompt\nsentiment,வணக்கம்", encoding="utf-8")
    parser = PromptCSVParser()
    result = parser.parse(f)
    assert result.prompts[0].prompt == "வணக்கம்"

def test_windows_line_endings(tmp_path):
    f = tmp_path / "win.csv"
    f.write_bytes(b"parameter,prompt\r\nsentiment,test\r\n")
    parser = PromptCSVParser()
    result = parser.parse(f)
    assert result.prompts[0].prompt == "test"

def test_linux_line_endings(tmp_path):
    f = tmp_path / "linux.csv"
    f.write_bytes(b"parameter,prompt\nsentiment,test\n")
    parser = PromptCSVParser()
    result = parser.parse(f)
    assert result.prompts[0].prompt == "test"

def test_whitespace_normalization(tmp_path):
    f = tmp_path / "ws.csv"
    f.write_text(" parameter , prompt \n  sentiment  ,  test  \n", encoding="utf-8")
    parser = PromptCSVParser()
    result = parser.parse(f)
    assert result.prompts[0].parameter == "sentiment"
    assert result.prompts[0].prompt == "test"

def test_original_row_ordering(tmp_path):
    f = tmp_path / "order.csv"
    f.write_text("parameter,prompt\nb,2\na,1\nc,3", encoding="utf-8")
    parser = PromptCSVParser()
    result = parser.parse(f)
    assert result.prompts[0].parameter == "b"
    assert result.prompts[1].parameter == "a"
    assert result.prompts[2].parameter == "c"
