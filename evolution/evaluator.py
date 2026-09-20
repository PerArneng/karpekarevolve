"""OpenEvolve adapter.

A frontend, exactly like the CLI: it parses a path and calls the facade. All the
scoring lives in ``kaprekarevolve``, so ``kaprekarevolve score <file>`` and the
evolution loop cannot drift apart.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from openevolve.evaluation_result import EvaluationResult  # noqa: E402

from kaprekarevolve.container import Container  # noqa: E402
from kaprekarevolve.interfaces.engine import Engine  # noqa: E402
from kaprekarevolve.interfaces.scoring import EvaluationReport  # noqa: E402


def _engine() -> Engine:
    container = Container()
    container.config.use_color.from_value(False)
    engine: Engine = container.engine()
    return engine


def _as_result(report: EvaluationReport) -> Any:
    return EvaluationResult(metrics=dict(report.metrics), artifacts=dict(report.artifacts))


def evaluate_stage1(program_path: str) -> Any:
    """Cheap contract check on a sample of the domain."""
    return _as_result(_engine().screen_path(Path(program_path)))


def evaluate_stage2(program_path: str) -> Any:
    """Exact analysis of all 10,000 starting numbers."""
    return _as_result(_engine().evaluate_path(Path(program_path)))


def evaluate(program_path: str) -> Any:
    """Full evaluation, used when cascade evaluation is turned off."""
    return _as_result(_engine().evaluate_path(Path(program_path)))


if __name__ == "__main__":
    result = _engine().evaluate_path(Path(sys.argv[1]))
    for name, value in sorted(result.metrics.items()):
        print(f"{name:<24} {value:.6f}")
    for name, detail in sorted(result.artifacts.items()):
        print(f"{name:<24} {detail}")
