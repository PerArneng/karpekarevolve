from typing import Protocol

from kaprekarevolve.interfaces.catalogue.catalogue_entry import CatalogueEntry
from kaprekarevolve.interfaces.evolution.evolution_result import EvolutionResult
from kaprekarevolve.interfaces.kaprekar.trajectory import Trajectory
from kaprekarevolve.interfaces.scoring.score_card import ScoreCard


class ReportFormatter(Protocol):
    """Renders models as terminal text. Pure."""

    def format_score_card(self, title: str, card: ScoreCard) -> str:
        """Return a human readable report for ``card``."""
        ...

    def format_catalogue(self, examined: int, entries: list[CatalogueEntry]) -> str:
        """Render the enumerated catalogue of short-formula structures."""
        ...

    def format_trajectory(self, trajectory: Trajectory) -> str:
        """Return a human readable walk."""
        ...

    def format_evolution_result(self, result: EvolutionResult) -> str:
        """Return a human readable summary of an evolution run."""
        ...
