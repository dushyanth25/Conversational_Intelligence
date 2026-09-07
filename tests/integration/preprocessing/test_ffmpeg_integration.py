import subprocess

import pytest

from pipeline.preprocessing import ffmpeg


def has_ffmpeg():
    try:
        subprocess.run(
            ["ffmpeg", "-version"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False

pytestmark = pytest.mark.skipif(not has_ffmpeg(), reason="FFmpeg is not installed")

def test_ffmpeg_dependencies():
    """Test that check_dependencies runs without errors when ffmpeg is present."""
    ffmpeg.check_dependencies()
