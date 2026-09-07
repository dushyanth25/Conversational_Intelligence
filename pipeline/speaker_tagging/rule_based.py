import re
from collections import defaultdict
from typing import List

from models import AlignedSegment, SpeakerRole, SpeakerRoleMapping

from .base import SpeakerRoleClassifier


class RuleBasedRoleClassifier(SpeakerRoleClassifier):
    """
    A deterministic, rule-based role classifier.
    Assigns AGENT or CUSTOMER based on regex patterns of typical utterances.
    """

    def __init__(self):
        # Patterns typical for agents
        self.agent_patterns = [
            r"\b(thank you for calling|how may i help)\b",
            r"\b(how can i help|customer support)\b",
            r"\b(my name is|speaking|account number|verify your)\b",
            r"\b(happy to assist|transferring you|please hold)\b",
            r"\b(can i have your|could you confirm|apologize for the inconvenience)\b",
        ]
        
        # Patterns typical for customers
        self.customer_patterns = [
            r"\b(my order|i ordered|track my|refund|cancel my)\b",
            r"\b(i have a problem|i need help with|not working)\b",
            r"\b(where is my|why is my|i want to)\b",
        ]

        self.agent_regex = re.compile("|".join(self.agent_patterns), re.IGNORECASE)
        self.customer_regex = re.compile(
            "|".join(self.customer_patterns), re.IGNORECASE
        )

    def classify(self, segments: List[AlignedSegment]) -> List[SpeakerRoleMapping]:
        if not segments:
            return []

        speaker_scores = defaultdict(lambda: {"AGENT": 0, "CUSTOMER": 0})
        all_speakers = set()

        for segment in segments:
            speaker = segment.speaker
            if speaker == "UNKNOWN":
                continue
            
            all_speakers.add(speaker)
            text = segment.text

            # Simple heuristic scoring
            if self.agent_regex.search(text):
                speaker_scores[speaker]["AGENT"] += 1
            if self.customer_regex.search(text):
                speaker_scores[speaker]["CUSTOMER"] += 1

        mappings = []
        for speaker in all_speakers:
            agent_score = speaker_scores[speaker]["AGENT"]
            customer_score = speaker_scores[speaker]["CUSTOMER"]
            total_score = agent_score + customer_score

            if total_score == 0:
                mappings.append(
                    SpeakerRoleMapping(
                        speaker=speaker, role=SpeakerRole.UNKNOWN, confidence=0.0
                    )
                )
            else:
                # Basic confidence based on matched rules ratio
                if agent_score > customer_score:
                    confidence = agent_score / total_score
                    mappings.append(
                        SpeakerRoleMapping(
                            speaker=speaker, 
                            role=SpeakerRole.AGENT, 
                            confidence=confidence
                        )
                    )
                elif customer_score > agent_score:
                    confidence = customer_score / total_score
                    mappings.append(
                        SpeakerRoleMapping(
                            speaker=speaker, 
                            role=SpeakerRole.CUSTOMER, 
                            confidence=confidence
                        )
                    )
                else:
                    # Tie
                    mappings.append(
                        SpeakerRoleMapping(
                            speaker=speaker, role=SpeakerRole.UNKNOWN, confidence=0.5
                        )
                    )

        # Ensure we don't accidentally return empty list if all segments were UNKNOWN
        for segment in segments:
            known_speakers = [m.speaker for m in mappings]
            if segment.speaker == "UNKNOWN" and "UNKNOWN" not in known_speakers:
                mappings.append(
                    SpeakerRoleMapping(
                        speaker="UNKNOWN", role=SpeakerRole.UNKNOWN, confidence=1.0
                    )
                )

        return mappings
