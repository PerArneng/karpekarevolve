from functools import reduce
from math import gcd

from kaprekarevolve.interfaces.kaprekar import MapAnalysis
from kaprekarevolve.interfaces.novelty import MapFingerprint


class AnalysisFingerprinter:
    """Reduces an analysis to the structure of its functional graph."""

    def fingerprint(self, analysis: MapAnalysis) -> MapFingerprint:
        """Return the gcd-normalised in-degree profile of ``analysis``."""
        # The zero bucket counts values nothing maps to. It scales with the domain
        # rather than with the map's shape, so it is left out of the key.
        profile = tuple((degree, count) for degree, count in analysis.indegree_histogram if degree)
        if not profile:
            return MapFingerprint(structure=())
        degree_divisor = reduce(gcd, [degree for degree, _ in profile])
        count_divisor = reduce(gcd, [count for _, count in profile])
        return MapFingerprint(
            structure=tuple(
                sorted(
                    (degree // degree_divisor, count // count_divisor)
                    for degree, count in profile
                )
            )
        )
