import math

from kaprekarevolve.interfaces.kaprekar import AnalysisOutcome, MapAnalysis
from kaprekarevolve.interfaces.novelty import Fingerprinter, NoveltyRegistry
from kaprekarevolve.interfaces.scoring import ScoreCard, ScoreWeights
from kaprekarevolve.interfaces.shape import CodeShape


class WeightedScoringPolicy:
    """Scores the *shape* of a map's convergence, and the shape of the code that made it.

    On a finite domain every total map converges, so "does it converge?" says nothing.
    Six factors multiply together, each in ``0..1``:

    ``dominance``
        the share of the domain that falls into the largest attractor.
    ``attractor_focus``
        decays with the number of distinct attractors.
    ``cycle_quality``
        a fixed point beats a long terminal cycle.
    ``depth_score``
        a *band*, not a ramp. It peaks where Kaprekar's routine sits and falls away on
        both sides, so a map that settles instantly and a map that pads its trajectories
        are both penalised. The earlier ramp rewarded depth without limit up to a cap,
        and the search answered exactly as asked: it bolted rotation chains onto the
        Kaprekar difference purely to lengthen paths.
    ``elegance``
        decays with the AST cost of ``transform``. Strictly decreasing, with no flat top,
        because a factor that saturates stops ranking the candidates that reach it.
    ``novelty``
        discounts prior art. A structure already in the catalogue is worth at most
        ``known_map_penalty``, scaled further by how much longer this code is than the
        cheapest route already known to it - so a *terser* expression of a known map
        keeps some credit, while bolting rotations onto one earns almost none. Without
        this term a relabelling of Kaprekar's routine reads as a discovery.

    Output diversity is deliberately absent: the real Kaprekar routine only ever emits
    55 distinct values, so rewarding a wide image would punish the thing being imitated.
    """

    def __init__(
        self,
        weights: ScoreWeights,
        registry: NoveltyRegistry,
        fingerprinter: Fingerprinter,
    ) -> None:
        self._weights = weights
        self._registry = registry
        self._fingerprinter = fingerprinter

    def score(self, outcome: AnalysisOutcome, shape: CodeShape | None = None) -> ScoreCard:
        analysis = outcome.analysis
        if analysis is None:
            return ScoreCard(
                combined_score=0.0,
                valid=False,
                dominance=0.0,
                attractor_focus=0.0,
                cycle_quality=0.0,
                depth_score=0.0,
                elegance=0.0,
                novelty=0.0,
                shape=shape,
                failure=outcome.failure,
            )
        dominance = self._dominance(analysis)
        attractor_focus = self._attractor_focus(analysis)
        cycle_quality = self._cycle_quality(analysis)
        depth_score = self._depth_score(analysis)
        elegance = self._elegance(shape)
        novelty = self._novelty(analysis, shape)
        return ScoreCard(
            combined_score=(
                dominance * attractor_focus * cycle_quality * depth_score * elegance * novelty
            ),
            valid=True,
            dominance=dominance,
            attractor_focus=attractor_focus,
            cycle_quality=cycle_quality,
            depth_score=depth_score,
            elegance=elegance,
            novelty=novelty,
            analysis=analysis,
            shape=shape,
        )

    def _dominance(self, analysis: MapAnalysis) -> float:
        return float(analysis.dominant_basin_fraction**self._weights.dominance_exponent)

    def _attractor_focus(self, analysis: MapAnalysis) -> float:
        excess = analysis.attractor_count - 1
        return 1.0 / (1.0 + self._weights.attractor_penalty * excess)

    def _cycle_quality(self, analysis: MapAnalysis) -> float:
        excess = analysis.dominant_cycle_length - 1
        return 1.0 / (1.0 + self._weights.cycle_penalty * excess)

    def _depth_score(self, analysis: MapAnalysis) -> float:
        """Score a Gaussian band on mean depth, gated at the low end, damped at the high.

        The gate is what keeps this the anti-triviality term: a bare Gaussian is
        generous to maps that barely move, and a hard cutoff would only catch a mean
        depth of exactly 1.0 while a map that settles in 1.05 steps sailed through.
        """
        mean_depth = analysis.mean_depth
        if mean_depth <= self._weights.depth_onset:
            return 0.0
        rise = (mean_depth - self._weights.depth_onset) / self._weights.depth_onset_width
        onset = 1.0 - math.exp(-rise * rise)
        offset = (mean_depth - self._weights.depth_peak) / self._weights.depth_width
        band = math.exp(-offset * offset)
        reach = min(1.0, self._weights.max_depth_reference / max(analysis.max_depth, 1))
        return onset * band * reach

    def _elegance(self, shape: CodeShape | None) -> float:
        """Strictly decreasing in AST cost. Never reaches 1.0, never reaches 0."""
        if shape is None:
            # The built-in baseline map is an object, not source. Judge it on its
            # convergence alone rather than inventing a cost for it.
            return 1.0
        reference = self._weights.elegance_reference
        return reference / (reference + shape.cost)

    def _novelty(self, analysis: MapAnalysis, shape: CodeShape | None) -> float:
        """Full credit for a new structure; a discount on one we already have."""
        best_known = self._registry.best_known_cost(self._fingerprinter.fingerprint(analysis))
        if best_known is None:
            return 1.0
        floor = self._weights.known_map_penalty
        if shape is None or shape.cost <= 0:
            return floor
        return floor * min(1.0, best_known / shape.cost)
