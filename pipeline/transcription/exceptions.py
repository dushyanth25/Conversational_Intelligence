class ASRError(Exception):
    """Base exception for all ASR errors."""
    pass

class ASRModelLoadError(ASRError):
    pass

class ASRInferenceError(ASRError):
    pass

class ASRAudioInvalidError(ASRError):
    pass
