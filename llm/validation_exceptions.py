from .exceptions import LLMError


class LLMJSONParseError(LLMError):
    pass

class LLMSchemaValidationError(LLMError):
    pass

class MissingParametersError(LLMError):
    pass

class UnexpectedParametersError(LLMError):
    pass

class InvalidEvidenceError(LLMError):
    pass
