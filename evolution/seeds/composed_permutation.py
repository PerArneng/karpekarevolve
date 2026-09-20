"""Seed: a composed permutation, deliberately outside the catalogued family.

`uv run kaprekarevolve catalogue` exhausts `(a*P(v) + b*Q(v) + c) % 10000` for digit
permutations P and Q - 2400 formulas reaching only 7 distinct structures, all recorded.
This map is not in that family: it *composes* the permutations rather than adding them,
applying a rotation to the ascending digits before subtracting. That one change is
enough to reach a structure the sweep never sees, and it settles on 4950.

It starts where the search should be looking: novelty 1.0, and short enough that the
elegance term is still working in its favour.
"""

# EVOLVE-BLOCK-START


def transform(value: int) -> int:
    """Descending digits minus a rotation of the ascending digits."""
    digits = f"{value:04d}"
    ascending = "".join(sorted(digits))
    descending = int("".join(sorted(digits, reverse=True)))
    return (descending - int(ascending[1:] + ascending[0])) % 10000


# EVOLVE-BLOCK-END


if __name__ == "__main__":
    current = 3524
    for _ in range(8):
        print(f"{current:04d}")
        current = transform(current)
