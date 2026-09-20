from typing import Protocol

from kaprekarevolve.interfaces.shape.code_shape import CodeShape


class ShapeAnalyzer(Protocol):
    """Measures the shape of candidate source. Pure."""

    def analyze(self, source: str) -> CodeShape:
        """Return the shape of the ``transform`` function defined in ``source``."""
        ...
