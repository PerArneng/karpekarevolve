from typing import Protocol

from kaprekarevolve.interfaces.kaprekar.analysis_failure import AnalysisFailure
from kaprekarevolve.interfaces.scoring.evaluation_report import EvaluationReport
from kaprekarevolve.interfaces.scoring.score_card import ScoreCard


class EvaluationProjector(Protocol):
    """Turns a score card into the metrics and artifacts OpenEvolve consumes. Pure."""

    def project_screening(
        self, passed: bool, failure: AnalysisFailure | None, pass_score: float
    ) -> EvaluationReport:
        """Return the cheap cascade stage's report."""
        ...

    def project(self, card: ScoreCard) -> EvaluationReport:
        """Return the evaluation report for ``card``."""
        ...
