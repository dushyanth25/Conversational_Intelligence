
from models import AlignedSegment, SpeakerRole
from pipeline.speaker_tagging.base import SpeakerRoleClassifier
from pipeline.speaker_tagging.rule_based import RuleBasedRoleClassifier
from pipeline.speaker_tagging.service import SpeakerTaggingService


def seg(speaker, text):
    return AlignedSegment(
        start=0.0, end=1.0, speaker=speaker, text=text, confidence=1.0, language="en"
    )

def test_clear_agent():
    classifier = RuleBasedRoleClassifier()
    segments = [
        seg("SPEAKER_00", "Thank you for calling customer support. How can I help?"),
        seg("SPEAKER_00", "Please hold while I verify your account number.")
    ]
    mappings = classifier.classify(segments)
    assert len(mappings) == 1
    assert mappings[0].speaker == "SPEAKER_00"
    assert mappings[0].role == SpeakerRole.AGENT
    assert mappings[0].confidence == 1.0

def test_clear_customer():
    classifier = RuleBasedRoleClassifier()
    segments = [
        seg("SPEAKER_01", "I ordered a laptop but it's not working."),
        seg("SPEAKER_01", "I want to cancel my subscription.")
    ]
    mappings = classifier.classify(segments)
    assert len(mappings) == 1
    assert mappings[0].speaker == "SPEAKER_01"
    assert mappings[0].role == SpeakerRole.CUSTOMER
    assert mappings[0].confidence == 1.0

def test_two_speaker_conversation():
    classifier = RuleBasedRoleClassifier()
    segments = [
        seg("SPEAKER_00", "Thank you for calling."),
        seg("SPEAKER_01", "Where is my order?"),
        seg("SPEAKER_00", "Let me check that account number."),
    ]
    mappings = classifier.classify(segments)
    assert len(mappings) == 2
    
    s0_map = next(m for m in mappings if m.speaker == "SPEAKER_00")
    s1_map = next(m for m in mappings if m.speaker == "SPEAKER_01")
    
    assert s0_map.role == SpeakerRole.AGENT
    assert s1_map.role == SpeakerRole.CUSTOMER

def test_ambiguous_conversation():
    classifier = RuleBasedRoleClassifier()
    # One utterance matches both roles perfectly
    segments = [
        seg("SPEAKER_00", "I ordered something, can I have your account number?")
    ]
    mappings = classifier.classify(segments)
    assert mappings[0].role == SpeakerRole.UNKNOWN
    assert mappings[0].confidence == 0.5

def test_unknown_role():
    classifier = RuleBasedRoleClassifier()
    segments = [
        seg("SPEAKER_00", "Hello."),
        seg("SPEAKER_01", "Yes, hi.")
    ]
    mappings = classifier.classify(segments)
    assert len(mappings) == 2
    assert mappings[0].role == SpeakerRole.UNKNOWN
    assert mappings[1].role == SpeakerRole.UNKNOWN

def test_multiple_speakers():
    classifier = RuleBasedRoleClassifier()
    segments = [
        seg("SPEAKER_00", "Thank you for calling."),
        seg("SPEAKER_01", "I need a refund."),
        seg("SPEAKER_02", "Yeah, me too. I ordered something.")
    ]
    mappings = classifier.classify(segments)
    assert len(mappings) == 3
    
    roles = {m.speaker: m.role for m in mappings}
    assert roles["SPEAKER_00"] == SpeakerRole.AGENT
    assert roles["SPEAKER_01"] == SpeakerRole.CUSTOMER
    assert roles["SPEAKER_02"] == SpeakerRole.CUSTOMER

def test_no_transcript():
    classifier = RuleBasedRoleClassifier()
    segments = []
    mappings = classifier.classify(segments)
    assert mappings == []

def test_empty_transcript():
    classifier = RuleBasedRoleClassifier()
    segments = [seg("SPEAKER_00", " ")]
    mappings = classifier.classify(segments)
    assert mappings[0].role == SpeakerRole.UNKNOWN

def test_original_identity_preservation():
    classifier = RuleBasedRoleClassifier()
    segments = [
        seg("SPK_99", "Thank you for calling.")
    ]
    mappings = classifier.classify(segments)
    assert mappings[0].speaker == "SPK_99"
    assert mappings[0].role == SpeakerRole.AGENT

def test_classifier_abstraction():
    class DummyClassifier(SpeakerRoleClassifier):
        def classify(self, segments):
            return []
            
    service = SpeakerTaggingService(classifier=DummyClassifier())
    assert service.process("CALL_1", []) == []

def test_service_integration():
    service = SpeakerTaggingService()
    mappings = service.process("CALL_2", [
        seg("SPEAKER_00", "Thank you for calling support."),
        seg("SPEAKER_01", "I need to track my package.")
    ])
    
    assert len(mappings) == 2
    roles = {m.speaker: m.role for m in mappings}
    assert roles["SPEAKER_00"] == SpeakerRole.AGENT
    assert roles["SPEAKER_01"] == SpeakerRole.CUSTOMER
