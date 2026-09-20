from kaprekarevolve.interfaces.scoring import EvaluationReport, ScoreCard


class DefaultEvaluationProjector:
    """Flattens a score card.

    ``combined_score`` drives selection; the raw metrics are what the MAP-Elites grid
    bins on, so they are returned unscaled.
    """

    def project(self, card: ScoreCard) -> EvaluationReport:
        metrics: dict[str, float] = {
            "combined_score": card.combined_score,
            "validity": 1.0 if card.valid else 0.0,
            "dominance": card.dominance,
            "parsimony": card.parsimony,
            "cycle_quality": card.cycle_quality,
            "depth_score": card.depth_score,
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
            }
        )
        return EvaluationReport(metrics=metrics, artifacts=artifacts)
