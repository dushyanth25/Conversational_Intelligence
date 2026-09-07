class VADError(Exception):
    """Base exception for all VAD errors."""
    pass

class VADModelLoadError(VADError):
    pass

class VADInferenceError(VADError):
    pass

class VADAudioInvalidError(VADError):
    pass

class VADDisabledError(VADError):
    pass
