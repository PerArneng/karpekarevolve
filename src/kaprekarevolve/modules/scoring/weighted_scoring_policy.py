from kaprekarevolve.interfaces.kaprekar import AnalysisOutcome, MapAnalysis
from kaprekarevolve.interfaces.scoring import ScoreCard, ScoreWeights


class WeightedScoringPolicy:
    """Scores the *shape* of a map's convergence.

    On a finite domain every total map converges, so "does it converge?" says nothing.
    Four factors multiply together, each in ``0..1``:

    ``dominance``
        the share of the domain that falls into the largest attractor.
    ``parsimony``
        decays with the number of distinct attractors.
    ``cycle_quality``
        a fixed point beats a long terminal cycle.
    ``depth_score``
        rewards *structure*: how many steps the average value needs to settle. This is
        the anti-triviality term. A constant map has mean depth 1 and the identity has
        mean depth 0, so both score exactly zero however tidy their attractors look.

    Output diversity is deliberately absent: the real Kaprekar routine only ever emits
    55 distinct values, so rewarding a wide image would punish the thing being imitated.
    """

    def __init__(self, weights: ScoreWeights) -> None:
        self._weights = weights

    def score(self, outcome: AnalysisOutcome) -> ScoreCard:
        analysis = outcome.analysis
        if analysis is None:
            return ScoreCard(
                combined_score=0.0,
                valid=False,
                dominance=0.0,
                parsimony=0.0,
                cycle_quality=0.0,
                depth_score=0.0,
                failure=outcome.failure,
            )
        dominance = self._dominance(analysis)
        parsimony = self._parsimony(analysis)
        cycle_quality = self._cycle_quality(analysis)
        depth_score = self._depth_score(analysis)
        return ScoreCard(
            combined_score=dominance * parsimony * cycle_quality * depth_score,
            valid=True,
            dominance=dominance,
            parsimony=parsimony,
            cycle_quality=cycle_quality,
            depth_score=depth_score,
            analysis=analysis,
        )

    def _dominance(self, analysis: MapAnalysis) -> float:
        return float(analysis.dominant_basin_fraction**self._weights.dominance_exponent)

    def _parsimony(self, analysis: MapAnalysis) -> float:
        excess = analysis.attractor_count - 1
        return 1.0 / (1.0 + self._weights.attractor_penalty * excess)

    def _cycle_quality(self, analysis: MapAnalysis) -> float:
        excess = analysis.dominant_cycle_length - 1
        return 1.0 / (1.0 + self._weights.cycle_penalty * excess)

    def _depth_score(self, analysis: MapAnalysis) -> float:
        reach = (analysis.mean_depth - self._weights.depth_floor) / self._weights.depth_span
        return min(1.0, max(0.0, reach))
