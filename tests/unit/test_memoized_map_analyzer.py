from datetime import datetime

import pytest

from kaprekarevolve.interfaces.kaprekar import AnalysisSettings, FailureReason
from kaprekarevolve.modules.kaprekar import BuiltinKaprekarMap, MemoizedMapAnalyzer
from tests.fakes import FrozenClock

MOMENT = datetime(2026, 9, 20, 12, 0, 0)


def analyzer(**overrides: object) -> MemoizedMapAnalyzer:
    return MemoizedMapAnalyzer(
        clock=FrozenClock(MOMENT), settings=AnalysisSettings(**overrides)
    )


def test_kaprekar_baseline_has_two_attractors() -> None:
    outcome = analyzer().analyze(BuiltinKaprekarMap())

    analysis = outcome.analysis
    assert analysis is not None
    assert analysis.attractor_count == 2
    assert analysis.dominant_attractor.members == (6174,)
    assert analysis.dominant_attractor.basin_size == 9990
    assert analysis.dominant_basin_fraction == pytest.approx(0.999)
    assert analysis.dominant_cycle_length == 1
    assert analysis.max_depth == 7
    assert analysis.mean_depth == pytest.approx(4.6646)
    assert analysis.image_size == 55
    assert analysis.fixed_point_count == 2


def test_identity_gives_one_attractor_per_value() -> None:
    outcome = analyzer().analyze(lambda value: value)

    analysis = outcome.analysis
    assert analysis is not None
    assert analysis.attractor_count == 10_000
    assert analysis.mean_depth == 0.0
    assert analysis.fixed_point_count == 10_000


def test_constant_map_settles_in_a_single_step() -> None:
    outcome = analyzer().analyze(lambda _: 6174)

    analysis = outcome.analysis
    assert analysis is not None
    assert analysis.attractor_count == 1
    assert analysis.mean_depth == pytest.approx(0.9999)
    assert analysis.max_depth == 1


def test_two_cycle_is_reported_as_one_attractor_of_length_two() -> None:
    outcome = analyzer().analyze(lambda value: 1 if value == 0 else 0)

    analysis = outcome.analysis
    assert analysis is not None
    assert analysis.attractor_count == 1
    assert analysis.dominant_attractor.members == (0, 1)
    assert analysis.dominant_cycle_length == 2


def test_out_of_range_output_is_rejected() -> None:
    outcome = analyzer().analyze(lambda value: value + 10_000)

    assert outcome.analysis is None
    assert outcome.failure is not None
    assert outcome.failure.reason is FailureReason.OUT_OF_RANGE


def test_non_integer_output_is_rejected() -> None:
    outcome = analyzer().analyze(lambda value: f"{value:04d}")  # type: ignore[arg-type]

    assert outcome.failure is not None
    assert outcome.failure.reason is FailureReason.NOT_INTEGER


def test_raising_map_is_rejected() -> None:
    def explode(value: int) -> int:
        raise ValueError("boom")

    outcome = analyzer().analyze(explode)

    assert outcome.failure is not None
    assert outcome.failure.reason is FailureReason.RAISED
    assert "boom" in outcome.failure.detail


def test_non_deterministic_map_is_rejected() -> None:
    class Counter:
        def __init__(self) -> None:
            self.calls = 0

        def __call__(self, value: int) -> int:
            self.calls += 1
            return self.calls % 10_000

    outcome = analyzer().analyze(Counter())

    assert outcome.failure is not None
    assert outcome.failure.reason is FailureReason.NON_DETERMINISTIC


def test_a_map_that_settles_too_slowly_is_rejected() -> None:
    # A single long chain: 0 -> 1 -> 2 -> ... -> 9999 -> 9999.
    outcome = analyzer(max_iterations=100).analyze(lambda value: min(value + 1, 9_999))

    assert outcome.failure is not None
    assert outcome.failure.reason is FailureReason.ITERATION_LIMIT


def test_time_budget_is_enforced() -> None:
    slow = MemoizedMapAnalyzer(
        clock=FrozenClock(MOMENT, seconds=0.0),
        settings=AnalysisSettings(time_budget_seconds=-1.0),
    )

    outcome = slow.analyze(BuiltinKaprekarMap())

    assert outcome.failure is not None
    assert outcome.failure.reason is FailureReason.TIME_LIMIT


def test_trace_walks_to_the_fixed_point() -> None:
    trajectory = analyzer().trace(BuiltinKaprekarMap(), 9831)

    assert trajectory.seed == 9831
    assert trajectory.values[0] == 9831
    assert trajectory.cycle == (6174,)
    assert trajectory.steps_to_cycle == 7


def test_validate_passes_the_baseline_and_catches_a_broken_map() -> None:
    assert analyzer().validate(BuiltinKaprekarMap()) is None

    failure = analyzer().validate(lambda value: -1)
    assert failure is not None
    assert failure.reason is FailureReason.OUT_OF_RANGE
