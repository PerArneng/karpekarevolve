import pytest

from kaprekarevolve.interfaces.program import ProgramLoadError
from kaprekarevolve.modules.program import ExecProgramLoader

LOADER = ExecProgramLoader()


def test_loads_the_transform_function() -> None:
    digit_map = LOADER.load("def transform(value):\n    return (value * 3) % 10000\n")

    assert digit_map(1111) == 3333


def test_source_without_a_transform_is_rejected() -> None:
    with pytest.raises(ProgramLoadError, match="no transform"):
        LOADER.load("def other(value):\n    return value\n")


def test_source_that_fails_to_import_is_rejected() -> None:
    with pytest.raises(ProgramLoadError, match="failed to import"):
        LOADER.load("def transform(value)\n    return value\n")


def test_a_non_callable_transform_is_rejected() -> None:
    with pytest.raises(ProgramLoadError, match="not callable"):
        LOADER.load("transform = 42\n")
