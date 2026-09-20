import os
import sys
from pathlib import Path
from typing import Annotated

import typer

from kaprekarevolve.container import Container
from kaprekarevolve.interfaces.engine import Engine

app = typer.Typer(no_args_is_help=True, add_completion=False, help=__doc__)


def _engine() -> Engine:
    """Build the composition root. The only place a Container is created."""
    container = Container()
    container.config.use_color.from_value(
        sys.stdout.isatty() and os.environ.get("NO_COLOR") is None
    )
    engine: Engine = container.engine()
    return engine


@app.callback()
def cli() -> None:
    """Evolve Kaprekar-like maps on the four-digit numbers."""


@app.command()
def baseline() -> None:
    """Analyse and score the built-in Kaprekar routine."""
    _engine().show_baseline()


@app.command()
def score(
    program: Annotated[Path, typer.Argument(help="Python file defining transform(n)")],
) -> None:
    """Score a candidate program."""
    _engine().show_score(program)


@app.command()
def trace(
    seed: Annotated[int, typer.Argument(help="starting number, 0..9999")],
    program: Annotated[
        Path | None, typer.Option("--program", "-p", help="candidate to trace with")
    ] = None,
) -> None:
    """Walk one number to its attractor."""
    _engine().show_trace(seed, program)


@app.command()
def evolve(
    iterations: Annotated[
        int | None, typer.Option("--iterations", "-n", help="override the config")
    ] = None,
) -> None:
    """Run OpenEvolve to search for new maps."""
    _engine().evolve(iterations)


@app.command()
def best() -> None:
    """Show the best program from the last evolution run."""
    _engine().show_best()


def main() -> None:
    """Console script entry point."""
    app()
