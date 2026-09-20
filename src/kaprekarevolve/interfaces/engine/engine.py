from pathlib import Path
from typing import Protocol

from kaprekarevolve.interfaces.scoring.evaluation_report import EvaluationReport
from kaprekarevolve.interfaces.scoring.score_card import ScoreCard


class Engine(Protocol):
    """The facade every frontend calls."""

    def score_source(self, source: str) -> ScoreCard:
        """Score candidate source code."""
        ...

    def score_path(self, path: Path) -> ScoreCard:
        """Score the candidate program stored at ``path``."""
        ...

    def evaluate_path(self, path: Path) -> EvaluationReport:
        """Return the full OpenEvolve evaluation of the program at ``path``."""
        ...

    def screen_path(self, path: Path) -> EvaluationReport:
        """Return a cheap contract check of the program at ``path``."""
        ...

    def show_baseline(self) -> None:
        """Report the built-in Kaprekar routine."""
        ...

    def show_score(self, path: Path) -> None:
        """Report the candidate program at ``path``."""
        ...

    def show_trace(self, seed: int, path: Path | None) -> None:
        """Report the walk of ``seed`` under a candidate, or under the baseline."""
        ...

    def show_best(self) -> None:
        """Report the best program left behind by the last evolution run."""
        ...

    def evolve(self, iterations: int | None, backend: str | None = None) -> None:
        """Run an evolution and report the winner.

        `backend` names a config in `evolution/`, e.g. "cerebras".
        """
        ...
