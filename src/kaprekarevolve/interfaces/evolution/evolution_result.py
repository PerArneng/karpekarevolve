from pydantic import BaseModel, ConfigDict


class EvolutionResult(BaseModel):
    """What an evolution run produced."""

    model_config = ConfigDict(frozen=True)

    best_score: float
    best_code: str
    metrics: dict[str, float]
    output_dir: str | None = None
