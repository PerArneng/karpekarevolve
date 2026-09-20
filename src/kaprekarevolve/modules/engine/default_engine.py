import json
from pathlib import Path

from kaprekarevolve.interfaces.console import Console
from kaprekarevolve.interfaces.evolution import EvolutionRunner, EvolutionSettings
from kaprekarevolve.interfaces.file_system import FileSystem
from kaprekarevolve.interfaces.kaprekar import (
    AnalysisFailure,
    AnalysisOutcome,
    FailureReason,
    MapAnalyzer,
    MapRejectedError,
)
from kaprekarevolve.interfaces.log import Logger
from kaprekarevolve.interfaces.program import DigitMap, ProgramLoader, ProgramLoadError
from kaprekarevolve.interfaces.report import ReportFormatter
from kaprekarevolve.interfaces.scoring import (
    EvaluationProjector,
    EvaluationReport,
    ScoreCard,
    ScoringPolicy,
)


class DefaultEngine:
    """Every use case of the application hangs off this class."""

    def __init__(
        self,
        file_system: FileSystem,
        program_loader: ProgramLoader,
        baseline_map: DigitMap,
        analyzer: MapAnalyzer,
        scoring_policy: ScoringPolicy,
        evaluation_projector: EvaluationProjector,
        report_formatter: ReportFormatter,
        evolution_runner: EvolutionRunner,
        evolution_settings: EvolutionSettings,
        console: Console,
        logger: Logger,
    ) -> None:
        self._file_system = file_system
        self._program_loader = program_loader
        self._baseline_map = baseline_map
        self._analyzer = analyzer
        self._scoring_policy = scoring_policy
        self._evaluation_projector = evaluation_projector
        self._report_formatter = report_formatter
        self._evolution_runner = evolution_runner
        self._evolution_settings = evolution_settings
        self._console = console
        self._logger = logger

    def score_source(self, source: str) -> ScoreCard:
        try:
            digit_map = self._program_loader.load(source)
        except ProgramLoadError as error:
            return self._scoring_policy.score(
                AnalysisOutcome(
                    failure=AnalysisFailure(
                        reason=FailureReason.LOAD_ERROR, detail=str(error)
                    )
                )
            )
        return self._score_map(digit_map)

    def score_path(self, path: Path) -> ScoreCard:
        return self.score_source(self._file_system.read_text(path))

    def evaluate_path(self, path: Path) -> EvaluationReport:
        return self._evaluation_projector.project(self.score_path(path))

    def screen_path(self, path: Path) -> EvaluationReport:
        """Cheap first cascade stage: contract check on a sample, no scoring."""
        try:
            digit_map = self._program_loader.load(self._file_system.read_text(path))
        except ProgramLoadError as error:
            return EvaluationReport(
                metrics={"combined_score": 0.0, "validity": 0.0},
                artifacts={"failure_reason": FailureReason.LOAD_ERROR.value, "stderr": str(error)},
            )
        failure = self._analyzer.validate(digit_map)
        if failure is not None:
            return EvaluationReport(
                metrics={"combined_score": 0.0, "validity": 0.0},
                artifacts={"failure_reason": failure.reason.value, "stderr": failure.detail},
            )
        return EvaluationReport(metrics={"combined_score": 1.0, "validity": 1.0})

    def show_baseline(self) -> None:
        card = self._score_map(self._baseline_map)
        self._console.write(
            self._report_formatter.format_score_card("Kaprekar routine (baseline)", card)
        )

    def show_score(self, path: Path) -> None:
        card = self.score_path(path)
        self._console.write(self._report_formatter.format_score_card(str(path), card))

    def show_trace(self, seed: int, path: Path | None) -> None:
        digit_map = self._baseline_map
        if path is not None:
            try:
                digit_map = self._program_loader.load(self._file_system.read_text(path))
            except ProgramLoadError as error:
                self._logger.error(str(error))
                return
        try:
            trajectory = self._analyzer.trace(digit_map, seed)
        except MapRejectedError as rejected:
            self._logger.error(rejected.failure.detail)
            return
        self._console.write(self._report_formatter.format_trajectory(trajectory))

    def show_best(self) -> None:
        best_dir = self._evolution_settings.output_dir / "best"
        program_path = best_dir / "best_program.py"
        if not self._file_system.exists(program_path):
            self._logger.error(f"no evolved program at {program_path}; run evolve first")
            return
        source = self._file_system.read_text(program_path)
        card = self.score_source(source)
        self._console.write(self._report_formatter.format_score_card(str(program_path), card))
        info_path = best_dir / "best_program_info.json"
        if self._file_system.exists(info_path):
            info = json.loads(self._file_system.read_text(info_path))
            self._console.write(f"\ngeneration              {info.get('generation', '?')}")
            self._console.write(f"iteration               {info.get('iteration_found', '?')}")
        self._console.write("\n" + source)

    def evolve(
        self,
        iterations: int | None,
        backend: str | None = None,
        seed: str | None = None,
    ) -> None:
        settings = self._evolution_settings
        if iterations is not None:
            settings = settings.model_copy(update={"iterations": iterations})
        if backend is not None:
            settings = settings.model_copy(
                update={"config_path": self._backend_config_path(backend)}
            )
        if seed is not None:
            settings = settings.model_copy(
                update={"initial_program_path": self._seed_program_path(seed)}
            )
        self._logger.info(
            f"evolving for {settings.iterations} iterations "
            f"from {settings.initial_program_path} "
            f"using {settings.config_path}"
        )
        result = self._evolution_runner.run(settings)
        self._console.write(self._report_formatter.format_evolution_result(result))

    @staticmethod
    def _backend_config_path(backend: str) -> Path:
        """Map a backend name onto its OpenEvolve config file."""
        return Path("evolution") / f"config.{backend}.yaml"

    @staticmethod
    def _seed_program_path(seed: str) -> Path:
        """Map a seed name onto its starting program."""
        return Path("evolution") / "seeds" / f"{seed}.py"

    def _score_map(self, digit_map: DigitMap) -> ScoreCard:
        return self._scoring_policy.score(self._analyzer.analyze(digit_map))
