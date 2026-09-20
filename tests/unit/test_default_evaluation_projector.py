from kaprekarevolve.interfaces.kaprekar import AnalysisFailure, FailureReason
from kaprekarevolve.interfaces.scoring import ScoreCard
from kaprekarevolve.modules.scoring import REJECTED_FEATURES, DefaultEvaluationProjector

PROJECTOR = DefaultEvaluationProjector()


def _rejected() -> ScoreCard:
    return ScoreCard(
        combined_score=0.0,
        valid=False,
        dominance=0.0,
        attractor_focus=0.0,
        cycle_quality=0.0,
        depth_score=0.0,
        elegance=0.0,
        novelty=0.0,
        failure=AnalysisFailure(
            reason=FailureReason.OUT_OF_RANGE, detail="0000 returned 12345"
        ),
    )


def test_a_rejection_is_forwarded_as_an_artifact() -> None:
    report = PROJECTOR.project(_rejected())

    assert report.metrics["combined_score"] == 0.0
    assert report.metrics["validity"] == 0.0
    assert report.artifacts["failure_reason"] == "out_of_range"
    assert report.artifacts["stderr"] == "0000 returned 12345"


def test_a_rejection_still_carries_every_feature_dimension() -> None:
    """Otherwise the rejection reason never reaches the model.

    OpenEvolve computes MAP-Elites coordinates inside ``database.add()`` and raises when
    a configured feature dimension is missing from a program's metrics. The call that
    stores artifacts is the next statement, so it never runs. Across every run on record
    that cost all 173 rejections their explanation - and the assertion this test replaced,
    ``"attractor_count" not in report.metrics``, is what held the bug in place.
    """
    report = PROJECTOR.project(_rejected())

    for feature in REJECTED_FEATURES:
        assert feature in report.metrics, f"{feature} missing: artifacts would be dropped"


def test_the_cheap_stage_also_carries_every_feature_dimension() -> None:
    """The stage-1 path is the one that actually failed in the logged runs.

    Every ERROR line across all five run directories came from a cascade stage-1
    rejection, whose metrics carried only combined_score and validity.
    """
    failure = AnalysisFailure(reason=FailureReason.RAISED, detail="0000 raised ValueError")

    rejected = PROJECTOR.project_screening(False, failure, 0.0001)
    passed = PROJECTOR.project_screening(True, None, 0.0001)

    for feature in REJECTED_FEATURES:
        assert feature in rejected.metrics
        assert feature in passed.metrics
    assert rejected.metrics["combined_score"] == 0.0
    assert rejected.artifacts["stderr"] == "0000 raised ValueError"
    # The pass sentinel must stay below any score a real map can earn: OpenEvolve keeps
    # these metrics when stage 2 times out.
    assert 0.0 < passed.metrics["combined_score"] < 0.001


def test_the_depth_note_says_which_side_of_the_band_the_map_is_on() -> None:
    """A map that settles too fast needs the opposite advice to one that pads its paths."""
    shallow = DefaultEvaluationProjector._depth_note(3.09, 6)
    deep = DefaultEvaluationProjector._depth_note(8.72, 16)

    assert "BELOW" in shallow and "too quickly" in shallow
    assert "ABOVE" in deep and "LOWERS" in deep
    # Telling a too-shallow map to stop padding is the advice it must never get.
    assert "LOWERS" not in shallow
