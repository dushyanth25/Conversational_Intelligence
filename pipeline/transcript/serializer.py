import logging
from pathlib import Path

from models import Conversation

from .exceptions import TranscriptWriteError

logger = logging.getLogger(__name__)

class JSONSerializer:
    def serialize(self, conversation: Conversation) -> str:
        return conversation.model_dump_json(indent=2)

    def write(self, conversation: Conversation, output_path: str | Path) -> None:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self.serialize(conversation))
                
            logger.info(
                f"Successfully wrote JSON transcript to {path}",
                extra={
                    "call_id": conversation.call_id,
                    "pipeline_module": "transcript",
                    "file_path": str(path),
                },
            )
        except Exception as e:
            raise TranscriptWriteError(f"Failed to write JSON: {e}") from e
