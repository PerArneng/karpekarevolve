from kaprekarevolve.interfaces.kaprekar.analysis_failure import AnalysisFailure


class MapRejectedError(Exception):
    """Raised when a candidate map breaks its contract mid-walk."""

    def __init__(self, failure: AnalysisFailure) -> None:
        super().__init__(failure.detail)
        self.failure = failure
