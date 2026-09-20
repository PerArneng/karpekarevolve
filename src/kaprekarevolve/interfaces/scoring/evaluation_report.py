from pydantic import BaseModel, ConfigDict


class EvaluationReport(BaseModel):
    """What an evaluation hands back to OpenEvolve.

    ``metrics`` drives selection and the MAP-Elites grid; ``artifacts`` is the
    side-channel that puts a rejection message in front of the next generation.
    """

    model_config = ConfigDict(frozen=True)

    metrics: dict[str, float]
    artifacts: dict[str, str] = {}
