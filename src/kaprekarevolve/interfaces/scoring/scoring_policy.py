from typing import Protocol

from kaprekarevolve.interfaces.kaprekar.analysis_outcome import AnalysisOutcome
from kaprekarevolve.interfaces.scoring.score_card import ScoreCard
from kaprekarevolve.interfaces.shape.code_shape import CodeShape


class ScoringPolicy(Protocol):
    """Turns an analysis into a score. Pure."""

    def score(self, outcome: AnalysisOutcome, shape: CodeShape | None = None) -> ScoreCard:
        """Return the score card for ``outcome``.

        ``shape`` is the measured source of the candidate, or ``None`` for a map that
        has no source - the built-in baseline.
        """
        ...
