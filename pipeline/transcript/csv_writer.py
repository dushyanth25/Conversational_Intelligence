import csv
import logging
from pathlib import Path

from models import Conversation

from .exceptions import TranscriptWriteError

logger = logging.getLogger(__name__)

def format_timestamp(seconds: float) -> str:
    """Format seconds into HH:MM:SS."""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    return f"{h:02d}:{m:02d}:{s:02d}"

class CSVWriter:
    def write(self, conversation: Conversation, output_path: str | Path) -> None:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(path, "w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["timestamp", "speaker", "transcript"])

                for segment in conversation.segments:
                    ts = format_timestamp(segment.start)
                    # The CSV speaker field contains the resolved conversational role
                    # where available, else UNKNOWN.
                    role = (
                        segment.speaker_role.value 
                        if segment.speaker_role else "UNKNOWN"
                    )
                    writer.writerow([ts, role, segment.text])

            logger.info(
                f"Successfully wrote CSV transcript to {path}",
                extra={
                    "call_id": conversation.call_id,
                    "pipeline_module": "transcript",
                    "file_path": str(path),
                },
            )
        except Exception as e:
            raise TranscriptWriteError(f"Failed to write CSV: {e}") from e
