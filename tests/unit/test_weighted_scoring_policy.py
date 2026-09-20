from datetime import datetime

import pytest

from kaprekarevolve.interfaces.kaprekar import (
    AnalysisFailure,
    AnalysisOutcome,
    AnalysisSettings,
    FailureReason,
)
from kaprekarevolve.interfaces.scoring import ScoreWeights
from kaprekarevolve.modules.kaprekar import BuiltinKaprekarMap, MemoizedMapAnalyzer
from kaprekarevolve.modules.scoring import WeightedScoringPolicy
from tests.fakes import FrozenClock

ANALYZER = MemoizedMapAnalyzer(
    clock=FrozenClock(datetime(2026, 9, 20, 12, 0, 0)), settings=AnalysisSettings()
)
POLICY = WeightedScoringPolicy(weights=ScoreWeights())


def test_baseline_scores_as_measured() -> None:
    card = POLICY.score(ANALYZER.analyze(BuiltinKaprekarMap()))

    assert card.valid
    assert card.combined_score == pytest.approx(0.292728, abs=1e-6)
    assert card.dominance == pytest.approx(0.9985, abs=1e-4)
    assert card.parsimony == pytest.approx(0.8)
    assert card.cycle_quality == 1.0


def test_a_constant_map_scores_zero_despite_its_single_tidy_attractor() -> None:
    card = POLICY.score(ANALYZER.analyze(lambda _: 6174))

    assert card.valid
    assert card.dominance == 1.0
    assert card.parsimony == 1.0
    assert card.depth_score == 0.0
    assert card.combined_score == 0.0


def test_the_identity_scores_zero() -> None:
    card = POLICY.score(ANALYZER.analyze(lambda value: value))

    assert card.combined_score == 0.0


def test_a_rejected_map_scores_zero_and_keeps_its_failure() -> None:
    failure = AnalysisFailure(reason=FailureReason.OUT_OF_RANGE, detail="0000 returned -1")

    card = POLICY.score(AnalysisOutcome(failure=failure))

    assert not card.valid
    assert card.combined_score == 0.0
    assert card.failure == failure


def test_a_deep_single_fixed_point_beats_the_baseline() -> None:
    # Every value walks down to zero one step at a time: one attractor, deep basins.
    card = POLICY.score(ANALYZER.analyze(lambda value: max(0, value - 1000)))

    assert card.parsimony == 1.0
    assert card.cycle_quality == 1.0
    assert card.depth_score == pytest.approx(0.4499)
    assert card.combined_score > 0.292728
