from typing import Any

from openevolve import run_evolution

from kaprekarevolve.interfaces.evolution import EvolutionResult, EvolutionSettings


class OpenEvolveRunner:
    """Drives OpenEvolve's library API. An edge: it calls an LLM and writes files."""

    def run(self, settings: EvolutionSettings) -> EvolutionResult:
        result: Any = run_evolution(
            initial_program=settings.initial_program_path,
            evaluator=settings.evaluator_path,
            config=settings.config_path,
            iterations=settings.iterations,
            output_dir=str(settings.output_dir),
            cleanup=False,
        )
        metrics = {
            name: float(value)
            for name, value in dict(result.metrics).items()
            if isinstance(value, (int, float)) and not isinstance(value, bool)
        }
        return EvolutionResult(
            best_score=float(result.best_score),
            best_code=str(result.best_code),
            metrics=metrics,
            output_dir=result.output_dir,
        )
