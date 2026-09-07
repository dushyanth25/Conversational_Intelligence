class DiarizationError(Exception):
    """Base exception for all Diarization errors."""
    pass

class DiarizationModelLoadError(DiarizationError):
    pass

class DiarizationAuthError(DiarizationError):
    pass

class DiarizationInferenceError(DiarizationError):
    pass

class DiarizationAudioInvalidError(DiarizationError):
    pass
