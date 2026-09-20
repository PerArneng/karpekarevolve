from dependency_injector import containers, providers

from kaprekarevolve.interfaces.evolution import EvolutionSettings
from kaprekarevolve.interfaces.kaprekar import AnalysisSettings
from kaprekarevolve.interfaces.scoring import ScoreWeights
from kaprekarevolve.modules.clock import SystemClock
from kaprekarevolve.modules.console import StdioConsole
from kaprekarevolve.modules.engine import DefaultEngine
from kaprekarevolve.modules.evolution import OpenEvolveRunner
from kaprekarevolve.modules.file_system import LocalFileSystem
from kaprekarevolve.modules.kaprekar import BuiltinKaprekarMap, MemoizedMapAnalyzer
from kaprekarevolve.modules.log import AnsiLogFormatter, DefaultLogger
from kaprekarevolve.modules.program import ExecProgramLoader
from kaprekarevolve.modules.report import TextReportFormatter
from kaprekarevolve.modules.scoring import (
    DefaultEvaluationProjector,
    WeightedScoringPolicy,
)


class Container(containers.DeclarativeContainer):
    """The composition root. Only a frontend entry point may instantiate this."""

    config = providers.Configuration()

    analysis_settings = providers.Singleton(AnalysisSettings)
    score_weights = providers.Singleton(ScoreWeights)
    evolution_settings = providers.Singleton(EvolutionSettings)

    clock = providers.Singleton(SystemClock)
    console = providers.Singleton(StdioConsole)
    file_system = providers.Singleton(LocalFileSystem)
    log_formatter = providers.Singleton(AnsiLogFormatter, use_color=config.use_color)
    logger = providers.Singleton(
        DefaultLogger, clock=clock, formatter=log_formatter, console=console
    )

    program_loader = providers.Singleton(ExecProgramLoader)
    baseline_map = providers.Singleton(BuiltinKaprekarMap)
    analyzer = providers.Singleton(
        MemoizedMapAnalyzer, clock=clock, settings=analysis_settings
    )
    scoring_policy = providers.Singleton(WeightedScoringPolicy, weights=score_weights)
    evaluation_projector = providers.Singleton(DefaultEvaluationProjector)
    report_formatter = providers.Singleton(TextReportFormatter)
    evolution_runner = providers.Singleton(OpenEvolveRunner)

    engine = providers.Singleton(
        DefaultEngine,
        file_system=file_system,
        program_loader=program_loader,
        baseline_map=baseline_map,
        analyzer=analyzer,
        scoring_policy=scoring_policy,
        evaluation_projector=evaluation_projector,
        report_formatter=report_formatter,
        evolution_runner=evolution_runner,
        evolution_settings=evolution_settings,
        console=console,
        logger=logger,
    )
