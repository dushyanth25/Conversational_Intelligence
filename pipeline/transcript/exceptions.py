class TranscriptError(Exception):
    """Base exception for all Transcript errors."""
    pass

class TranscriptValidationError(TranscriptError):
    pass

class TranscriptWriteError(TranscriptError):
    pass
