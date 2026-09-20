from datetime import datetime

import pytest

from kaprekarevolve.interfaces.kaprekar import (
    AnalysisFailure,
    AnalysisOutcome,
    AnalysisSettings,
    FailureReason,
)
from kaprekarevolve.interfaces.novelty import NoveltyRegistry
from kaprekarevolve.interfaces.scoring import ScoreWeights
from kaprekarevolve.interfaces.shape import CodeShape
from kaprekarevolve.modules.kaprekar import BuiltinKaprekarMap, MemoizedMapAnalyzer
from kaprekarevolve.modules.novelty import AnalysisFingerprinter
from kaprekarevolve.modules.scoring import WeightedScoringPolicy
from tests.fakes import FrozenClock

ANALYZER = MemoizedMapAnalyzer(
    clock=FrozenClock(datetime(2026, 9, 20, 12, 0, 0)), settings=AnalysisSettings()
)
FINGERPRINTER = AnalysisFingerprinter()
# An empty registry: nothing is known, so these tests measure shape alone.
POLICY = WeightedScoringPolicy(
    weights=ScoreWeights(), registry=NoveltyRegistry(), fingerprinter=FINGERPRINTER
)


def _shape(cost: int) -> CodeShape:
    return CodeShape(
        node_count=cost, branch_count=0, magic_constant_count=0, table_element_count=0, cost=cost
    )


def test_baseline_scores_as_measured() -> None:
    card = POLICY.score(ANALYZER.analyze(BuiltinKaprekarMap()))

    assert card.valid
    assert card.combined_score == pytest.approx(0.788877, abs=1e-6)
    assert card.dominance == pytest.approx(0.9985, abs=1e-4)
    assert card.attractor_focus == pytest.approx(0.8)
    assert card.cycle_quality == 1.0
    # Kaprekar's own mean depth is what the band is centred on.
    assert card.depth_score == pytest.approx(0.9876, abs=1e-4)


def test_a_constant_map_scores_zero_despite_its_single_tidy_attractor() -> None:
    card = POLICY.score(ANALYZER.analyze(lambda _: 6174))

    assert card.valid
    assert card.dominance == 1.0
    assert card.attractor_focus == 1.0
    assert card.depth_score == 0.0
    assert card.combined_score == 0.0


def test_the_identity_scores_zero() -> None:
    card = POLICY.score(ANALYZER.analyze(lambda value: value))

    assert card.combined_score == 0.0


def test_a_near_constant_map_is_still_treated_as_trivial() -> None:
    """depth_score is the anti-triviality term, so its low end must not be generous.

    A bare Gaussian band hands this map 0.18. The onset gate is what keeps it near zero,
    continuously, rather than with a cutoff that only catches a mean depth of exactly 1.
    """
    # Everything lands on 0 in one step; only 0 itself is already there.
    card = POLICY.score(ANALYZER.analyze(lambda value: 0 if value else 1))

    assert card.depth_score < 0.01


def test_a_rejected_map_scores_zero_and_keeps_its_failure() -> None:
    failure = AnalysisFailure(reason=FailureReason.OUT_OF_RANGE, detail="0000 returned -1")

    card = POLICY.score(AnalysisOutcome(failure=failure))

    assert not card.valid
    assert card.combined_score == 0.0
    assert card.failure == failure


def test_a_map_settling_near_the_peak_beats_the_baseline() -> None:
    # Every value walks down to zero a thousand at a time: one attractor, mean depth 5.5.
    card = POLICY.score(ANALYZER.analyze(lambda value: max(0, value - 1000)))

    assert card.attractor_focus == 1.0
    assert card.cycle_quality == 1.0
    assert card.depth_score == pytest.approx(0.9727, abs=1e-4)
    assert card.combined_score > 0.788877


def test_padding_trajectories_now_costs_rather_than_pays() -> None:
    """The old ramp paid for depth up to a cap, which is what produced the bloat."""
    shallow = POLICY.score(ANALYZER.analyze(lambda value: max(0, value - 1000)))
    padded = POLICY.score(ANALYZER.analyze(lambda value: max(0, value - 100)))

    assert padded.analysis is not None and shallow.analysis is not None
    assert padded.analysis.mean_depth > shallow.analysis.mean_depth
    assert padded.depth_score < shallow.depth_score


def test_elegance_falls_with_code_size_and_never_plateaus() -> None:
    outcome = ANALYZER.analyze(BuiltinKaprekarMap())

    tidy = POLICY.score(outcome, _shape(20)).elegance
    middling = POLICY.score(outcome, _shape(48)).elegance
    sprawling = POLICY.score(outcome, _shape(400)).elegance

    assert tidy > middling > sprawling
    # No flat top: a factor that saturates stops ranking whatever reaches it.
    assert POLICY.score(outcome, _shape(1)).elegance < 1.0


def test_a_map_with_no_source_is_judged_on_convergence_alone() -> None:
    card = POLICY.score(ANALYZER.analyze(BuiltinKaprekarMap()), None)

    assert card.elegance == 1.0
    assert card.shape is None


def test_a_known_structure_is_discounted_as_prior_art() -> None:
    outcome = ANALYZER.analyze(BuiltinKaprekarMap())
    assert outcome.analysis is not None
    registry = NoveltyRegistry(
        known_costs={FINGERPRINTER.fingerprint(outcome.analysis): 50}
    )
    policy = WeightedScoringPolicy(
        weights=ScoreWeights(), registry=registry, fingerprinter=FINGERPRINTER
    )

    # Reaching a known structure in far more code is worth almost nothing...
    assert policy.score(outcome, _shape(500)).novelty == pytest.approx(0.005)
    # ...but a shorter route to it keeps the full discount.
    assert policy.score(outcome, _shape(25)).novelty == pytest.approx(0.05)
    # An unknown structure is untouched.
    assert POLICY.score(outcome, _shape(500)).novelty == 1.0
