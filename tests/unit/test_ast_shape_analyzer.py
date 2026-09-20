import pytest

from kaprekarevolve.modules.shape import AstShapeAnalyzer

ANALYZER = AstShapeAnalyzer()

DEF = "def transform(value: int) -> int:\n    return (value // 100) * (value % 100) % 10000\n"
LAMBDA = "transform = lambda v: (v // 100) * (v % 100) % 10_000"


def test_a_lambda_binding_costs_the_same_as_the_equivalent_def() -> None:
    """The exploit that a 200-iteration run actually found.

    Looking only for a FunctionDef meant `transform = lambda ...` raised, and the raise
    was caught upstream as "this map has no source" - the neutral meant for the built-in
    baseline. That handed the candidate elegance 1.0, a perfect score on the one factor
    it was dodging. 30 of 201 programs in that run found it.
    """
    assert ANALYZER.analyze(LAMBDA).cost == ANALYZER.analyze(DEF).cost


def test_source_with_no_recognisable_transform_is_charged_not_excused() -> None:
    shape = ANALYZER.analyze("x = 1\ny = [1, 2, 3, 4, 5]\n")

    assert shape.cost > 0


def test_the_docstring_is_not_counted() -> None:
    documented = (
        'def transform(v):\n'
        '    """A very long explanation that should not count."""\n'
        "    return v % 10\n"
    )
    bare = "def transform(v):\n    return v % 10\n"

    assert ANALYZER.analyze(documented).cost == ANALYZER.analyze(bare).cost


def test_branches_and_magic_constants_and_tables_all_cost_extra() -> None:
    plain = ANALYZER.analyze("def transform(v):\n    return v % 10\n")
    branchy = ANALYZER.analyze("def transform(v):\n    return v % 10 if v else 0\n")
    magic = ANALYZER.analyze("def transform(v):\n    return (v + 6174) % 10\n")
    table = ANALYZER.analyze("def transform(v):\n    return [1, 2, 3, 4, 10, 0][v % 3]\n")

    assert branchy.cost > plain.cost
    assert magic.magic_constant_count == 1 and magic.cost > plain.cost
    assert table.table_element_count == 6 and table.cost > plain.cost


def test_a_numeric_string_is_a_magic_constant_in_disguise() -> None:
    assert ANALYZER.analyze('def transform(v):\n    return int("6174")\n').magic_constant_count == 1


def test_format_specifiers_and_join_separators_are_free() -> None:
    source = 'def transform(v):\n    return int("".join(sorted(f"{v:04d}")))\n'

    assert ANALYZER.analyze(source).magic_constant_count == 0


@pytest.mark.parametrize("source", [DEF, LAMBDA, "x = 1\n"])
def test_analysis_never_raises(source: str) -> None:
    """A raise here became a perfect score upstream, so this must be total."""
    assert ANALYZER.analyze(source).cost >= 0
