from datetime import datetime
from pathlib import Path

import pytest

from kaprekarevolve.interfaces.catalogue import CatalogueSettings
from kaprekarevolve.interfaces.evolution import EvolutionResult, EvolutionSettings
from kaprekarevolve.interfaces.kaprekar import AnalysisSettings, BaselineProgram
from kaprekarevolve.interfaces.novelty import NoveltyRegistry
from kaprekarevolve.interfaces.scoring import ScoreWeights
from kaprekarevolve.modules.catalogue import FormulaCataloguer
from kaprekarevolve.modules.engine import DefaultEngine
from kaprekarevolve.modules.kaprekar import BuiltinKaprekarMap, MemoizedMapAnalyzer
from kaprekarevolve.modules.log import AnsiLogFormatter, DefaultLogger
from kaprekarevolve.modules.novelty import AnalysisFingerprinter
from kaprekarevolve.modules.program import ExecProgramLoader
from kaprekarevolve.modules.report import TextReportFormatter
from kaprekarevolve.modules.scoring import DefaultEvaluationProjector, WeightedScoringPolicy
from kaprekarevolve.modules.shape import AstShapeAnalyzer
from tests.fakes import (
    FrozenClock,
    InMemoryConsole,
    InMemoryFileSystem,
    RecordingEvolutionRunner,
)

CANDIDATE = Path("candidate.py")
#: The same text the baseline is scored from, so the two paths are comparable at all.
KAPREKAR_SOURCE = BaselineProgram().source


class Harness:
    """The whole application, wired to fakes."""

    def __init__(
        self,
        files: dict[Path, str] | None = None,
        registry: NoveltyRegistry | None = None,
    ) -> None:
        clock = FrozenClock(datetime(2026, 9, 20, 12, 0, 0))
        fingerprinter = AnalysisFingerprinter()
        self.console = InMemoryConsole()
        self.file_system = InMemoryFileSystem(files)
        self.runner = RecordingEvolutionRunner(
            EvolutionResult(
                best_score=0.9, best_code="def transform(v): return 0", metrics={"x": 1.0}
            )
        )
        self.engine = DefaultEngine(
            file_system=self.file_system,
            program_loader=ExecProgramLoader(),
            baseline_map=BuiltinKaprekarMap(),
            baseline_program=BaselineProgram(),
            analyzer=MemoizedMapAnalyzer(clock=clock, settings=AnalysisSettings()),
            scoring_policy=WeightedScoringPolicy(
                weights=ScoreWeights(),
                # Empty by default: these tests measure shape, not prior art.
                registry=registry or NoveltyRegistry(),
                fingerprinter=fingerprinter,
            ),
            shape_analyzer=AstShapeAnalyzer(),
            fingerprinter=fingerprinter,
            cataloguer=FormulaCataloguer(),
            catalogue_settings=CatalogueSettings(),
            evaluation_projector=DefaultEvaluationProjector(),
            report_formatter=TextReportFormatter(),
            evolution_runner=self.runner,
            evolution_settings=EvolutionSettings(iterations=7),
            console=self.console,
            logger=DefaultLogger(
                clock=clock,
                formatter=AnsiLogFormatter(use_color=False),
                console=self.console,
            ),
        )


def test_scoring_a_candidate_file_matches_the_baseline() -> None:
    """The yardstick must be measured exactly like the things measured against it.

    Now that the score reads the source as well as the convergence, a baseline scored
    some other way would drift from `kaprekarevolve score` - the one divergence the
    architecture exists to prevent.
    """
    harness = Harness({CANDIDATE: KAPREKAR_SOURCE})

    card = harness.engine.score_path(CANDIDATE)
    harness.engine.show_baseline()

    assert card.combined_score == pytest.approx(0.394438, abs=1e-6)
    assert f"{card.combined_score:.6f}" in harness.console.text


