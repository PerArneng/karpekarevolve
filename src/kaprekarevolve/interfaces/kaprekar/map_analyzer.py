from typing import Protocol

from kaprekarevolve.interfaces.kaprekar.analysis_failure import AnalysisFailure
from kaprekarevolve.interfaces.kaprekar.analysis_outcome import AnalysisOutcome
from kaprekarevolve.interfaces.kaprekar.trajectory import Trajectory
from kaprekarevolve.interfaces.program.digit_map import DigitMap


class MapAnalyzer(Protocol):
    """Explores a candidate map over the whole domain. Pure."""

    def analyze(self, digit_map: DigitMap) -> AnalysisOutcome:
        """Return the convergence structure of ``digit_map``, or why it was rejected."""
        ...

    def validate(self, digit_map: DigitMap) -> AnalysisFailure | None:
        """Check the contract on a sample of the domain, for a cheap early reject.

        Returns the first violation found, or ``None`` if the sample looks sound.
        """
        ...

    def trace(self, digit_map: DigitMap, seed: int) -> Trajectory:
        """Return the walk of ``seed`` under ``digit_map`` up to its first repeat."""
        ...
