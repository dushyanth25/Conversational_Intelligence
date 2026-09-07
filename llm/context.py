from abc import ABC, abstractmethod

from models.conversation import Conversation


class ConversationContext(ABC):
    @abstractmethod
    def get_context(self) -> str:
        pass


class FullTranscriptContext(ConversationContext):
    def __init__(self, conversation: Conversation, max_length: int):
        self.conversation = conversation
        self.max_length = max_length

    def get_context(self) -> str:
        lines = []
        for segment in self.conversation.segments:
            role = segment.speaker_role.value if segment.speaker_role else "UNKNOWN"
            start = f"{segment.start:.2f}"
            end = f"{segment.end:.2f}"
            lines.append(
                f"[{start} - {end}] {segment.speaker} ({role}): {segment.text}"
            )
        
        transcript = "\n".join(lines)
        if len(transcript) > self.max_length:
            raise ValueError(
                f"Transcript length {len(transcript)} exceeds maximum allowed "
                f"length {self.max_length}"
            )
        
        return transcript
