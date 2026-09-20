from pydantic import BaseModel, ConfigDict

from kaprekarevolve.interfaces.kaprekar.analysis_failure import AnalysisFailure
from kaprekarevolve.interfaces.kaprekar.map_analysis import MapAnalysis


class AnalysisOutcome(BaseModel):
    """Either an analysis or the reason there is none. Exactly one is set."""

    model_config = ConfigDict(frozen=True)

    analysis: MapAnalysis | None = None
    failure: AnalysisFailure | None = None
