from enum import StrEnum


class PipelineStage(StrEnum):
    DISCOVERED = "discovered"
    RESEARCHED = "researched"
    QUALIFIED = "qualified"
    CALL_PENDING = "call_pending"
    CONTACTED = "contacted"
    AUDIT_SENT = "audit_sent"
    AUDIT_COMPLETED = "audit_completed"
    MEETING = "meeting"
    DIAGNOSIS = "diagnosis"
    PROPOSAL = "proposal"
    WON = "won"
    LOST = "lost"
    NURTURING = "nurturing"

    @property
    def is_terminal(self) -> bool:
        return self in {self.WON, self.LOST}


class CallOutcome(StrEnum):
    NO_ANSWER = "no_answer"
    CALL_BACK = "call_back"
    WRONG_CONTACT = "wrong_contact"
    NOT_INTERESTED = "not_interested"
    INTERESTED = "interested"
    SEND_AUDIT = "send_audit"
    MEETING = "meeting"
    DISCARDED = "discarded"


PIPELINE_ORDER = tuple(PipelineStage)
