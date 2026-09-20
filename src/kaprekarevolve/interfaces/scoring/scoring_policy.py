from typing import Protocol

from kaprekarevolve.interfaces.kaprekar.analysis_outcome import AnalysisOutcome
from kaprekarevolve.interfaces.scoring.score_card import ScoreCard


class ScoringPolicy(Protocol):
    """Turns an analysis into a score. Pure."""

    def score(self, outcome: AnalysisOutcome) -> ScoreCard:
        """Return the score card for ``outcome``."""
        ...
