from typing import Protocol

from kaprekarevolve.interfaces.scoring.evaluation_report import EvaluationReport
from kaprekarevolve.interfaces.scoring.score_card import ScoreCard


class EvaluationProjector(Protocol):
    """Turns a score card into the metrics and artifacts OpenEvolve consumes. Pure."""

    def project(self, card: ScoreCard) -> EvaluationReport:
        """Return the evaluation report for ``card``."""
        ...
