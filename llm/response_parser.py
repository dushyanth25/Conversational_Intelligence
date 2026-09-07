import json
import re
from typing import Any, Dict

from .validation_exceptions import LLMJSONParseError


class ResponseParser:
    def parse(self, raw_text: str) -> Dict[str, Any]:
        text = raw_text.strip()
        
        match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
        if match:
            text = match.group(1).strip()
        elif text.startswith("{") and text.endswith("}"):
            pass # already looks like a json object
        elif text.startswith("[") and text.endswith("]"):
            pass # looks like a list
        else:
            match = re.search(r'(\{.*\})', text, re.DOTALL)
            if match:
                text = match.group(1).strip()
            
        try:
            parsed = json.loads(text)
            if not isinstance(parsed, dict):
                raise LLMJSONParseError("Parsed JSON is not an object")
            return parsed
        except json.JSONDecodeError as e:
            raise LLMJSONParseError(f"Failed to parse JSON: {e}") from e
