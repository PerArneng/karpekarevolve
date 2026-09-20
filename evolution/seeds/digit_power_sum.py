"""Seed: sum of the cubes of the digits.

A different family from Kaprekar's routine: it discards digit *order* entirely
and works on the multiset of digits through a power sum. Known to settle on
several fixed points (153, 370, 371, 407) and short cycles, so it starts with
poor parsimony - the search has to earn a single attractor some other way.

Stays in range without clamping: 4 * 9**3 = 2916.
"""

# EVOLVE-BLOCK-START


def transform(value: int) -> int:
    """Sum the cubes of the four digits."""
    return sum(int(digit) ** 3 for digit in f"{value:04d}")


# EVOLVE-BLOCK-END


if __name__ == "__main__":
    current = 3524
    for _ in range(8):
        print(f"{current:04d}")
        current = transform(current)
