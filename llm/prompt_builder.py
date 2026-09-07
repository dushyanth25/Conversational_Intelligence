from pipeline.insights.batch_models import InsightBatch


class PromptBuilder:
    def build_system_prompt(self) -> str:
        return (
            "You are an AI assistant analyzing a conversation.\n"
            "You must follow each supplied parameter prompt precisely.\n"
            "Base your conclusions ONLY on the supplied transcript information.\n"
            "DO NOT fabricate evidence, timestamps, speaker names, quotes, or events.\n"
            "If sufficient evidence does not exist for a parameter, "
            "explicitly indicate that.\n"
            "You must return valid JSON in exactly this structure:\n"
            "{\n"
            '  "results": [\n'
            "    {\n"
            '      "parameter": "...",\n'
            '      "result": "...",\n'
            '      "confidence": 0.0,\n'
            '      "evidence": [\n'
            "        {\n"
            '          "timestamp": "...",\n'
            '          "speaker": "...",\n'
            '          "text": "..."\n'
            "        }\n"
            "      ]\n"
            "    }\n"
            "  ]\n"
            "}\n"
            "Confidence must be between 0.0 and 1.0.\n"
            "Each requested parameter must have exactly one result object."
        )

    def build_user_prompt(self, transcript: str, batch: InsightBatch) -> str:
        lines = ["CONVERSATION:", transcript, "", "REQUESTED INSIGHTS:"]
        
        for param in batch.parameters:
            lines.append("PARAMETER:")
            lines.append(param.parameter)
            lines.append("")
            lines.append("PROMPT:")
            lines.append(param.prompt)
            lines.append("")
            
        return "\n".join(lines).strip()