def test_the_cascade_stages_agree_on_a_sound_candidate() -> None:
    harness = Harness({CANDIDATE: KAPREKAR_SOURCE})

    screen = harness.engine.screen_path(CANDIDATE)
    full = harness.engine.evaluate_path(CANDIDATE)

    assert screen.metrics["validity"] == 1.0
    assert full.metrics["validity"] == 1.0
    assert full.metrics["attractor_count"] == 2.0
    assert full.artifacts == {}


def test_a_broken_candidate_is_rejected_by_the_cheap_stage_with_an_artifact() -> None:
    harness = Harness({CANDIDATE: "def transform(value):\n    return value + 99999\n"})

    screen = harness.engine.screen_path(CANDIDATE)

    assert screen.metrics["combined_score"] == 0.0
    assert screen.artifacts["failure_reason"] == "out_of_range"


def test_source_without_a_transform_scores_zero() -> None:
    harness = Harness({CANDIDATE: "x = 1\n"})

    card = harness.engine.score_path(CANDIDATE)

    assert not card.valid
    assert card.failure is not None
    assert card.failure.reason.value == "load_error"


def test_show_baseline_reports_6174() -> None:
    harness = Harness()

    harness.engine.show_baseline()

    assert "6174" in harness.console.text
    assert "0.394438" in harness.console.text


def test_show_trace_walks_the_baseline() -> None:
    harness = Harness()

    harness.engine.show_trace(9831, None)

    assert harness.console.text.startswith("9831: 9831 -> 8442")
    assert "reached after 7 step(s)" in harness.console.text


def test_show_trace_reports_a_broken_candidate_without_crashing() -> None:
    harness = Harness({CANDIDATE: "def transform(value):\n    return -1\n"})

    harness.engine.show_trace(1234, CANDIDATE)

    assert harness.console.output == []
    assert "outside 0..9999" in harness.console.errors[0]


def test_evolve_passes_the_iteration_override_through() -> None:
    harness = Harness()

    harness.engine.evolve(25)

    assert harness.runner.calls[0].iterations == 25
    assert "best combined_score     0.900000" in harness.console.text


def test_evolve_defaults_to_the_brain_tailscale_backend() -> None:
    harness = Harness()

    harness.engine.evolve(None)

    assert harness.runner.calls[0].config_path == Path(
        "evolution/config.brain-tailscale.yaml"
    )


def test_evolve_selects_the_named_backend_config() -> None:
    harness = Harness()

    harness.engine.evolve(None, "cerebras")

    assert harness.runner.calls[0].config_path == Path("evolution/config.cerebras.yaml")


def test_evolve_backend_and_iterations_compose() -> None:
    harness = Harness()

    harness.engine.evolve(7, "cerebras")

    call = harness.runner.calls[0]
    assert call.iterations == 7
    assert call.config_path == Path("evolution/config.cerebras.yaml")


def test_evolve_defaults_to_the_kaprekar_seed() -> None:
    harness = Harness()

    harness.engine.evolve(None)

    assert harness.runner.calls[0].initial_program_path == Path(
        "evolution/seeds/kaprekar.py"
    )


def test_evolve_selects_the_named_seed() -> None:
    harness = Harness()

    harness.engine.evolve(None, None, "reverse_add")

    assert harness.runner.calls[0].initial_program_path == Path(
        "evolution/seeds/reverse_add.py"
    )


def test_evolve_seed_and_backend_are_independent() -> None:
    harness = Harness()

    harness.engine.evolve(5, "cerebras", "digit_power_sum")

    call = harness.runner.calls[0]
    assert call.iterations == 5
    assert call.config_path == Path("evolution/config.cerebras.yaml")
    assert call.initial_program_path == Path("evolution/seeds/digit_power_sum.py")


def test_evolve_without_an_override_keeps_the_configured_iterations() -> None:
    harness = Harness()

    harness.engine.evolve(None)

    assert harness.runner.calls[0].iterations == 7


def test_show_best_complains_when_nothing_has_been_evolved() -> None:
    harness = Harness()

    harness.engine.show_best()

    assert "run evolve first" in harness.console.errors[0]
