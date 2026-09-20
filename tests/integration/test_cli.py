from typer.testing import CliRunner

from kaprekarevolve.cli.main import app

RUNNER = CliRunner()


def test_baseline_command_runs_end_to_end() -> None:
    result = RUNNER.invoke(app, ["baseline"])

    assert result.exit_code == 0
    assert "0.585457" in result.stdout


def test_trace_command_runs_end_to_end() -> None:
    result = RUNNER.invoke(app, ["trace", "9831"])

    assert result.exit_code == 0
    assert "6174" in result.stdout


def test_bare_invocation_lists_the_commands() -> None:
    result = RUNNER.invoke(app, [])

    # Typer exits 2 for a missing command; what matters is that it lists them.
    assert result.exit_code == 2
    for command in ("baseline", "score", "trace", "evolve", "best"):
        assert command in result.output
