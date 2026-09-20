from collections.abc import Iterator
from itertools import product

#: Permutations of a number's digits, written as the expression that produces them.
#: Every one is a bijection on the four-digit strings, so composing with them is exactly
#: the "relabelling" the novelty fingerprint is built to see through.
PRIMITIVES: dict[str, str] = {
    "asc": 'int("".join(sorted(d)))',
    "desc": 'int("".join(sorted(d, reverse=True)))',
    "rev": "int(d[::-1])",
    "rot": "int(d[1:] + d[0])",
    "ror": "int(d[-1] + d[:-1])",
    "swp": "int(d[1] + d[0] + d[3] + d[2])",
}

COEFFICIENTS: tuple[int, ...] = (-2, -1, 1, 2)

#: 0 and 1 are the plain cases; the others are the constants this corner of number
#: theory keeps producing - Kaprekar's own, its three-digit cousin, and 1089.
OFFSETS: tuple[int, ...] = (0, 1, 495, 1089, 6174)


class FormulaCataloguer:
    """Enumerates ``(a*P(v) + b*Q(v) + c) % 10000`` over digit permutations.

    This is the family a for-loop can exhaust in minutes. Cataloguing it is what stops
    the LLM spending its budget rediscovering members of it - which is exactly what
    every run on record did.
    """

    def candidates(self) -> Iterator[tuple[str, str]]:
        for (left, right), (a, b), c in product(
            product(PRIMITIVES, repeat=2), product(COEFFICIENTS, repeat=2), OFFSETS
        ):
            if left == right:
                continue
            offset = f" + {c}" if c else ""
            formula = f"({a}*{left} {b:+d}*{right}{offset}) % 10000"
            yield formula, self._source(left, right, a, b, c)

    @staticmethod
    def _source(left: str, right: str, a: int, b: int, c: int) -> str:
        offset = f" + {c}" if c else ""
        return (
            "def transform(value):\n"
            '    d = f"{value:04d}"\n'
            f"    return ({a}*{PRIMITIVES[left]} {b:+d}*{PRIMITIVES[right]}{offset}) % 10000\n"
        )
