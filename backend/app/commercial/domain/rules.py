from datetime import datetime

from app.commercial.domain.enums import PipelineStage


class CommercialRuleViolation(ValueError):
    pass


def require_next_action(
    stage: PipelineStage, next_best_action: str | None, next_action_at: datetime | None
) -> None:
    if stage.is_terminal:
        return
    if not next_best_action or next_action_at is None:
        raise CommercialRuleViolation(
            "Active opportunities require a next best action and due date"
        )
