from .exceptions import InsightsError


class AggregationError(InsightsError):
    pass

class DuplicateBatchError(AggregationError):
    pass

class DuplicateParameterError(AggregationError):
    pass

class InconsistentCallIdError(AggregationError):
    pass

class UnexpectedParameterError(AggregationError):
    pass
