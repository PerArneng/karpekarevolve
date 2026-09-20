from typing import Protocol

from kaprekarevolve.interfaces.evolution.evolution_result import EvolutionResult
from kaprekarevolve.interfaces.evolution.evolution_settings import EvolutionSettings


class EvolutionRunner(Protocol):
    """Drives OpenEvolve. An edge: it spends money and writes files."""

    def run(self, settings: EvolutionSettings) -> EvolutionResult:
        """Run the evolution described by ``settings`` and return its best program."""
        ...
