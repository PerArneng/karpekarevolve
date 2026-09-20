from pydantic import BaseModel, ConfigDict

from kaprekarevolve.interfaces.kaprekar.analysis_failure import AnalysisFailure
from kaprekarevolve.interfaces.kaprekar.map_analysis import MapAnalysis
from kaprekarevolve.interfaces.shape.code_shape import CodeShape


class ScoreCard(BaseModel):
    """The verdict on one candidate map: the score, its factors and the evidence."""

    model_config = ConfigDict(frozen=True)

    combined_score: float
    valid: bool
    dominance: float
    attractor_focus: float
    cycle_quality: float
    depth_score: float
    elegance: float
    novelty: float
    analysis: MapAnalysis | None = None
    shape: CodeShape | None = None
    failure: AnalysisFailure | None = None
