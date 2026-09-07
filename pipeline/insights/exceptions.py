class InsightsError(Exception):
    pass

class PromptFileNotFoundError(InsightsError):
    pass

class PromptCSVValidationError(InsightsError):
    pass

class DuplicateParameterError(PromptCSVValidationError):
    pass

class EmptyPromptError(PromptCSVValidationError):
    pass

class MissingColumnError(PromptCSVValidationError):
    pass

class BatchProcessingError(InsightsError):
    pass
