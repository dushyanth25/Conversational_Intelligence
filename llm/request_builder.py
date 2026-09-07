from config.settings import get_settings
from models.conversation import Conversation
from pipeline.insights.batch_models import InsightBatch

from .context import FullTranscriptContext
from .models import PromptRequest
from .prompt_builder import PromptBuilder


class RequestBuilder:
    def __init__(self):
        self.settings = get_settings()
        self.prompt_builder = PromptBuilder()
        self.max_length = getattr(self.settings, "MAX_TRANSCRIPT_LENGTH", 100000)

    def build_request(
        self, conversation: Conversation, batch: InsightBatch
    ) -> PromptRequest:
        context = FullTranscriptContext(conversation, self.max_length)
        transcript_text = context.get_context()
        
        system_prompt = self.prompt_builder.build_system_prompt()
        user_prompt = self.prompt_builder.build_user_prompt(transcript_text, batch)
        
        return PromptRequest(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            batch_id=batch.batch_id,
            call_id=conversation.call_id,
            model=self.settings.GROQ_MODEL,
        )
