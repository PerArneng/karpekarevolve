from kaprekarevolve.interfaces.evolution import EvolutionResult, EvolutionSettings


class RecordingEvolutionRunner:
    """Records the settings it was asked to run, and returns a canned result."""

    def __init__(self, result: EvolutionResult) -> None:
        self._result = result
        self.calls: list[EvolutionSettings] = []

    def run(self, settings: EvolutionSettings) -> EvolutionResult:
        self.calls.append(settings)
        return self._result
