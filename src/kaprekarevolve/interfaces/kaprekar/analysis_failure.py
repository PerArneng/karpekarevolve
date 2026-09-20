from pydantic import BaseModel, ConfigDict

from kaprekarevolve.interfaces.kaprekar.failure_reason import FailureReason


class AnalysisFailure(BaseModel):
    """A rejected candidate, with a message the evolving LLM can act on."""

    model_config = ConfigDict(frozen=True)

    reason: FailureReason
    detail: str
