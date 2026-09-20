from kaprekarevolve.interfaces.kaprekar import AnalysisFailure
from kaprekarevolve.interfaces.scoring import EvaluationReport, ScoreCard

#: Every metric named in a config's `feature_dimensions` must be present on EVERY
#: program, including rejected ones. OpenEvolve raises inside `database.add()` when one
#: is missing, and the very next statement is the one that stores artifacts - so a
#: missing key threw away the rejection reason instead of feeding it back to the model.
#: Across every run on record that cost 173 of 173 rejections their explanation.
REJECTED_FEATURES: dict[str, float] = {
    # The score's own factors.
    "dominance": 0.0,
    "attractor_focus": 0.0,
    "cycle_quality": 0.0,
    "depth_score": 0.0,
    "elegance": 0.0,
    "novelty": 0.0,
    # The raw analysis, unscaled, because the MAP-Elites grid bins on it.
    "attractor_count": 0.0,
    "dominant_basin_fraction": 0.0,
    "dominant_cycle_length": 0.0,
    "mean_depth": 0.0,
    "max_depth": 0.0,
    "image_ratio": 0.0,
    "fixed_point_count": 0.0,
    "elegance_cost": 0.0,
    "depth_ratio": 0.0,
}


class DefaultEvaluationProjector:
    """Flattens a score card.

    ``combined_score`` drives selection; the raw metrics are what the MAP-Elites grid
    bins on, so they are returned unscaled.
    """

    def project_screening(
        self, passed: bool, failure: AnalysisFailure | None, pass_score: float
    ) -> EvaluationReport:
        """Project the cheap cascade stage, which checks the contract and nothing else.

        It goes through this class rather than hand-building a dict so that the feature
        dimensions are listed in exactly one place. A stage-1 rejection that omits one
        is thrown away by OpenEvolve before its reason is ever stored - which is what
        happened at iterations 28, 41, 61, 64, 72, 102, 163 and 189 of the logged runs.
        """
        metrics: dict[str, float] = {
            "combined_score": pass_score if passed else 0.0,
            "validity": 1.0 if passed else 0.0,
            **REJECTED_FEATURES,
        }
        artifacts: dict[str, str] = {}
        if failure is not None:
            artifacts["failure_reason"] = failure.reason.value
            artifacts["stderr"] = failure.detail
        return EvaluationReport(metrics=metrics, artifacts=artifacts)

    def project(self, card: ScoreCard) -> EvaluationReport:
        # Start from every key this class can ever emit, so that no path can omit a
        # configured feature dimension. Omitting one costs the candidate its artifacts.
        metrics: dict[str, float] = {
            **REJECTED_FEATURES,
            "combined_score": card.combined_score,
            "validity": 1.0 if card.valid else 0.0,
            "dominance": card.dominance,
            "attractor_focus": card.attractor_focus,
            "cycle_quality": card.cycle_quality,
            "depth_score": card.depth_score,
            "elegance": card.elegance,
            "novelty": card.novelty,
        }
        artifacts: dict[str, str] = {}
        if card.failure is not None:
            artifacts["failure_reason"] = card.failure.reason.value
            artifacts["stderr"] = card.failure.detail
        analysis = card.analysis
        if analysis is None:
            return EvaluationReport(metrics=metrics, artifacts=artifacts)
        metrics.update(
            {
                "attractor_count": float(analysis.attractor_count),
                "dominant_basin_fraction": analysis.dominant_basin_fraction,
                "dominant_cycle_length": float(analysis.dominant_cycle_length),
                "mean_depth": analysis.mean_depth,
                "max_depth": float(analysis.max_depth),
                "image_ratio": analysis.image_ratio,
                "fixed_point_count": float(analysis.fixed_point_count),
                "elegance_cost": float(card.shape.cost) if card.shape is not None else 0.0,
                # Bounded 0..1, so OpenEvolve's running min-max scaling cannot be
                # wrecked by one outlier the way an unbounded count is.
                "depth_ratio": analysis.mean_depth / max(analysis.max_depth, 1),
            }
        )
        artifacts.update(self._feedback(card))
        return EvaluationReport(metrics=metrics, artifacts=artifacts)

    @classmethod
    def _feedback(cls, card: ScoreCard) -> dict[str, str]:
        """Tell the model *why* it scored what it scored.

        The score is a product, so one weak factor decides the outcome. Naming it is
        far better steering than a static system message.
        """
        notes: dict[str, str] = {}
        if card.novelty < 1.0:
            notes["novelty"] = (
                "This map is a relabelling of one already in the catalogue: its "
                "functional graph is identical, only the values differ. Score suppressed. "
                "Change the STRUCTURE, not the constants."
            )
        if card.shape is not None and card.elegance < 0.4:
            notes["elegance"] = (
                f"Source is elaborate: AST cost {card.shape.cost} "
                f"({card.shape.branch_count} branches, "
                f"{card.shape.magic_constant_count} magic constants). "
                "Shorter, plainer arithmetic scores higher."
            )
        analysis = card.analysis
        if card.depth_score < 0.85 and analysis is not None:
            notes["depth"] = cls._depth_note(analysis.mean_depth, analysis.max_depth)
        return notes

    @staticmethod
    def _depth_note(mean_depth: float, max_depth: int) -> str:
        """Say which side of the band the map is on.

        Telling a map that settles too fast that it should stop padding its paths is
        the opposite of what it needs, and the band has two sides.
        """
        if mean_depth < 5.0:
            return (
                f"Mean depth {mean_depth:.2f} is BELOW the band, which peaks at 5. "
                "This map settles too quickly. Find one whose trajectories are longer "
                "by their own arithmetic - NOT by adding stages or special cases, which "
                "the elegance factor charges for."
            )
        return (
            f"Mean depth {mean_depth:.2f} (deepest {max_depth}) is ABOVE the band, which "
            "peaks at 5 and is damped again past a deepest path of 12. Padding "
            "trajectories LOWERS the score. Aim for Kaprekar's own depth, not more."
        )
