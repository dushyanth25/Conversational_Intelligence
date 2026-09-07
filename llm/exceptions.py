class LLMError(Exception):
    pass

class LLMAuthenticationError(LLMError):
    pass

class LLMRateLimitError(LLMError):
    pass

class LLMTimeoutError(LLMError):
    pass

class LLMConnectionError(LLMError):
    pass

class LLMRequestError(LLMError):
    pass

class LLMResponseError(LLMError):
    pass
