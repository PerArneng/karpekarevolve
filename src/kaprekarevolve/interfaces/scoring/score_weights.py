from pydantic import BaseModel, ConfigDict


class ScoreWeights(BaseModel):
    """Tunables of the combined score. Injected, never hard-coded in the policy."""

    model_config = ConfigDict(frozen=True)

    dominance_exponent: float = 1.5
    attractor_penalty: float = 0.25
    cycle_penalty: float = 0.5
    depth_floor: float = 1.0
    depth_span: float = 5.0
