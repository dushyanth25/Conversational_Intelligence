class PreprocessingError(Exception):
    """Base exception for all preprocessing errors."""
    pass

class AudioFileNotFoundError(PreprocessingError):
    """Raised when the input audio file does not exist."""
    pass

class UnsupportedAudioFormatError(PreprocessingError):
    """Raised when the audio format is not supported."""
    pass

class EmptyAudioFileError(PreprocessingError):
    """Raised when the audio file is empty."""
    pass

class CorruptedAudioError(PreprocessingError):
    """Raised when FFprobe cannot parse the audio file."""
    pass

class FFmpegNotInstalledError(PreprocessingError):
    """Raised when FFmpeg or FFprobe is not found on the system."""
    pass

class AudioProcessingError(PreprocessingError):
    """Raised when FFmpeg fails during conversion."""
    pass
