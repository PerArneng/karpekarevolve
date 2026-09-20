"""Seed program for evolution: the classic Kaprekar routine.

The contract, which the evaluator enforces:

* ``transform(value)`` takes an int in ``0..9999`` and returns an int in ``0..9999``.
* Think of the number as its zero-padded four-digit form: 49 is "0049".
* It must be pure and deterministic - no randomness, no globals, no IO.

The score rewards the *shape* of the convergence, not merely that it converges:
a single shallow-but-not-instant basin ending in a fixed point. Constant maps and
the identity score exactly zero.
"""

# EVOLVE-BLOCK-START


def transform(value: int) -> int:
    """Kaprekar's routine: descending digits minus ascending digits."""
    digits = f"{value:04d}"
    descending = int("".join(sorted(digits, reverse=True)))
    ascending = int("".join(sorted(digits)))
    return descending - ascending


# EVOLVE-BLOCK-END


if __name__ == "__main__":
    current = 3524
    for _ in range(8):
        print(f"{current:04d}")
        current = transform(current)
