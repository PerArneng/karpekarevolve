from collections import Counter

from kaprekarevolve.interfaces.clock import Clock
from kaprekarevolve.interfaces.kaprekar import (
    AnalysisFailure,
    AnalysisOutcome,
    AnalysisSettings,
    Attractor,
    FailureReason,
    MapAnalysis,
    MapRejectedError,
    Trajectory,
)
from kaprekarevolve.interfaces.program import DigitMap

_UNVISITED = 0
_ON_PATH = 1
_SETTLED = 2


class MemoizedMapAnalyzer:
    """Analyses a map over the whole domain in one pass.

    The domain under a total map is a functional graph, so every value settles into
    exactly one cycle. Labelling each value once - memoised across seeds - makes the
    analysis O(domain) rather than O(domain x max_iterations), which is what lets the
    evaluator be exact instead of sampled.
    """

    def __init__(self, clock: Clock, settings: AnalysisSettings) -> None:
        self._clock = clock
        self._settings = settings

    def analyze(self, digit_map: DigitMap) -> AnalysisOutcome:
        started = self._clock.elapsed_seconds()
        try:
            outputs = self._tabulate(digit_map, started)
            self._reject_if_non_deterministic(digit_map, outputs)
            self._reject_if_out_of_time(started)
            analysis = self._explore(outputs)
            self._reject_if_out_of_time(started)
        except MapRejectedError as rejected:
            return AnalysisOutcome(failure=rejected.failure)
        return AnalysisOutcome(analysis=analysis)

    def validate(self, digit_map: DigitMap) -> AnalysisFailure | None:
        """Walk a stratified sample only. Cheap enough for a cascade's first stage."""
        domain_size = self._settings.domain_size
        sample_size = min(self._settings.quick_sample_size, domain_size)
        stride = max(1, domain_size // max(1, sample_size))
        try:
            for seed in range(0, domain_size, stride):
                seen: set[int] = set()
                current = seed
                while current not in seen:
                    seen.add(current)
                    current = self._apply(digit_map, current)
                    self._reject_if_too_long(len(seen), seed)
                if self._apply(digit_map, seed) != self._apply(digit_map, seed):
                    raise MapRejectedError(
                        AnalysisFailure(
                            reason=FailureReason.NON_DETERMINISTIC,
                            detail=f"{seed:04d} gave two different answers; the map must be pure",
                        )
                    )
        except MapRejectedError as rejected:
            return rejected.failure
        return None

    def trace(self, digit_map: DigitMap, seed: int) -> Trajectory:
        values: list[int] = []
        position: dict[int, int] = {}
        current = seed
        while current not in position and len(values) <= self._settings.max_iterations:
            position[current] = len(values)
            values.append(current)
            current = self._apply(digit_map, current)
        if current in position:
            start = position[current]
            return Trajectory(
                seed=seed,
                values=tuple(values),
                cycle=tuple(values[start:]),
                steps_to_cycle=start,
            )
        return Trajectory(
            seed=seed, values=tuple(values), cycle=(), steps_to_cycle=len(values)
        )

    def _tabulate(self, digit_map: DigitMap, started: float) -> list[int]:
        """Evaluate the map once on every value, validating the contract as we go.

        The clock is checked as we go, not merely afterwards: a candidate whose every
        call is slow would otherwise run past the whole time budget here and be killed
        by OpenEvolve's evaluator timeout instead - the one path that records a
        cascade stage-1 pass as the final score.
        """
        stride = self._settings.time_check_stride
        outputs: list[int] = []
        for value in range(self._settings.domain_size):
            if value % stride == 0:
                self._reject_if_out_of_time(started)
            outputs.append(self._apply(digit_map, value))
        return outputs

    def _apply(self, digit_map: DigitMap, value: int) -> int:
        try:
            result: object = digit_map(value)
        except Exception as error:  # noqa: BLE001 - any failure is the candidate's fault
            raise MapRejectedError(
                AnalysisFailure(
                    reason=FailureReason.RAISED,
                    detail=f"{value:04d} raised {type(error).__name__}: {error}",
                )
            ) from error
        if isinstance(result, bool) or not isinstance(result, int):
            raise MapRejectedError(
                AnalysisFailure(
                    reason=FailureReason.NOT_INTEGER,
                    detail=f"{value:04d} returned {result!r}, which is not an int",
                )
            )
        if not 0 <= result < self._settings.domain_size:
            raise MapRejectedError(
                AnalysisFailure(
                    reason=FailureReason.OUT_OF_RANGE,
                    detail=(
                        f"{value:04d} returned {result}, outside "
                        f"0..{self._settings.domain_size - 1}"
                    ),
                )
            )
        return result

    def _reject_if_non_deterministic(self, digit_map: DigitMap, outputs: list[int]) -> None:
        domain_size = self._settings.domain_size
        sample_size = min(self._settings.determinism_sample_size, domain_size)
        if sample_size == 0:
            return
        stride = max(1, domain_size // sample_size)
        for value in range(0, domain_size, stride):
            repeated = self._apply(digit_map, value)
            if repeated != outputs[value]:
                raise MapRejectedError(
                    AnalysisFailure(
                        reason=FailureReason.NON_DETERMINISTIC,
                        detail=(
                            f"{value:04d} returned {outputs[value]} then {repeated}; "
                            "the map must be pure"
                        ),
                    )
                )

    def _reject_if_out_of_time(self, started: float) -> None:
        elapsed = self._clock.elapsed_seconds() - started
        if elapsed > self._settings.time_budget_seconds:
            raise MapRejectedError(
                AnalysisFailure(
                    reason=FailureReason.TIME_LIMIT,
                    detail=f"analysis took {elapsed:.1f}s, budget is "
                    f"{self._settings.time_budget_seconds:.1f}s",
                )
            )

    def _explore(self, outputs: list[int]) -> MapAnalysis:
        domain_size = len(outputs)
        state = bytearray(domain_size)
        label = [-1] * domain_size
        depth = [0] * domain_size
        cycles: dict[int, tuple[int, ...]] = {}

        for seed in range(domain_size):
            if state[seed] != _UNVISITED:
                continue
            path: list[int] = []
            position: dict[int, int] = {}
            current = seed
            while state[current] == _UNVISITED:
                state[current] = _ON_PATH
                position[current] = len(path)
                path.append(current)
                current = outputs[current]
                self._reject_if_too_long(len(path), seed)
            if state[current] == _ON_PATH:
                start = position[current]
                members = tuple(sorted(path[start:]))
                identifier = members[0]
                cycles[identifier] = members
                for member in path[start:]:
                    state[member] = _SETTLED
                    label[member] = identifier
                    depth[member] = 0
                tail = path[:start]
            else:
                identifier = label[current]
                tail = path
            distance = depth[current]
            for node in reversed(tail):
                distance += 1
                state[node] = _SETTLED
                label[node] = identifier
                depth[node] = distance

        max_depth = max(depth)
        if max_depth > self._settings.max_iterations:
            self._reject_if_too_long(max_depth, depth.index(max_depth))
        basins = Counter(label)
        attractors = tuple(
            sorted(
                (
                    Attractor(
                        members=cycles[identifier],
                        cycle_length=len(cycles[identifier]),
                        basin_size=basin_size,
                    )
                    for identifier, basin_size in basins.items()
                ),
                key=lambda attractor: (-attractor.basin_size, attractor.members[0]),
            )
        )
        dominant = attractors[0]
        image_size = len(set(outputs))
        # Both histograms are graph invariants: two maps that are the same map
        # relabelled share them exactly. Together they are the novelty fingerprint.
        # Values that are never an output have in-degree 0 and so are absent from
        # the Counter; they are a real part of the graph's shape, so count them back in.
        indegrees = Counter(outputs)
        indegree_counts = Counter(indegrees.values())
        indegree_counts[0] = domain_size - len(indegrees)
        return MapAnalysis(
            domain_size=domain_size,
            attractors=attractors,
            attractor_count=len(attractors),
            dominant_attractor=dominant,
            dominant_basin_fraction=dominant.basin_size / domain_size,
            dominant_cycle_length=dominant.cycle_length,
            mean_depth=sum(depth) / domain_size,
            max_depth=max_depth,
            image_size=image_size,
            image_ratio=image_size / domain_size,
            fixed_point_count=sum(1 for value, image in enumerate(outputs) if value == image),
            depth_histogram=tuple(sorted(Counter(depth).items())),
            indegree_histogram=tuple(sorted(indegree_counts.items())),
        )

    def _reject_if_too_long(self, steps: int, seed: int) -> None:
        if steps > self._settings.max_iterations:
            raise MapRejectedError(
                AnalysisFailure(
                    reason=FailureReason.ITERATION_LIMIT,
                    detail=(
                        f"{seed:04d} had not settled after {self._settings.max_iterations} "
                        "iterations; a map that slow is not interesting"
                    ),
                )
            )
