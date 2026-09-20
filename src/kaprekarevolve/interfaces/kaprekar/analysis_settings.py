from pydantic import BaseModel, ConfigDict


class AnalysisSettings(BaseModel):
    """Bounds of the analysis. Injected, so tests can shrink the domain."""

    model_config = ConfigDict(frozen=True)

    domain_size: int = 10_000
    max_iterations: int = 1_001
    determinism_sample_size: int = 64
    #: How often to check the clock while evaluating the map over the domain.
    time_check_stride: int = 500
    quick_sample_size: int = 200
    time_budget_seconds: float = 60.0
