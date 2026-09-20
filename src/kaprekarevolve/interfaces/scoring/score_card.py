from pydantic import BaseModel, ConfigDict

from kaprekarevolve.interfaces.kaprekar.analysis_failure import AnalysisFailure
from kaprekarevolve.interfaces.kaprekar.map_analysis import MapAnalysis


class ScoreCard(BaseModel):
    """The verdict on one candidate map: the score, its factors and the evidence."""

    model_config = ConfigDict(frozen=True)

    combined_score: float
    valid: bool
    dominance: float
    parsimony: float
    cycle_quality: float
    depth_score: float
    analysis: MapAnalysis | None = None
    failure: AnalysisFailure | None = None
