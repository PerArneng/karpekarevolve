import json
from pathlib import Path

from kaprekarevolve.interfaces.catalogue import CatalogueEntry, Cataloguer, CatalogueSettings
from kaprekarevolve.interfaces.console import Console
from kaprekarevolve.interfaces.evolution import EvolutionRunner, EvolutionSettings
from kaprekarevolve.interfaces.file_system import FileSystem
from kaprekarevolve.interfaces.kaprekar import (
    AnalysisFailure,
    AnalysisOutcome,
    BaselineProgram,
    FailureReason,
    MapAnalyzer,
    MapRejectedError,
)
from kaprekarevolve.interfaces.log import Logger
from kaprekarevolve.interfaces.novelty import Fingerprinter
from kaprekarevolve.interfaces.program import DigitMap, ProgramLoader, ProgramLoadError
from kaprekarevolve.interfaces.report import ReportFormatter
from kaprekarevolve.interfaces.scoring import (
    EvaluationProjector,
    EvaluationReport,
    ScoreCard,
    ScoringPolicy,
)
from kaprekarevolve.interfaces.shape import CodeShape, ShapeAnalyzer

#: Cascade stage 1 only proves the candidate obeys the contract; the real score comes
#: from stage 2. It must sit above `cascade_thresholds[0]` in every config so stage 2
#: runs, and below any score a real map can earn - because OpenEvolve keeps stage 1's
#: metrics when stage 2 times out, and a hung candidate must never outrank a map that
#: actually converged. Under the six-factor product real maps score from ~1e-4 upward,
#: so this is deliberately tiny rather than the 1.0 it used to be.
_SCREEN_PASS_SCORE = 0.0001


class DefaultEngine:
    """Every use case of the application hangs off this class."""

    def __init__(
        self,
        file_system: FileSystem,
        program_loader: ProgramLoader,
        baseline_map: DigitMap,
        baseline_program: BaselineProgram,
        analyzer: MapAnalyzer,
        scoring_policy: ScoringPolicy,
        shape_analyzer: ShapeAnalyzer,
        fingerprinter: Fingerprinter,
        cataloguer: Cataloguer,
        catalogue_settings: CatalogueSettings,
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
        self._baseline_program = baseline_program
        self._analyzer = analyzer
        self._scoring_policy = scoring_policy
        self._shape_analyzer = shape_analyzer
        self._fingerprinter = fingerprinter
        self._cataloguer = cataloguer
        self._catalogue_settings = catalogue_settings
        self._evaluation_projector = evaluation_projector
        self._report_formatter = report_formatter
        self._evolution_runner = evolution_runner
        self._evolution_settings = evolution_settings
        self._console = console
        self._logger = logger

    def score_source(self, source: str) -> ScoreCard:
        shape = self._measure(source)
        try:
            digit_map = self._program_loader.load(source)
        except ProgramLoadError as error:
            return self._scoring_policy.score(
                AnalysisOutcome(
                    failure=AnalysisFailure(
                        reason=FailureReason.LOAD_ERROR, detail=str(error)
                    )
                ),
                shape,
            )
        return self._score_map(digit_map, shape)

    def _measure(self, source: str) -> CodeShape | None:
        """Measure the candidate's source, or None if it will not even parse."""
        try:
            return self._shape_analyzer.analyze(source)
        except (SyntaxError, ValueError):
            return None

    def score_path(self, path: Path) -> ScoreCard:
        return self.score_source(self._file_system.read_text(path))

    def evaluate_path(self, path: Path) -> EvaluationReport:
        return self._evaluation_projector.project(self.score_path(path))

    def screen_path(self, path: Path) -> EvaluationReport:
        """Cheap first cascade stage: contract check on a sample, no scoring."""
        try:
            digit_map = self._program_loader.load(self._file_system.read_text(path))
        except ProgramLoadError as error:
            return self._evaluation_projector.project_screening(
                False,
                AnalysisFailure(reason=FailureReason.LOAD_ERROR, detail=str(error)),
                _SCREEN_PASS_SCORE,
            )
        failure = self._analyzer.validate(digit_map)
        return self._evaluation_projector.project_screening(
            failure is None, failure, _SCREEN_PASS_SCORE
        )

    def show_baseline(self) -> None:
        # Scored from source, by the same path a candidate file takes, so that the
        # yardstick and the thing measured against it cannot drift apart.
        card = self.score_source(self._baseline_program.source)
        self._console.write(
            self._report_formatter.format_score_card(self._baseline_program.title, card)
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

    def show_catalogue(self) -> None:
        """Enumerate the short-formula family and write down what it already reaches."""
        settings = self._catalogue_settings
        best: dict[object, CatalogueEntry] = {}
        examined = 0
        for formula, source in self._cataloguer.candidates():
            examined += 1
            card = self.score_source(source)
            analysis = card.analysis
            if analysis is None or card.shape is None:
                continue
            if analysis.dominant_basin_fraction < settings.min_basin_fraction:
                continue
            if analysis.dominant_cycle_length > settings.max_cycle_length:
                continue
            fingerprint = self._fingerprinter.fingerprint(analysis)
            entry = CatalogueEntry(
                formula=formula,
                fingerprint=fingerprint,
                cost=card.shape.cost,
                attractor=analysis.dominant_attractor.members,
                basin_fraction=analysis.dominant_basin_fraction,
                attractor_count=analysis.attractor_count,
                mean_depth=analysis.mean_depth,
                max_depth=analysis.max_depth,
            )
            # Keep the cheapest route to each structure: that is the bar a candidate
            # has to beat to count as having found a shorter way to a known place.
            known = best.get(fingerprint.structure)
            if known is None or entry.cost < known.cost:
                best[fingerprint.structure] = entry
        entries = sorted(best.values(), key=lambda item: (-item.basin_fraction, item.cost))
        self._write_catalogue(entries)
        self._console.write(
            self._report_formatter.format_catalogue(examined, entries)
        )

    def _write_catalogue(self, entries: list[CatalogueEntry]) -> None:
        settings = self._catalogue_settings
        self._file_system.write_text(
            settings.registry_path,
            json.dumps(
                [
                    {"structure": [list(pair) for pair in entry.fingerprint.structure],
                     "cost": entry.cost,
                     "formula": entry.formula}
                    for entry in entries
                ],
                indent=2,
            ),
        )
        self._file_system.write_text(
            settings.report_path, self._report_formatter.format_catalogue(len(entries), entries)
        )

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

    def _score_map(self, digit_map: DigitMap, shape: CodeShape | None = None) -> ScoreCard:
        return self._scoring_policy.score(self._analyzer.analyze(digit_map), shape)
