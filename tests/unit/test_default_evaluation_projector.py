from kaprekarevolve.interfaces.kaprekar import AnalysisFailure, FailureReason
from kaprekarevolve.interfaces.scoring import ScoreCard
from kaprekarevolve.modules.scoring import DefaultEvaluationProjector

PROJECTOR = DefaultEvaluationProjector()


def test_a_rejection_is_forwarded_as_an_artifact() -> None:
    card = ScoreCard(
        combined_score=0.0,
        valid=False,
        dominance=0.0,
        parsimony=0.0,
        cycle_quality=0.0,
        depth_score=0.0,
        failure=AnalysisFailure(
            reason=FailureReason.OUT_OF_RANGE, detail="0000 returned 12345"
        ),
    )

    report = PROJECTOR.project(card)

    assert report.metrics["combined_score"] == 0.0
    assert report.metrics["validity"] == 0.0
    assert "attractor_count" not in report.metrics
    assert report.artifacts["failure_reason"] == "out_of_range"
    assert report.artifacts["stderr"] == "0000 returned 12345"
