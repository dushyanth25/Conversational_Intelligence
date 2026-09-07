import json
import logging
import subprocess
from pathlib import Path
from typing import Any, Dict

from .exceptions import (
    AudioProcessingError,
    CorruptedAudioError,
    FFmpegNotInstalledError,
)

logger = logging.getLogger(__name__)


def check_dependencies() -> None:
    """Check if ffmpeg and ffprobe are installed."""
    try:
        subprocess.run(
            ["ffmpeg", "-version"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )
        subprocess.run(
            ["ffprobe", "-version"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError) as e:
        raise FFmpegNotInstalledError("FFmpeg or FFprobe is not installed.") from e


def get_metadata(file_path: Path) -> Dict[str, Any]:
    """Extract audio metadata using FFprobe."""
    cmd = [
        "ffprobe",
        "-v",
        "quiet",
        "-print_format",
        "json",
        "-show_format",
        "-show_streams",
        str(file_path),
    ]
    try:
        result = subprocess.run(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True
        )
        metadata = json.loads(result.stdout)

        # If no streams or format, it might be corrupted
        if "format" not in metadata or not metadata.get("streams"):
            raise CorruptedAudioError(
                f"File {file_path} appears corrupted or has no audio streams."
            )

        return metadata
    except subprocess.CalledProcessError as e:
        logger.error(
            f"FFprobe failed for {file_path}: {e.stderr}",
            extra={"input_filename": file_path.name, "error": e.stderr},
        )
        raise CorruptedAudioError(
            "Failed to extract metadata. The file may be corrupted."
        ) from e
    except json.JSONDecodeError as e:
        raise CorruptedAudioError("Failed to parse ffprobe output.") from e


def convert_audio(
    input_path: Path, output_path: Path, sample_rate: int, channels: int
) -> None:
    """Convert audio to the normalized format (WAV, PCM)."""
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(input_path),
        "-ac",
        str(channels),
        "-ar",
        str(sample_rate),
        "-c:a",
        "pcm_s16le",
        str(output_path),
    ]
    try:
        subprocess.run(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True
        )
    except subprocess.CalledProcessError as e:
        logger.error(
            f"FFmpeg conversion failed for {input_path}: {e.stderr}",
            extra={"input_filename": input_path.name, "error": e.stderr},
        )
        raise AudioProcessingError(f"Audio conversion failed: {e.stderr}") from e
