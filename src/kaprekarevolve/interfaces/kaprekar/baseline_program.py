from pydantic import BaseModel, ConfigDict

#: The reference map, as source. `baseline` scores this through exactly the path a
#: candidate file takes, so that `kaprekarevolve baseline` and
#: `kaprekarevolve score evolution/seeds/kaprekar.py` cannot report different numbers -
#: which they would the moment the score started measuring code as well as convergence.
KAPREKAR_SOURCE = '''def transform(value: int) -> int:
    """Kaprekar's routine: descending digits minus ascending digits."""
    digits = f"{value:04d}"
    descending = int("".join(sorted(digits, reverse=True)))
    ascending = int("".join(sorted(digits)))
    return descending - ascending
'''


class BaselineProgram(BaseModel):
    """The map every candidate is measured against, carried as source."""

    model_config = ConfigDict(frozen=True)

    title: str = "Kaprekar routine (baseline)"
    source: str = KAPREKAR_SOURCE
