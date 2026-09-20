from typing import Protocol

from kaprekarevolve.interfaces.kaprekar.map_analysis import MapAnalysis
from kaprekarevolve.interfaces.novelty.map_fingerprint import MapFingerprint


class Fingerprinter(Protocol):
    """Identifies a map up to relabelling. Pure."""

    def fingerprint(self, analysis: MapAnalysis) -> MapFingerprint:
        """Return the fingerprint of ``analysis``."""
        ...
