from pathlib import Path

from dependency_injector import containers, providers

from kaprekarevolve.interfaces.catalogue import CatalogueSettings
from kaprekarevolve.interfaces.evolution import EvolutionSettings
from kaprekarevolve.interfaces.kaprekar import AnalysisSettings, BaselineProgram
from kaprekarevolve.interfaces.scoring import ScoreWeights
from kaprekarevolve.modules.catalogue import FormulaCataloguer
from kaprekarevolve.modules.clock import SystemClock
from kaprekarevolve.modules.console import StdioConsole
from kaprekarevolve.modules.engine import DefaultEngine
from kaprekarevolve.modules.evolution import OpenEvolveRunner
from kaprekarevolve.modules.file_system import LocalFileSystem
from kaprekarevolve.modules.kaprekar import BuiltinKaprekarMap, MemoizedMapAnalyzer
from kaprekarevolve.modules.log import AnsiLogFormatter, DefaultLogger
from kaprekarevolve.modules.novelty import AnalysisFingerprinter, JsonRegistryLoader
from kaprekarevolve.modules.program import ExecProgramLoader
from kaprekarevolve.modules.report import TextReportFormatter
from kaprekarevolve.modules.scoring import (
    DefaultEvaluationProjector,
    WeightedScoringPolicy,
)
from kaprekarevolve.modules.shape import AstShapeAnalyzer

#: Where `kaprekarevolve catalogue` records the maps already known, so that the scorer
#: can tell a discovery from one of them wearing a different set of values.
REGISTRY_PATH = Path("found-solutions/registry.json")


class Container(containers.DeclarativeContainer):
    """The composition root. Only a frontend entry point may instantiate this."""

    config = providers.Configuration()

    analysis_settings = providers.Singleton(AnalysisSettings)
    score_weights = providers.Singleton(ScoreWeights)
    evolution_settings = providers.Singleton(EvolutionSettings)
    catalogue_settings = providers.Singleton(CatalogueSettings)

    clock = providers.Singleton(SystemClock)
    console = providers.Singleton(StdioConsole)
    file_system = providers.Singleton(LocalFileSystem)
    log_formatter = providers.Singleton(AnsiLogFormatter, use_color=config.use_color)
    logger = providers.Singleton(
        DefaultLogger, clock=clock, formatter=log_formatter, console=console
    )

    program_loader = providers.Singleton(ExecProgramLoader)
    baseline_map = providers.Singleton(BuiltinKaprekarMap)
    baseline_program = providers.Singleton(BaselineProgram)
    analyzer = providers.Singleton(
        MemoizedMapAnalyzer, clock=clock, settings=analysis_settings
    )
    shape_analyzer = providers.Singleton(AstShapeAnalyzer)
    cataloguer = providers.Singleton(FormulaCataloguer)
    fingerprinter = providers.Singleton(AnalysisFingerprinter)
    registry_loader = providers.Singleton(JsonRegistryLoader, file_system=file_system)
    novelty_registry = providers.Singleton(
        lambda loader, path: loader.load(path),
        loader=registry_loader,
        path=REGISTRY_PATH,
    )
    scoring_policy = providers.Singleton(
        WeightedScoringPolicy,
        weights=score_weights,
        registry=novelty_registry,
        fingerprinter=fingerprinter,
    )
    evaluation_projector = providers.Singleton(DefaultEvaluationProjector)
    report_formatter = providers.Singleton(TextReportFormatter)
    evolution_runner = providers.Singleton(OpenEvolveRunner)

    engine = providers.Singleton(
        DefaultEngine,
        file_system=file_system,
        program_loader=program_loader,
        baseline_map=baseline_map,
        baseline_program=baseline_program,
        analyzer=analyzer,
        scoring_policy=scoring_policy,
        shape_analyzer=shape_analyzer,
        fingerprinter=fingerprinter,
        cataloguer=cataloguer,
        catalogue_settings=catalogue_settings,
        evaluation_projector=evaluation_projector,
        report_formatter=report_formatter,
        evolution_runner=evolution_runner,
        evolution_settings=evolution_settings,
        console=console,
        logger=logger,
    )
